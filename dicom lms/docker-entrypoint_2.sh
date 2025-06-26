#!/bin/sh
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
