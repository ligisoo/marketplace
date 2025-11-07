# OCR Configuration Guide

This guide explains how to configure and use the dual OCR provider system (AWS Textract and EasyOCR) in the marketplace application.

## Overview

The application now supports two OCR providers:
1. **AWS Textract** - Cloud-based OCR service (requires AWS credentials)
2. **EasyOCR** - Open-source OCR library (runs locally, CPU-only)

## Features

- **Seamless switching**: Toggle between OCR providers via Django admin
- **Same interface**: Both providers use the same parsing logic
- **CPU-optimized**: EasyOCR uses CPU-only PyTorch to minimize resource usage
- **Automatic fallback**: System defaults to Textract if not configured

## Configuration

### Accessing OCR Settings

1. Log in to Django Admin: `/admin/`
2. Navigate to **Tips** → **OCR Provider Settings**
3. Select your desired OCR provider from the dropdown
4. Click **Save**

The system will automatically use the selected provider for all new betslip uploads.

### Provider Details

#### AWS Textract (Default)
- **Pros**: High accuracy, fast processing, no local resources needed
- **Cons**: Requires AWS account and credentials, incurs costs
- **Requirements**:
  - AWS credentials configured in settings.py
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_S3_REGION_NAME`

#### EasyOCR
- **Pros**: Free, runs locally, no external API calls, models cached globally
- **Cons**: First run downloads model files (~95MB) if not cached, slightly slower than Textract
- **Requirements**: Already installed (CPU-only version)
- **Dependencies**: `easyocr`, `opencv-python-headless`, `pytorch-cpu`
- **Model Cache**: Uses `~/.EasyOCR/model/` - shared across all projects on this server
- **Status**: ✓ Models already downloaded from `/home/walter/deepseek` project (95MB saved!)

## Installation (Already Completed)

The following packages were installed with CPU-only PyTorch to minimize disk space:

```bash
# PyTorch CPU-only (saves ~700MB compared to CUDA version)
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.0+cpu torchvision==0.24.0+cpu

# EasyOCR and dependencies
pip install easyocr==1.7.2 opencv-python-headless==4.12.0.88 python-bidi==0.6.7 \
    pyclipper==1.3.0.post6 scikit-image==0.25.2 scipy==1.15.3 \
    PyYAML==6.0.3 shapely==2.1.2
```

## Usage

### For Administrators

1. **Switching Providers**:
   - Go to Admin → Tips → OCR Provider Settings
   - Change the "Provider" field
   - Save the changes
   - All subsequent betslip uploads will use the new provider

2. **Monitoring**:
   - Check application logs for OCR processing status
   - Both providers log their activity for debugging

### For Developers

#### Using the BetslipOCR class:

```python
from apps.tips.ocr import BetslipOCR

# Uses the provider configured in admin
ocr = BetslipOCR()

# Or specify a provider explicitly
ocr = BetslipOCR(provider='easyocr')
ocr = BetslipOCR(provider='textract')

# Process image
result = ocr.process_betslip_image(image_file)
```

#### Checking Current Provider:

```python
from apps.tips.models import OCRProviderSettings

current_provider = OCRProviderSettings.get_active_provider()
print(f"Current OCR provider: {current_provider}")
```

## Technical Details

### Database Model

The `OCRProviderSettings` model (apps/tips/models.py:183):
- Stores a single settings record
- Tracks the active provider ('textract' or 'easyocr')
- Records who last updated the settings and when

### OCR Processing Flow

1. User uploads betslip screenshot
2. System checks `OCRProviderSettings` for active provider
3. `BetslipOCR` initialized with selected provider
4. Image processed using appropriate OCR backend
5. Text extracted and parsed using shared parsing logic
6. Matches, odds, and betting info extracted

### Image Preprocessing (EasyOCR only)

EasyOCR includes image preprocessing for better accuracy:
- Grayscale conversion
- Noise reduction
- Contrast enhancement (CLAHE)
- Adaptive thresholding

This preprocessing is automatically applied when using EasyOCR.

## Troubleshooting

### EasyOCR First Run
- **Issue**: Slow first execution
- **Cause**: EasyOCR downloads model files (~95MB) on first use
- **Solution**: Normal behavior, subsequent runs will be faster
- **Note**: Models are cached at `~/.EasyOCR/model/` and shared across all applications on the same user account. If you've already used EasyOCR in another project (like `/home/walter/deepseek`), the models are already downloaded and will be reused automatically!

### Import Errors
- **Issue**: `ModuleNotFoundError: No module named 'cv2'` or `'easyocr'`
- **Solution**: Reinstall dependencies:
  ```bash
  pip install opencv-python-headless easyocr
  ```

### Low OCR Accuracy
- **EasyOCR**: Try uploading higher quality images, ensure good lighting
- **Textract**: Check AWS service status, verify credentials

### Provider Not Changing
- **Issue**: OCR still using old provider
- **Solution**:
  1. Verify settings in admin are saved
  2. Restart Django application
  3. Check logs for initialization messages

## Performance Comparison

| Metric | AWS Textract | EasyOCR (CPU) |
|--------|-------------|---------------|
| Setup Time | Instant | ~5s (first run) |
| Processing Speed | ~1-2s | ~3-5s |
| Accuracy | Very High | High |
| Cost | Per request | Free |
| Internet Required | Yes | No |
| Disk Space | Minimal | ~400MB |

## Files Modified

1. `apps/tips/models.py` - Added `OCRProviderSettings` model
2. `apps/tips/admin.py` - Added admin interface for settings
3. `apps/tips/ocr.py` - Added EasyOCR integration
4. `apps/tips/migrations/0002_ocrprovidersettings.py` - Database migration

## Next Steps

1. **Monitor Performance**: Track OCR accuracy and processing times
2. **Cost Analysis**: Compare AWS Textract costs vs server resources for EasyOCR
3. **Optimization**: Fine-tune preprocessing parameters for your specific betslip formats
4. **Backup Strategy**: Consider having both providers available for failover

## Model Cache Management

### EasyOCR Model Location
EasyOCR models are stored at: `~/.EasyOCR/model/`

Current models (already downloaded):
- `craft_mlt_25k.pth` (80MB) - Text detection model
- `english_g2.pth` (15MB) - English recognition model

### Benefits of Shared Cache
- **Multi-project sharing**: All EasyOCR applications on this server use the same models
- **No redundant downloads**: Models downloaded once, used everywhere
- **Disk space savings**: 95MB saved per additional project
- **Faster initialization**: No waiting for downloads after first use

### Manual Model Management
If you need to clear or re-download models:
```bash
# Remove models (they'll be re-downloaded on next use)
rm -rf ~/.EasyOCR/model/

# Check model cache size
du -sh ~/.EasyOCR/model/
```

## Support

For issues or questions:
- Check application logs: `logs/` directory
- Review betslip processing in Django admin
- Verify OCR provider settings are correct
- Inspect model cache: `ls -lh ~/.EasyOCR/model/`
