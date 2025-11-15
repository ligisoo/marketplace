# Tipster User Flow - How to Submit Tips

## Overview

Tipsters can now submit tips using **two different methods** depending on which OCR provider is active:

1. **Screenshot Upload** (Textract/EasyOCR)
2. **Bet Sharing Link** (SportPesa Scraper)

The form **automatically adapts** based on the admin's OCR provider selection.

---

## Method 1: Screenshot Upload (Textract/EasyOCR)

### When Active:
- Admin has selected "AWS Textract" or "EasyOCR" in OCR Provider Settings

### User Flow:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Tipster Goes to "Create Tip" Page                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Form Shows Screenshot Upload Field                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Bookmaker:    [Select: Betika/SportPesa/etc]           │ │
│  │  Price (KES):  [50]                                       │ │
│  │  Screenshot:   [📷 Upload betslip image]                 │ │
│  │                                                            │ │
│  │  [Upload & Create Tip]                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Tipster Takes Screenshot of Betslip                    │
│  - Opens betting app (Betika/SportPesa/etc)                    │
│  - Takes screenshot of betslip                                  │
│  - Uploads screenshot file                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: System Processes with OCR                              │
│  - Extracts text from image                                    │
│  - Identifies: bet code, odds, teams, markets                  │
│  - Processing time: 2-3 seconds                                │
│  - Confidence: 70-90%                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Verification Page (Manual Check)                       │
│  - Review extracted data                                       │
│  - Fix any OCR errors                                          │
│  - Enter match dates manually                                  │
│  - Submit tip                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Tip Published to Marketplace ✓                         │
└─────────────────────────────────────────────────────────────────┘
```

### What Tipster Sees:

**Form Title:**
> "Create New Tip"
> "Upload your betslip screenshot to share your winning insights"

**Screenshot Field:**
```
┌────────────────────────────────────────────────┐
│           📷 Upload Betslip Screenshot         │
│                                                │
│   Drag and drop your betslip image here,      │
│        or click to browse                      │
│                                                │
│          JPG, PNG up to 5MB                    │
└────────────────────────────────────────────────┘
```

**Guidelines:**
- ✓ Ensure your betslip screenshot is clear and readable
- ✓ Make sure the bet code, odds, and match details are visible
- ✓ Only upload betslips that haven't been played yet

**Button:**
`[📤 Upload & Create Tip]`

---

## Method 2: Bet Sharing Link (SportPesa Scraper)

### When Active:
- Admin has selected "SportPesa Scraper" in OCR Provider Settings

### User Flow:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Tipster Goes to "Create Tip" Page                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Form Shows Bet Sharing Link Field                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Bookmaker:         [Select: SportPesa]                   │ │
│  │  Price (KES):       [50]                                  │ │
│  │  Bet Sharing Link:  [🔗 Paste SportPesa link]            │ │
│  │                                                            │ │
│  │  [Process Link & Create Tip]                              │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Tipster Gets Sharing Link from SportPesa               │
│  1. Opens SportPesa app/website                                │
│  2. Places bet and views betslip                               │
│  3. Clicks "Share" or "Referral" button                        │
│  4. Copies the sharing link                                    │
│     Format: https://www.ke.sportpesa.com/referral/XXXXX        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Pastes Link in Form                                    │
│  - Pastes link into "Bet Sharing Link" field                   │
│  - Example: https://www.ke.sportpesa.com/referral/MPCPYA       │
│  - Submits form                                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: System Scrapes SportPesa                               │
│  - Launches headless browser                                   │
│  - Navigates to referral link                                  │
│  - Scrapes: teams, markets, picks, odds                        │
│  - Processing time: 5-10 seconds                               │
│  - Confidence: 95%                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Verification Page (Manual Check)                       │
│  - Review scraped data                                         │
│  - Data is highly accurate (95% confidence)                    │
│  - Enter match dates manually (not in referral link)           │
│  - Submit tip                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Tip Published to Marketplace ✓                         │
└─────────────────────────────────────────────────────────────────┘
```

### What Tipster Sees:

**Form Title:**
> "Create New Tip"
> "Share your SportPesa bet using the referral link"

**Bet Sharing Link Field:**
```
┌────────────────────────────────────────────────┐
│        🔗 Paste Your Bet Sharing Link          │
│                                                │
│   Copy the referral link from your SportPesa   │
│           bet and paste it below               │
│                                                │
│  [https://www.ke.sportpesa.com/referral/...]  │
└────────────────────────────────────────────────┘

📋 How to get your sharing link:
1. Place your bet on SportPesa
2. Open your betslip
3. Click the "Share" or "Referral" button
4. Copy the link and paste it here
```

**Guidelines:**
- ✓ Ensure your betting link is a valid SportPesa referral URL
- ✓ The link must contain your active bets (not an empty betslip)
- ✓ Only share betslips that haven't been played yet

**Button:**
`[🔗 Process Link & Create Tip]`

---

## Side-by-Side Comparison

| Feature | Screenshot Upload | Bet Sharing Link |
|---------|------------------|------------------|
| **OCR Provider** | Textract/EasyOCR | SportPesa Scraper |
| **Input Method** | Upload image file | Paste URL |
| **Bookmakers** | All (Betika, SportPesa, Mozzart, etc.) | SportPesa only |
| **Processing Time** | 2-3 seconds | 5-10 seconds |
| **Accuracy** | 70-90% | 95% |
| **Match Dates** | Sometimes extracted | Not available (manual entry) |
| **Internet Required** | No (for upload) | Yes (for scraping) |
| **File Size Limit** | 5MB max | N/A |
| **User Effort** | Take screenshot → Upload | Copy link → Paste |

---

## Admin Control

