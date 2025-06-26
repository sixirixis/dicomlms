# Create the Unified Medical Viewer (React app) that switches between DICOM and pathology viewers
unified_dockerfile = """FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build the React application
RUN npm run build

# Production stage
FROM node:18-alpine

# Install serve to host the built React app
RUN npm install -g serve@14 && \\
    addgroup -g 1001 -S nodejs && \\
    adduser -S nextjs -u 1001

# Set working directory
WORKDIR /app

# Copy build output from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/build ./build

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \\
    CMD wget -q -O /dev/null http://localhost:3000 || exit 1

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"]
"""

# Create package.json for unified viewer
unified_package_json = """{
  "name": "medical-lms-unified-viewer",
  "version": "1.0.0",
  "description": "Unified medical imaging viewer for DICOM and pathology slides",
  "homepage": "/",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.6.2",
    "openseadragon": "^4.1.1",
    "@types/openseadragon": "^3.0.10",
    "cornerstone-core": "^2.6.1",
    "cornerstone-tools": "^6.0.10",
    "dicom-parser": "^1.8.21",
    "cornerstone-wado-image-loader": "^4.13.2",
    "hammerjs": "^2.0.8",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "@mui/material": "^5.15.2",
    "@mui/icons-material": "^5.15.2",
    "styled-components": "^6.1.6",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.68",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.5",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8042"
}"""

# Create the main App component
app_component = """import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  Container,
  Alert,
  CircularProgress
} from '@mui/material';
import MedicalImagingActivity from './components/MedicalImagingActivity';
import StudySelector from './components/StudySelector';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1a',
        },
      },
    },
  },
});

const ViewerWrapper: React.FC = () => {
  const { studyUID } = useParams<{ studyUID: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading delay for demonstration
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, [studyUID]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="70vh">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading medical imaging viewer...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      <MedicalImagingActivity studyUID={studyUID || ''} />
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Medical LMS - Imaging Viewer
              </Typography>
              <Typography variant="body2" sx={{ mr: 2 }}>
                Unified DICOM & Pathology Viewer
              </Typography>
            </Toolbar>
          </AppBar>
          
          <Routes>
            <Route path="/" element={<StudySelector />} />
            <Route path="/viewer/:studyUID" element={<ViewerWrapper />} />
            <Route path="/study/:studyUID" element={<ViewerWrapper />} />
          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;
"""

# Create the core MedicalImagingActivity component
medical_imaging_component = """import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import DICOMViewer from './DICOMViewer';
import PathologyViewer from './PathologyViewer';

interface MedicalImagingActivityProps {
  studyUID: string;
}

const MedicalImagingActivity: React.FC<MedicalImagingActivityProps> = ({ studyUID }) => {
  const [viewerType, setViewerType] = useState<'dicom' | 'pathology' | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const determineViewerType = () => {
      try {
        // Logic to determine viewer type based on study UID
        // WSI_ prefix indicates whole slide imaging (pathology)
        // All other studies are treated as DICOM
        if (studyUID.includes('WSI_') || studyUID.includes('pathology') || studyUID.includes('slide')) {
          setViewerType('pathology');
        } else {
          setViewerType('dicom');
        }
        setLoading(false);
      } catch (err) {
        setError('Failed to determine viewer type');
        setLoading(false);
      }
    };

    if (studyUID) {
      determineViewerType();
    } else {
      setError('No study UID provided');
      setLoading(false);
    }
  }, [studyUID]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Determining viewer type...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  // Unified viewer framework switching based on study UID
  return (
    <Box height="100%" width="100%">
      {viewerType === 'pathology' ? (
        <PathologyViewer studyUID={studyUID} />
      ) : (
        <DICOMViewer studyUID={studyUID} />
      )}
    </Box>
  );
};

export default MedicalImagingActivity;
"""

