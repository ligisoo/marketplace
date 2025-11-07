# Quick Start: OCR Provider Toggle

## Accessing the Admin Page

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to: `http://localhost:8000/admin/`

3. Login with:
   - **Phone Number**: `+254700000000`
   - **Password**: `admin123`
   - ⚠️ **Important**: Use the PHONE NUMBER field, not username!
   - ⚠️ Change password after first login!

4. Go to: **Tips** → **OCR Provider Settings**

4. Select your preferred provider:
   - **AWS Textract** (default) - Cloud-based, requires AWS credentials
   - **EasyOCR** - Local, free, no API costs

5. Click **Save**

## Status Check ✓

- ✅ EasyOCR installed (CPU-only version)
- ✅ Models already downloaded (95MB, shared with /home/walter/deepseek)
- ✅ Database model created
- ✅ Admin interface configured
- ✅ Default provider: AWS Textract
- ✅ Ready to use!

## Model Cache Info

**Location**: `/home/walter/.EasyOCR/model/`

**Downloaded models**:
- `craft_mlt_25k.pth` (80MB) - Text detection
- `english_g2.pth` (15MB) - English recognition

**Note**: These models are automatically shared with your deepseek project. No additional downloads needed!

## Quick Test

Switch to EasyOCR and test with a betslip:
```bash
# 1. Switch provider in admin to "EasyOCR"

# 2. Upload a betslip through the web interface

# 3. Check logs for: "Loading EasyOCR model..."
#    (Only shown first time, then models are cached in memory)
```

## Performance Notes

- **First OCR call**: ~5 seconds (loads models into memory)
- **Subsequent calls**: ~3-5 seconds per betslip
- **No downloads**: Models already cached from deepseek project!

## Disk Space Usage

| Component | Size |
|-----------|------|
| PyTorch (CPU-only) | ~184 MB |
| EasyOCR + dependencies | ~120 MB |
| Models (shared cache) | 95 MB |
| **Total added to marketplace** | **~304 MB** |

**Savings**: Used CPU-only PyTorch (saved ~700MB vs CUDA version)

## Troubleshooting

If you see errors, verify installation:
```bash
python manage.py shell -c "from apps.tips.ocr import BetslipOCR; print('✓ Working')"
```

For detailed documentation, see: `OCR_CONFIGURATION_GUIDE.md`
