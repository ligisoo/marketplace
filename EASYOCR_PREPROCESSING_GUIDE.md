# EasyOCR Preprocessing Guide

## What Changed

The EasyOCR preprocessing has been improved to be less aggressive, which should significantly improve text recognition accuracy.

### Before (13% confidence)
- ❌ Heavy thresholding (converted to pure black/white)
- ❌ Removed gray tones and detail
- ❌ Too aggressive for some betslip formats

### After (Should be 70%+ confidence)
- ✅ Light sharpening (enhances edges)
- ✅ Preserves gray tones and detail
- ✅ Better for varied betslip formats

## Preprocessing Strategies Available

The system now supports 4 preprocessing strategies in `apps/tips/ocr.py:175`:

### 1. **None** (`strategy='none'`)
- No preprocessing, uses original image
- Best for: High-quality, clear screenshots
- Speed: Fastest

### 2. **Light** (`strategy='light'`) ⭐ DEFAULT
- Grayscale + gentle sharpening
- Best for: Most betslips, general use
- Speed: Fast
- **Currently active**

### 3. **Medium** (`strategy='medium'`)
- Grayscale + contrast enhancement (CLAHE)
- Best for: Low contrast or faded images
- Speed: Medium

### 4. **Heavy** (`strategy='heavy'`)
- Full pipeline: blur + contrast + thresholding
- Best for: Very noisy or poor quality images
- Speed: Slower
- **Note**: This was the old default that gave 13% confidence

## How to Change Preprocessing Strategy

Edit `apps/tips/ocr.py` line 175:

```python
# Current (Light preprocessing)
processed_path = self._preprocess_image(tmp_path, strategy='light')

# Try different strategies:
processed_path = self._preprocess_image(tmp_path, strategy='none')    # No preprocessing
processed_path = self._preprocess_image(tmp_path, strategy='medium')  # Medium preprocessing
processed_path = self._preprocess_image(tmp_path, strategy='heavy')   # Heavy preprocessing
```

## Testing Results

Upload the same betslip and compare:

| Strategy | Expected Confidence | Best For |
|----------|-------------------|----------|
| None | 60-80% | Clear images |
| **Light** | **70-90%** | **General use (DEFAULT)** |
| Medium | 65-85% | Low contrast |
| Heavy | 40-70% | Very poor quality |

## Recommendations

1. **Start with Light** (current default) - works for most betslips
2. **If confidence < 50%**: Try 'medium' strategy
3. **If confidence > 80%**: Consider 'none' (faster)
4. **Avoid 'heavy'** unless image is severely degraded

## Image Quality Tips

For best results with EasyOCR:
- ✅ Resolution: At least 1000px wide
- ✅ Format: PNG or high-quality JPG
- ✅ Lighting: Even, not too dark or bright
- ✅ Focus: Sharp, not blurry
- ✅ Angle: Straight, not tilted

## Comparing with AWS Textract

| Feature | EasyOCR (Light) | AWS Textract |
|---------|----------------|--------------|
| Typical Confidence | 70-90% | 90-98% |
| Speed | 3-5 seconds | 1-2 seconds |
| Cost | Free | $1-2 per 1000 images |
| Quality | Good | Excellent |
| Internet Required | No | Yes |

## Troubleshooting

### Still getting low confidence?

1. **Check image quality**: Is text readable to human eye?
2. **Try different strategy**: Test 'none' or 'medium'
3. **Switch to Textract**: Via Admin → Tips → OCR Provider Settings
4. **Check logs**: Look for preprocessing messages

### Where to find preprocessed images?

Preprocessed images are temporarily saved as:
```
/tmp/processed_light_<filename>.png
```

You can inspect these to see how preprocessing affects the image.

## Code Location

All preprocessing code is in:
- File: `apps/tips/ocr.py`
- Method: `_preprocess_image()` (line 222)
- Call site: `_extract_text_easyocr()` (line 175)
