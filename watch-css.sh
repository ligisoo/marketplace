#!/bin/bash

# Tailwind CSS Watch Script for Development
echo "🔍 Watching Tailwind CSS files for changes..."
echo "📁 Input: static/css/tailwind-input.css"
echo "📁 Output: static/css/tailwind-output.css"
echo ""
echo "Press Ctrl+C to stop watching"

# Watch for changes and rebuild
tailwindcss -i static/css/tailwind-input.css -o static/css/tailwind-output.css --watch