# Create DICOM Viewer component
dicom_viewer_component = """import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Alert, IconButton, Toolbar, Paper } from '@mui/material';
import { 
  ZoomIn, 
  ZoomOut, 
  Refresh, 
  Fullscreen, 
  PlayArrow, 
  Pause,
  Settings 
} from '@mui/icons-material';

interface DICOMViewerProps {
  studyUID: string;
}

const DICOMViewer: React.FC<DICOMViewerProps> = ({ studyUID }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const ohifUrl = process.env.REACT_APP_OHIF_URL || 'http://localhost:3000';
  const orthancUrl = process.env.REACT_APP_ORTHANC_URL || 'http://localhost:8042';

  useEffect(() => {
    const loadDICOMStudy = async () => {
      try {
        setLoading(true);
        
        // Construct OHIF viewer URL with study UID
        const viewerUrl = `${ohifUrl}/viewer?studyInstanceUIDs=${encodeURIComponent(studyUID)}`;
        
        // Set the iframe source
        if (iframeRef.current) {
          iframeRef.current.src = viewerUrl;
        }
        
        setLoading(false);
      } catch (err) {
        setError(`Failed to load DICOM study: ${err}`);
        setLoading(false);
      }
    };

    if (studyUID) {
      loadDICOMStudy();
    }
  }, [studyUID, ohifUrl]);

  const handleIframeLoad = () => {
    setLoading(false);
  };

  const handleIframeError = () => {
    setError('Failed to load OHIF viewer');
    setLoading(false);
  };

  const handleZoomIn = () => {
    // Send message to OHIF viewer iframe
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ type: 'ZOOM_IN' }, '*');
    }
  };

  const handleZoomOut = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ type: 'ZOOM_OUT' }, '*');
    }
  };

  const handleReset = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ type: 'RESET' }, '*');
    }
  };

  const handleFullscreen = () => {
    if (iframeRef.current?.requestFullscreen) {
      iframeRef.current.requestFullscreen();
    }
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ 
        type: isPlaying ? 'PAUSE' : 'PLAY' 
      }, '*');
    }
  };

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Typography variant="body2">
          Study UID: {studyUID}
        </Typography>
      </Box>
    );
  }

  return (
    <Box height="100%" display="flex" flexDirection="column">
      <Paper elevation={2} sx={{ mb: 1 }}>
        <Toolbar variant="dense" sx={{ minHeight: 48 }}>
          <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
            DICOM Viewer - Study: {studyUID}
          </Typography>
          
          <IconButton size="small" onClick={handleZoomIn} title="Zoom In">
            <ZoomIn />
          </IconButton>
          
          <IconButton size="small" onClick={handleZoomOut} title="Zoom Out">
            <ZoomOut />
          </IconButton>
          
          <IconButton size="small" onClick={handleReset} title="Reset View">
            <Refresh />
          </IconButton>
          
          <IconButton size="small" onClick={togglePlayback} title={isPlaying ? "Pause" : "Play"}>
            {isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
          
          <IconButton size="small" onClick={handleFullscreen} title="Fullscreen">
            <Fullscreen />
          </IconButton>
          
          <IconButton size="small" title="Settings">
            <Settings />
          </IconButton>
        </Toolbar>
      </Paper>
      
      <Box position="relative" flex={1}>
        {loading && (
          <Box 
            position="absolute" 
            top="50%" 
            left="50%" 
            style={{ transform: 'translate(-50%, -50%)' }}
            zIndex={1}
          >
            <Typography variant="body1">Loading DICOM viewer...</Typography>
          </Box>
        )}
        
        <iframe
          ref={iframeRef}
          title="OHIF DICOM Viewer"
          width="100%"
          height="100%"
          style={{ 
            border: 'none',
            backgroundColor: '#000',
            display: loading ? 'none' : 'block'
          }}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </Box>
    </Box>
  );
};

export default DICOMViewer;
"""

# Write unified viewer files
os.makedirs("medical-imaging-lms/unified-viewer/src/components", exist_ok=True)
os.makedirs("medical-imaging-lms/unified-viewer/public", exist_ok=True)

with open("medical-imaging-lms/unified-viewer/Dockerfile", "w") as f:
    f.write(unified_dockerfile)

with open("medical-imaging-lms/unified-viewer/package.json", "w") as f:
    f.write(unified_package_json)

with open("medical-imaging-lms/unified-viewer/src/App.tsx", "w") as f:
    f.write(app_component)

with open("medical-imaging-lms/unified-viewer/src/components/MedicalImagingActivity.tsx", "w") as f:
    f.write(medical_imaging_component)

with open("medical-imaging-lms/unified-viewer/src/components/DICOMViewer.tsx", "w") as f:
    f.write(dicom_viewer_component)

print("✅ Created Unified Medical Viewer")
print("📁 Files created:")
print("- unified-viewer/Dockerfile")
print("- unified-viewer/package.json")
print("- unified-viewer/src/App.tsx")
print("- unified-viewer/src/components/MedicalImagingActivity.tsx")
print("- unified-viewer/src/components/DICOMViewer.tsx")
print("\n📋 Unified Viewer Features:")
print("- React-based modern interface")
print("- Automatic viewer switching (DICOM vs Pathology)")
print("- OHIF viewer integration via iframe")
print("- Material-UI components")
print("- TypeScript support")
print("- Mobile-responsive design")