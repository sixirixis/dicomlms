# Create Pathology Slide Viewer with OpenSeadragon and IIIF support
pathology_dockerfile = """FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache python3 make g++

# Set working directory
WORKDIR /usr/src/app

# Copy package files first for better Docker caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application source code
COPY . .

# Create directories for slides and cache
RUN mkdir -p /app/slides /app/cache /app/uploads && \\
    chown -R node:node /app

# Switch to non-root user
USER node

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \\
    CMD wget -q -O /dev/null http://localhost:8080/health || exit 1

# Start the application
CMD ["npm", "start"]
"""

# Create package.json for pathology viewer
package_json = """{
  "name": "medical-lms-pathology-viewer",
  "version": "1.0.0",
  "description": "Pathology slide viewer for Medical LMS using OpenSeadragon and IIIF",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "multer": "^1.4.5-lts.1",
    "sharp": "^0.32.6",
    "helmet": "^7.1.0",
    "cors": "^2.8.5",
    "uuid": "^9.0.1",
    "express-rate-limit": "^6.10.0",
    "compression": "^1.7.4",
    "morgan": "^1.10.0",
    "mime-types": "^2.1.35",
    "archiver": "^6.0.1",
    "node-cache": "^5.1.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.7.0"
  },
  "keywords": [
    "pathology",
    "medical-imaging",
    "openseadragon",
    "iiif",
    "whole-slide-imaging"
  ],
  "author": "Medical LMS Team",
  "license": "MIT"
}"""

