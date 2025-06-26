# Create OHIF Viewer Dockerfile and configuration
ohif_dockerfile = """FROM node:18-alpine as builder

# Install system dependencies
RUN apk add --no-cache git python3 make g++

# Clone OHIF Viewer repository
WORKDIR /usr/src
RUN git clone --branch v3.7.1 --depth 1 https://github.com/OHIF/Viewers.git ohif-viewer

# Build OHIF Viewer
WORKDIR /usr/src/ohif-viewer
RUN yarn config set network-timeout 600000 && \\
    yarn install && \\
    yarn run build

# Production image
FROM node:18-alpine

# Set working directory
WORKDIR /usr/src/app

# Copy build output from builder stage
COPY --from=builder /usr/src/ohif-viewer/platform/app/dist /usr/src/app/dist

# Install serve to host the built application
RUN npm install -g serve@14 && \\
    mkdir -p /usr/src/app/config

# Copy custom configuration
COPY config/. /usr/src/app/config/
COPY docker-entrypoint.sh /usr/src/app/
RUN chmod +x /usr/src/app/docker-entrypoint.sh

# Expose port for web access
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \\
    CMD wget -q -O /dev/null http://localhost:3000 || exit 1

# Set environment variable
ENV PORT=3000
ENV OHIF_STATIC_ROOT=/usr/src/app/dist
ENV APP_CONFIG=/usr/src/app/config/default.js

# Start the application
ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
CMD ["serve", "-C", "-s", "dist", "-l", "3000"]
"""

# Create OHIF configuration file
ohif_config = """// OHIF Viewer v3 configuration
window.config = {
  routerBasename: '/',
  showStudyList: true,
  extensions: [
    '@ohif/extension-cornerstone',
    '@ohif/extension-cornerstone-dicom-sr',
    '@ohif/extension-measurement-tracking',
    '@ohif/extension-cornerstone-dicom-seg',
    '@ohif/extension-cornerstone-dicom-rt',
    '@ohif/extension-dicom-microscopy',
    '@ohif/extension-dicom-pdf',
    '@ohif/extension-dicom-video',
  ],
  modes: [
    {
      id: 'viewer',
      displayName: 'Basic Viewer',
      route: 'viewer',
      extensions: [
        '@ohif/extension-cornerstone',
        '@ohif/extension-measurement-tracking',
        '@ohif/extension-cornerstone-dicom-sr',
        '@ohif/extension-cornerstone-dicom-seg',
        '@ohif/extension-cornerstone-dicom-rt',
        '@ohif/extension-dicom-microscopy',
        '@ohif/extension-dicom-pdf',
        '@ohif/extension-dicom-video',
      ],
    },
    {
      id: 'segmentation',
      displayName: 'Segmentation',
      route: 'segmentation',
      extensions: [
        '@ohif/extension-cornerstone',
        '@ohif/extension-cornerstone-dicom-seg',
        '@ohif/extension-measurement-tracking'
      ],
      isPrimary: false,
    },
    {
      id: 'tracking',
      displayName: 'Measurement Tracking',
      route: 'tracking',
      extensions: [
        '@ohif/extension-cornerstone',
        '@ohif/extension-measurement-tracking',
        '@ohif/extension-cornerstone-dicom-sr',
      ],
      isPrimary: false,
    },
    {
      id: 'volumetric',
      displayName: '3D Rendering',
      route: 'volumetric',
      extensions: [
        '@ohif/extension-cornerstone',
        '@ohif/extension-measurement-tracking',
      ],
      isPrimary: false,
    },
  ],
  maxNumberOfWebWorkers: 3,
  showLoadingIndicator: true,
  strictZSpacingForVolumeViewport: true,
  maxNumRequests: {
    interaction: 100,
    thumbnail: 75,
    prefetch: 10,
  },
  filterQueryParam: true,
  dataSources: [
    {
      namespace: '@ohif/extension-default.dataSourcesModule.dicomweb',
      sourceName: 'dicomweb',
      configuration: {
        friendlyName: 'Medical LMS Orthanc Server',
        name: 'orthanc',
        wadoUriRoot: 'http://orthanc-server:8042/wado',
        qidoRoot: 'http://orthanc-server:8042/dicom-web',
        wadoRoot: 'http://orthanc-server:8042/dicom-web',
        qidoSupportsIncludeField: false,
        supportsReject: false,
        imageRendering: 'wadors',
        thumbnailRendering: 'wadors',
        enableStudyLazyLoad: true,
        supportsFuzzyMatching: false,
        supportsWildcard: true,
        staticWado: true,
        singlepart: 'bulkdata,video',
        dicomUploadEnabled: true,
        directStorageEnabled: true,
        authorizationHeaders: {
          /* If you need authentication, add authorization headers here */
        },
      },
    },
  ],
  defaultDataSourceName: 'dicomweb',
  hotkeys: [
    {
      commandName: 'nextViewport',
      label: 'Next Viewport',
      keys: ['right'],
      column: 1,
    },
    {
      commandName: 'previousViewport',
      label: 'Previous Viewport',
      keys: ['left'],
      column: 1,
    },
    {
      commandName: 'resetViewport',
      label: 'Reset Viewport',
      keys: ['space'],
      column: 2,
    },
    {
      commandName: 'toggleCine',
      label: 'Toggle CINE Play',
      keys: ['p'],
      column: 2,
    },
    {
      commandName: 'setWWWC',
      label: 'Window Width/Center',
      keys: ['w'],
      column: 3,
    },
    {
      commandName: 'zoom',
      label: 'Zoom',
      keys: ['z'],
      column: 3,
    },
    {
      commandName: 'pan',
      label: 'Pan',
      keys: ['h'],
      column: 3,
    },
    {
      commandName: 'toggleOverlayMode',
      label: 'Toggle Overlay',
      keys: ['o'],
      column: 4,
    },
    {
      commandName: 'toggleAnnotations',
      label: 'Toggle Annotations',
      keys: ['a'],
      column: 4,
    },
  ],
  cornerstoneExtensionConfig: {
    tools: {
      ArrowAnnotate: {
        configuration: {
          getTextCallback: (callback, eventDetails) => callback(prompt('Enter your annotation:')),
        },
      },
    },
    viewports: {
      defaultViewport: {
        background: [0, 0, 0],
      },
    },
  },
  i18n: {
    UI: 'en-US',
    '3D': 'en-US',
  },
  enableGoogleCloudAdapter: false,
  enableProgressiveWebApp: true,
  pwa: {
    name: 'OHIF Viewer',
    shortName: 'OHIF',
    themeColor: '#00529B',
    backgroundColor: '#000000',
    display: 'standalone',
  },
  // HIPAA-compliance features
  requiredConsent: {
    enabled: true,
    text: 'Access to patient data requires user authentication and consent.',
  },
  mediaPreview: {
    enabled: true,
    webWorkers: true,
  },
};

// Enables GPU acceleration for medical imaging rendering
window.config.experimentalFeatures = {
  // OHIF v3 GPU acceleration for faster rendering
  enableGPUAcceleration: true,
  // Maximum GPU memory to use (in MB)
  maxGPUMemory: 4096,
  // Enable WebGL-based volume rendering
  enableWebGLVolumeRendering: true,
  // Use WebGL 2.0 when available for better performance
  useWebGL2: true,
  // Enable more advanced multi-planar reformatting
  enableAdvancedMPR: true,
  // Enable 3D annotation tools
  enable3DTools: true,
};

// For integration with Medical LMS
window.config.moodleIntegration = {
  enabled: true,
  moodleUrl: 'http://moodle-app',
  redirectUrl: '/mod/medical_imaging/view.php',
  saveAnnotations: true,
  saveReport: true,
  saveScreenshots: true,
};
"""