### Switching Between Methods:

**Django Admin > Tips > OCR Provider Settings**

```
┌─────────────────────────────────────────────────┐
│ OCR Provider Setting                            │
│                                                 │
│ Provider: [▼ SportPesa Scraper]                │
│                                                 │
│ Options:                                        │
│  • AWS Textract     (Screenshot → OCR)          │
│  • EasyOCR          (Screenshot → OCR)          │
│  • SportPesa Scraper (Link → Scrape)           │
│                                                 │
│ Updated: 2025-11-07 18:30:00                    │
│                                                 │
│ [Save]                                          │
└─────────────────────────────────────────────────┘
```

**Effect:**
- Immediately changes the form for all tipsters
- Form automatically shows correct input field
- Validation rules adjust accordingly

---

## Form Validation Rules

### When SportPesa Scraper is Active:

✅ **Valid Submission:**
```json
{
  "bookmaker": "sportpesa",
  "price": 50,
  "bet_sharing_link": "https://www.ke.sportpesa.com/referral/MPCPYA",
  "screenshot": null
}
```

❌ **Invalid - No Link:**
```
Error: "SportPesa scraper is active. Please provide a bet sharing link."
```

❌ **Invalid - Wrong URL:**
```
Error: "Please provide a valid SportPesa referral/sharing link"
```

❌ **Invalid - Both Provided:**
```
Error: "Please provide either a screenshot OR a bet sharing link, not both."
```

### When Textract/EasyOCR is Active:

✅ **Valid Submission:**
```json
{
  "bookmaker": "betika",
  "price": 50,
  "screenshot": "<image file>",
  "bet_sharing_link": null
}
```

❌ **Invalid - No Screenshot:**
```
Error: "TEXTRACT is active. Please upload a betslip screenshot."
```

❌ **Invalid - File Too Large:**
```
Error: "Image file too large (max 5MB)"
```

❌ **Invalid - Wrong File Type:**
```
Error: "File must be an image"
```

---

## Step-by-Step: How Tipster Gets SportPesa Sharing Link

### Mobile App (Recommended):

1. **Open SportPesa App**
   ```
   📱 SportPesa App → Login
   ```

2. **Place Your Bet**
   ```
   🏟️ Browse matches → Add to betslip → Place bet
   ```

3. **Open Betslip**
   ```
   📋 My Bets → Active Betslips → Select your betslip
   ```

4. **Find Share Button**
   ```
   🔗 Look for "Share", "Referral", or share icon (usually top-right)
   ```

5. **Copy Link**
   ```
   📎 Click share → Copy link
   Format: https://www.ke.sportpesa.com/referral/MPCPYA
   ```

6. **Paste in Ligisoo**
   ```
   🔗 Go to Ligisoo → Create Tip → Paste link
   ```

### Website:

1. **Go to SportPesa.com**
2. **Place bet**
3. **View betslip**
4. **Click "Share" or referral icon**
5. **Copy generated link**
6. **Paste in Ligisoo form**

---

## Verification Step (Same for Both Methods)

After processing (OCR or scraping), tipster reviews extracted data:

```
┌─────────────────────────────────────────────────────────────────┐
│ Verify Your Tip                                                 │
│                                                                 │
│ Bet Code: [MPCPYA]                                             │
│ Total Odds: [74.65]                                            │
│ Expires At: [2025-11-10 15:00]                                │
│                                                                 │
│ ──────────────────────────────────────────────────────────────  │
│ Match 1:                                                        │
│  Home Team:  [Elche]                                           │
│  Away Team:  [Real Sociedad]                                   │
│  Market:     [Asian Handicap - Full Time]                      │
│  Selection:  [Real Sociedad [+0.50]]                           │
│  Odds:       [1.40]                                            │
│  Match Date: [2025-11-08 20:00]  ← MANUAL ENTRY REQUIRED      │
│                                                                 │
│ ──────────────────────────────────────────────────────────────  │
│ Match 2:                                                        │
│  ... (similar fields)                                           │
│                                                                 │
│ [Submit Tip]  [Cancel]                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- ✓ All extracted data is shown
- ✓ User can edit any field
- ✓ Match dates must be entered manually (especially for SportPesa links)
- ✓ Validation ensures all required fields are filled

---

## Troubleshooting

### "No betslip found on this page"

**Cause:** SportPesa link doesn't contain any bets

**Solution:**
1. Ensure you placed the bet before copying the link
2. Verify the betslip is still active
3. Try copying the link again from SportPesa

### "Invalid SportPesa referral link"

**Cause:** Link format is incorrect

**Solution:**
- Link must start with: `https://www.ke.sportpesa.com/referral/`
- Example valid link: `https://www.ke.sportpesa.com/referral/MPCPYA`
- Do NOT use other SportPesa URLs (like match pages)

### "Please provide either a screenshot OR a bet sharing link"

**Cause:** Both fields filled or both empty

**Solution:**
- Only fill ONE field (screenshot OR link)
- Based on active OCR provider

### Form Shows Wrong Field

**Cause:** OCR provider setting doesn't match expectation

**Solution:**
- Check: Django Admin > Tips > OCR Provider Settings
- Ensure correct provider is selected
- Refresh the create tip page

---

## Summary

✅ **Tipsters can submit tips using two methods:**
1. Screenshot upload (for all bookmakers with Textract/EasyOCR)
2. Bet sharing link (for SportPesa with scraper)

✅ **Form automatically adapts** based on admin's OCR provider selection

✅ **Both methods lead to verification step** where tipster reviews/adjusts data

✅ **SportPesa scraper is faster and more accurate** but requires internet and only works for SportPesa

✅ **Screenshot method is universal** but may have OCR errors that need correction