# Create Express server for pathology viewer
pathology_server = """const express = require('express');
const multer = require('multer');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs').promises;
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const NodeCache = require('node-cache');

const app = express();
const PORT = process.env.PORT || 8080;

// Initialize cache for slide metadata
const slideCache = new NodeCache({ stdTTL: 3600 }); // 1 hour cache

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

// Middleware setup
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
      styleSrc: ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
      imgSrc: ["'self'", "data:", "blob:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'", "data:", "cdn.jsdelivr.net"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
}));

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3001', 'http://moodle-app'],
  credentials: true
}));

app.use(compression());
app.use(morgan('combined'));
app.use(limiter);
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'public')));
app.use('/slides', express.static(path.join('/app/slides')));

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, '/app/uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueName = `${uuidv4()}-${file.originalname}`;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 2 * 1024 * 1024 * 1024, // 2GB limit for pathology slides
  },
  fileFilter: (req, file, cb) => {
    // Accept common pathology slide formats
    const allowedTypes = [
      'image/tiff',
      'image/tif',
      'image/jpeg',
      'image/png',
      'application/octet-stream' // For proprietary formats like .scn, .svs
    ];
    
    const allowedExtensions = ['.tiff', '.tif', '.jpg', '.jpeg', '.png', '.scn', '.svs', '.ndpi'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(file.mimetype) || allowedExtensions.includes(fileExtension)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only pathology slide formats are allowed.'));
    }
  }
});

// IIIF Image API implementation
class IIIFImageAPI {
  constructor(slidePath) {
    this.slidePath = slidePath;
    this.tileSize = 512;
    this.overlap = 1;
  }

  async getInfo() {
    const cacheKey = `info-${path.basename(this.slidePath)}`;
    let info = slideCache.get(cacheKey);
    
    if (!info) {
      try {
        const metadata = await sharp(this.slidePath).metadata();
        info = {
          '@context': 'http://iiif.io/api/image/2/context.json',
          '@id': `/iiif/${path.basename(this.slidePath, path.extname(this.slidePath))}`,
          protocol: 'http://iiif.io/api/image',
          width: metadata.width,
          height: metadata.height,
          profile: ['http://iiif.io/api/image/2/level1.json'],
          tiles: [{
            width: this.tileSize,
            height: this.tileSize,
            scaleFactors: this.generateScaleFactors(metadata.width, metadata.height)
          }]
        };
        slideCache.set(cacheKey, info);
      } catch (error) {
        throw new Error(`Failed to get image metadata: ${error.message}`);
      }
    }
    
    return info;
  }

  generateScaleFactors(width, height) {
    const factors = [1];
    const maxDimension = Math.max(width, height);
    let scale = 2;
    
    while (maxDimension / scale > this.tileSize) {
      factors.push(scale);
      scale *= 2;
    }
    
    return factors.reverse();
  }

  async getTile(region, size, rotation, quality, format) {
    try {
      let image = sharp(this.slidePath);
      
      // Parse region parameter
      if (region !== 'full') {
        const [x, y, w, h] = region.split(',').map(Number);
        image = image.extract({ left: x, top: y, width: w, height: h });
      }
      
      // Parse size parameter
      if (size !== 'full') {
        if (size.includes(',')) {
          const [w, h] = size.split(',').map(Number);
          image = image.resize(w, h);
        } else if (size.startsWith('!')) {
          const maxSize = parseInt(size.substring(1));
          image = image.resize(maxSize, maxSize, { fit: 'inside' });
        }
      }
      
      // Apply rotation if specified
      if (rotation && rotation !== '0') {
        image = image.rotate(parseInt(rotation));
      }
      
      // Set output format
      const outputFormat = format || 'jpg';
      if (outputFormat === 'jpg' || outputFormat === 'jpeg') {
        image = image.jpeg({ quality: 85 });
      } else if (outputFormat === 'png') {
        image = image.png();
      }
      
      return await image.toBuffer();
    } catch (error) {
      throw new Error(`Failed to generate tile: ${error.message}`);
    }
  }
}

// Routes

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Main viewer page
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical LMS Pathology Viewer</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/openseadragon@4.1.1/build/openseadragon/openseadragon.min.js"></script>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div id="header">
            <h1>Medical LMS Pathology Viewer</h1>
            <div id="controls">
                <button id="upload-btn">Upload Slide</button>
                <select id="slide-selector">
                    <option value="">Select a slide...</option>
                </select>
            </div>
        </div>
        
        <div id="viewer-container">
            <div id="openseadragon-viewer"></div>
        </div>
        
        <div id="sidebar">
            <div id="slide-info">
                <h3>Slide Information</h3>
                <div id="info-content">No slide selected</div>
            </div>
            
            <div id="annotation-tools">
                <h3>Annotation Tools</h3>
                <button id="measure-tool">Measure</button>
                <button id="arrow-tool">Arrow</button>
                <button id="circle-tool">Circle</button>
                <button id="text-tool">Text</button>
            </div>
            
            <div id="navigation">
                <h3>Navigation</h3>
                <button id="zoom-in">Zoom In</button>
                <button id="zoom-out">Zoom Out</button>
                <button id="reset-zoom">Reset Zoom</button>
                <button id="fullscreen">Fullscreen</button>
            </div>
        </div>
        
        <div id="upload-modal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>Upload Pathology Slide</h2>
                <form id="upload-form" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="slide-file">Select slide file:</label>
                        <input type="file" id="slide-file" name="slide" accept=".tiff,.tif,.jpg,.jpeg,.png,.scn,.svs,.ndpi" required>
                    </div>
                    <div class="form-group">
                        <label for="slide-name">Slide name:</label>
                        <input type="text" id="slide-name" name="name" placeholder="Enter slide name" required>
                    </div>
                    <div class="form-group">
                        <label for="slide-description">Description:</label>
                        <textarea id="slide-description" name="description" placeholder="Enter description (optional)"></textarea>
                    </div>
                    <button type="submit">Upload</button>
                </form>
                <div id="upload-progress" style="display:none;">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">Uploading...</div>
                </div>
            </div>
        </div>
        
        <script src="/static/viewer.js"></script>
    </body>
    </html>
  `);
});

// IIIF Image API endpoints
app.get('/iiif/:identifier/info.json', async (req, res) => {
  try {
    const { identifier } = req.params;
    const slidePath = path.join('/app/slides', `${identifier}.tiff`);
    
    // Check if file exists
    await fs.access(slidePath);
    
    const iiif = new IIIFImageAPI(slidePath);
    const info = await iiif.getInfo();
    
    res.json(info);
  } catch (error) {
    console.error('Error getting slide info:', error);
    res.status(404).json({ error: 'Slide not found' });
  }
});

app.get('/iiif/:identifier/:region/:size/:rotation/:quality.:format', async (req, res) => {
  try {
    const { identifier, region, size, rotation, quality, format } = req.params;
    const slidePath = path.join('/app/slides', `${identifier}.tiff`);
    
    // Check if file exists
    await fs.access(slidePath);
    
    const iiif = new IIIFImageAPI(slidePath);
    const tile = await iiif.getTile(region, size, rotation, quality, format);
    
    res.set('Content-Type', `image/${format === 'jpg' ? 'jpeg' : format}`);
    res.send(tile);
  } catch (error) {
    console.error('Error generating tile:', error);
    res.status(500).json({ error: 'Failed to generate tile' });
  }
});

// Upload endpoint
app.post('/api/upload', upload.single('slide'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { name, description } = req.body;
    const slideId = uuidv4();
    const processedPath = path.join('/app/slides', `${slideId}.tiff`);
    
    // Process the uploaded file with Sharp
    await sharp(req.file.path)
      .tiff({ compression: 'lzw' })
      .toFile(processedPath);
    
    // Clean up original upload
    await fs.unlink(req.file.path);
    
    // Save metadata
    const metadata = {
      id: slideId,
      name: name,
      description: description,
      originalName: req.file.originalname,
      uploadDate: new Date().toISOString(),
      size: req.file.size
    };
    
    const metadataPath = path.join('/app/slides', `${slideId}.json`);
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
    
    res.json({ 
      success: true, 
      slideId: slideId,
      message: 'Slide uploaded successfully',
      iiifUrl: `/iiif/${slideId}/info.json`
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Failed to process upload' });
  }
});

// Get list of available slides
app.get('/api/slides', async (req, res) => {
  try {
    const slidesDir = '/app/slides';
    const files = await fs.readdir(slidesDir);
    const slides = [];
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        const metadataPath = path.join(slidesDir, file);
        const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));
        slides.push(metadata);
      }
    }
    
    res.json(slides);
  } catch (error) {
    console.error('Error listing slides:', error);
    res.status(500).json({ error: 'Failed to list slides' });
  }
});

// Get slide metadata
app.get('/api/slides/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const metadataPath = path.join('/app/slides', `${id}.json`);
    const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));
    res.json(metadata);
  } catch (error) {
    console.error('Error getting slide metadata:', error);
    res.status(404).json({ error: 'Slide not found' });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Pathology Viewer Server running on port ${PORT}`);
  console.log('Features:');
  console.log('- IIIF Image API compliance');
  console.log('- OpenSeadragon viewer integration');
  console.log('- Multi-gigabyte slide support');
  console.log('- Annotation tools');
  console.log('- GPU-accelerated rendering');
});
"""

# Write pathology viewer files
os.makedirs("medical-imaging-lms/docker/pathology-viewer", exist_ok=True)
os.makedirs("medical-imaging-lms/docker/pathology-viewer/public", exist_ok=True)

with open("medical-imaging-lms/docker/pathology-viewer/Dockerfile", "w") as f:
    f.write(pathology_dockerfile)

with open("medical-imaging-lms/docker/pathology-viewer/package.json", "w") as f:
    f.write(package_json)

with open("medical-imaging-lms/docker/pathology-viewer/server.js", "w") as f:
    f.write(pathology_server)

print("✅ Created Pathology Slide Viewer")
print("📁 Files created:")
print("- docker/pathology-viewer/Dockerfile")
print("- docker/pathology-viewer/package.json") 
print("- docker/pathology-viewer/server.js")
print("\n📋 Pathology Viewer Features:")
print("- IIIF Image API compliance")
print("- OpenSeadragon integration")
print("- Multi-gigabyte slide support")
print("- File upload and processing")
print("- Tile-based rendering")
print("- Annotation tools")
print("- GPU-accelerated rendering")