# Create OHIF entrypoint script
ohif_entrypoint = """#!/bin/sh
set -e

# Create app configuration from environment or use default
if [ -n "$APP_CONFIG" ]; then
    echo "Using configuration from $APP_CONFIG"
else
    echo "Warning: No APP_CONFIG environment variable set, using default configuration"
    export APP_CONFIG="/usr/src/app/config/default.js"
fi

# Set up runtime configuration based on environment variables
if [ -n "$PROXY_TARGET" ]; then
    echo "Setting up Orthanc proxy to $PROXY_TARGET"
    # Update configuration to use the specified Orthanc server
    sed -i "s|http://orthanc-server:8042|$PROXY_TARGET|g" "$APP_CONFIG"
fi

# Optimize for GPU acceleration
if [ "$ENABLE_GPU_ACCELERATION" = "true" ]; then
    echo "Enabling GPU acceleration for medical imaging rendering"
    sed -i "s|enableGPUAcceleration: .*,|enableGPUAcceleration: true,|g" "$APP_CONFIG"
    
    # Set GPU memory limit if provided
    if [ -n "$GPU_MEMORY_LIMIT" ]; then
        echo "Setting GPU memory limit to $GPU_MEMORY_LIMIT MB"
        sed -i "s|maxGPUMemory: .*,|maxGPUMemory: $GPU_MEMORY_LIMIT,|g" "$APP_CONFIG"
    fi
else
    echo "GPU acceleration disabled"
    sed -i "s|enableGPUAcceleration: .*,|enableGPUAcceleration: false,|g" "$APP_CONFIG"
fi

# For medical LMS integration
if [ -n "$MOODLE_URL" ]; then
    echo "Configuring Moodle integration with $MOODLE_URL"
    sed -i "s|moodleUrl: .*,|moodleUrl: '$MOODLE_URL',|g" "$APP_CONFIG"
fi

echo "Starting OHIF Viewer..."
exec "$@"
"""

# Write OHIF Viewer configuration files
os.makedirs("medical-imaging-lms/docker/ohif-viewer/config", exist_ok=True)

with open("medical-imaging-lms/docker/ohif-viewer/Dockerfile", "w") as f:
    f.write(ohif_dockerfile)

with open("medical-imaging-lms/docker/ohif-viewer/config/default.js", "w") as f:
    f.write(ohif_config)

with open("medical-imaging-lms/docker/ohif-viewer/docker-entrypoint.sh", "w") as f:
    f.write(ohif_entrypoint)

print("✅ Created OHIF Viewer configuration")
print("📁 Files created:")
print("- docker/ohif-viewer/Dockerfile")
print("- docker/ohif-viewer/config/default.js")
print("- docker/ohif-viewer/docker-entrypoint.sh")
print("\n📋 OHIF Viewer Features:")
print("- DICOMweb integration with Orthanc server")
print("- GPU acceleration for faster rendering")
print("- Multi-planar reconstruction (MPR)")
print("- Measurement and annotation tools")
print("- 3D volume rendering")
print("- DICOM SEG, SR, and RT support")
print("- Integration with Moodle LMS")