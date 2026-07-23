#!/bin/bash

# Tailwind CSS Build Script for Production
echo "Building Tailwind CSS for production..."

# Determine Tailwind command (npx, system tailwindcss, or standalone binary)
if command -v npx &> /dev/null; then
    TAILWIND_CMD="npx tailwindcss"
elif command -v tailwindcss &> /dev/null; then
    TAILWIND_CMD="tailwindcss"
elif [ -f "./tailwindcss" ]; then
    TAILWIND_CMD="./tailwindcss"
else
    echo "Downloading standalone Tailwind CLI binary..."
    curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
    chmod +x tailwindcss-linux-x64
    mv tailwindcss-linux-x64 tailwindcss
    TAILWIND_CMD="./tailwindcss"
fi

echo "Executing: $TAILWIND_CMD -i static/css/tailwind-input.css -o static/css/tailwind-output.css --minify"
$TAILWIND_CMD -i static/css/tailwind-input.css -o static/css/tailwind-output.css --minify

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ CSS build completed successfully!"
    echo "📁 Output: static/css/tailwind-output.css"
    echo "📊 File size: $(du -h static/css/tailwind-output.css | cut -f1)"
else
    echo "❌ CSS build failed!"
    exit 1
fi