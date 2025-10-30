# AWS Textract OCR Setup Guide

## Overview
The Ligisoo platform uses AWS Textract to automatically extract betting information from betslip screenshots. This guide will help you configure and test the OCR functionality.

## Prerequisites
- AWS Account with IAM access
- AWS Textract permissions
- Python dependencies installed (boto3, fuzzywuzzy)

## AWS Configuration

### 1. AWS IAM User Setup
Your AWS IAM user is already created:
- **User**: textract-user
- **ARN**: `arn:aws:iam::891377179405:user/textract-user`
- **Console URL**: https://us-east-1.console.aws.amazon.com/iam/home?region=af-south-1#/users/details/textract-user

### 2. Required Permissions
The textract-user should have the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Get Access Keys
1. Go to the IAM console (link above)
2. Click on "Security credentials" tab
3. Click "Create access key"
4. Select "Application running on AWS compute service" or "Other"
5. Copy the **Access Key ID** and **Secret Access Key**

⚠️ **IMPORTANT**: Save these credentials securely! You won't be able to see the secret key again.

## Environment Setup

### 1. Add AWS Credentials to .env
Open the `.env` file and add your AWS credentials:

```env
# AWS Textract Configuration
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID_HERE
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY_HERE
AWS_REGION_NAME=us-east-1
```

### 2. Verify Dependencies
Ensure these packages are installed:
```bash
pip install boto3 fuzzywuzzy python-Levenshtein
```

## Testing the OCR

### Option 1: Using the Test Command
```bash
# Basic test
python manage.py test_ocr /path/to/betslip.jpg

# With debug output
python manage.py test_ocr /path/to/betslip.png --debug
```

### Option 2: Through the Web Interface
1. Log in as a tipster
2. Go to "Create New Tip"
3. Upload a betslip screenshot
4. The system will automatically extract:
   - Bet code
   - Total odds
   - Individual matches
   - Team names
   - Betting markets
   - Match dates

### Option 3: Python Shell
```python
from apps.tips.ocr import BetslipOCR

# Create OCR service
ocr = BetslipOCR()

# Test with an image
with open('/path/to/betslip.jpg', 'rb') as f:
    result = ocr.process_betslip_image(f)
    print(result)
```

## Supported Bookmakers

The OCR is optimized for Kenyan bookmakers:
- ✅ SportPesa
- ✅ Betika
- ✅ Mozzartbet
- ✅ Odibets
- ✅ Betway
- ✅ 22Bet
- ✅ 1xBet
- ✅ International bookmakers (Bet365, etc.)

## Extracted Information

The OCR extracts the following data:

### Betslip Level
- **Bet Code**: Unique identifier for the bet
- **Total Odds**: Combined odds of all selections
- **Expiry Date**: When the tip expires
- **OCR Confidence**: Quality score of extraction (0-100%)

### Per Match
- **Home Team**: Home team name
- **Away Team**: Away team name
- **League**: Competition name
- **Market**: Type of bet (e.g., Over 2.5, 1X2, BTTS)
- **Selection**: Specific choice (e.g., Over, Home Win)
- **Odds**: Individual match odds
- **Match Date**: Scheduled match time

## Supported Betting Markets

### Goals
- Over/Under (0.5, 1.5, 2.5, 3.5, 4.5)
- Total Goals
- MultiGoal

### Match Result
- 1X2 (Home/Draw/Away)
- Double Chance (1X, X2, 12)
- Full Time Result

### BTTS (Both Teams to Score)
- GG (Both Teams Score)
- NG (No Goals from both)
- Yes/No

### Other Markets
- Correct Score
- Half Time Result
- HT/FT
- Asian Handicap
- Clean Sheet
- First/Last Goal

## Supported Leagues

### English Football
- Premier League (EPL)
- Championship
- FA Cup, EFL Cup

### European Leagues
- La Liga (Spain)
- Serie A (Italy)
- Bundesliga (Germany)
- Ligue 1 (France)

### Kenyan & East African
- Kenya Premier League (KPL)
- FKF Premier League
- FKF Cup
- Tanzania Premier League
- Uganda Premier League

### International
- UEFA Champions League
- UEFA Europa League
- World Cup
- AFCON
- And more...

## Troubleshooting

### Error: "Invalid credentials"
- Check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env
- Ensure credentials are from the textract-user IAM user
- Verify the IAM user has Textract permissions

### Error: "Failed to extract text"
- Ensure image is clear and well-lit
- Image should be under 5MB
- Supported formats: JPG, JPEG, PNG
- Try taking screenshot directly from bookmaker app

### Low Confidence Score
- Use high-resolution images
- Ensure betslip text is readable
- Avoid blurry or dark images
- Make sure all text is visible (no cropping)

### Missing Matches
- Verify betslip format is supported
- Check if team names contain special characters
- Try manually adjusting extracted data in verification step
- Report issues for unsupported formats

## Best Practices

### For Betslip Screenshots
1. **Clear and Bright**: Ensure good lighting
2. **Full Screenshot**: Include all matches and bet details
3. **High Resolution**: Use device's native screenshot
4. **No Cropping**: Show entire betslip including bet code

### For Testing
1. Test with various bookmakers
2. Try different match counts (1-10+ matches)
3. Test different betting markets
4. Verify accuracy of extracted data

### For Production
1. Always verify OCR extracted data
2. Allow tipsters to edit any incorrect information
3. Monitor OCR confidence scores
4. Collect feedback on extraction accuracy

## Logging

Enable debug logging to see detailed OCR processing:

```python
# In settings
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.tips.ocr': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Cost Optimization

AWS Textract pricing (as of 2024):
- First 1M pages/month: $1.50 per 1,000 pages
- Over 1M pages/month: $0.60 per 1,000 pages

**Estimated costs for Ligisoo**:
- 100 tips/day = ~3,000 tips/month = ~$4.50/month
- 500 tips/day = ~15,000 tips/month = ~$22.50/month
- 1,000 tips/day = ~30,000 tips/month = ~$45/month

## Support

If you encounter issues:
1. Check the logs: `python manage.py test_ocr image.jpg --debug`
2. Verify AWS credentials are correct
3. Ensure IAM permissions are properly configured
4. Test with different betslip images

## Next Steps

1. ✅ Add AWS credentials to .env
2. ✅ Test with sample betslip: `python manage.py test_ocr betslip.jpg`
3. ✅ Create a tip through web interface
4. ✅ Monitor OCR accuracy and confidence scores
5. ✅ Adjust extraction patterns if needed

## Additional Resources

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
