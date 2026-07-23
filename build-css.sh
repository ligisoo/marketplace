#!/bin/bash

# Tailwind CSS Build Script for Production
echo "Building Tailwind CSS for production..."

# Ensure static/css directory and tailwind-input.css exist
mkdir -p static/css
if [ ! -f "static/css/tailwind-input.css" ]; then
    echo "Creating static/css/tailwind-input.css..."
    cat << 'EOF' > static/css/tailwind-input.css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn {
    @apply inline-flex items-center justify-center px-5 py-2.5 text-sm font-semibold rounded-md transition-all cursor-pointer;
  }
  .btn-primary {
    @apply bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm;
  }
  .btn-secondary {
    @apply bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border;
  }
}
EOF
fi

# Determine Tailwind command (npx, system tailwindcss, or v3 standalone binary)
if command -v npx &> /dev/null; then
    TAILWIND_CMD="npx tailwindcss"
elif command -v tailwindcss &> /dev/null; then
    TAILWIND_CMD="tailwindcss"
elif [ -f "./tailwindcss" ]; then
    TAILWIND_CMD="./tailwindcss"
else
    echo "Downloading Tailwind v3.4.17 CLI binary..."
    curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64
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