#!/bin/bash

# Tailwind CSS Build Script for Production
echo "Building Tailwind CSS for production..."

# Build the CSS
tailwindcss -i static/css/tailwind-input.css -o static/css/tailwind-output.css --minify

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ CSS build completed successfully!"
    echo "📁 Output: static/css/tailwind-output.css"
    
    # Show file size
    echo "📊 File size: $(du -h static/css/tailwind-output.css | cut -f1)"
else
    echo "❌ CSS build failed!"
    exit 1
fi