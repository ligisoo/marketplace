# OCR Extraction Improvements Summary

## Overview
Enhanced the Textract OCR extraction to accurately parse betting slips in the "Your Pick" format commonly used by Kenyan bookmakers.

## Changes Made

### 1. Match Extraction Logic (apps/tips/ocr.py:221-301)

**Problem:**
- OCR was picking up non-match text that happened to have separators
- Matches weren't being validated before adding to results
- False positives like "Number of Goals in Groups – Full Time"

**Solution:**
- Added validation: Only accepts matches that have BOTH "Your Pick:" and odds
- Implemented `found_pick` and `found_odds` flags to validate matches
- Skips potential matches that don't have both required components
- Logs skipped matches for debugging

**Key Features:**
- Looks ahead up to 6 lines after team names to find pick and odds
- Validates odds are in range (1.01 to 999.99)
- Sets default market to "3 Way" if not detected

### 2. Team Name Extraction (apps/tips/ocr.py:303-342)

**Enhancement:**
- Added support for Unicode separators: em dash (–), en dash (—), and hyphen (-)
- Pattern: `r'(.+?)\s+[\u2013\u2014\-]\s+(.+)'`
- Properly handles team names like "PSV Eindhoven – Fortuna Sittard"

### 3. Pick Extraction

**Pattern Added:**
```python
r'Your\s+Pick[:\s]+(Home|Away|Draw|Over|Under|Yes|No|1|X|2|1X|X2|12|GG|NG)'
```

**Supports:**
- "Your Pick: Home"
- "Your Pick: Away"
- "Your Pick: Draw"
- And other common betting selections

### 4. Total Odds Extraction (apps/tips/ocr.py:175-196)

**Improvements:**
- Better pattern matching for "Total Odds: 12.93"
- Validates odds range (1.01 to 9999.99)
- Handles comma separators

### 5. Possible Win Extraction (apps/tips/ocr.py:198-216)

**New Feature:**
- Extracts "Possible Win KSH 1,329.41"
- Patterns support with/without "KSH" prefix
- Parses comma-separated amounts
- Stored in betslip data for future use

### 6. Parse Results (apps/tips/ocr.py:110-138)

**Added to output:**
- `possible_win`: The potential winning amount
- Enhanced logging showing all extracted values

### 7. Debugging (apps/tips/views.py:183-203)

**Added logging in verify_tip view:**
- Logs OCR data structure
- Shows number of matches found
- Displays each match's details
- Helps diagnose extraction issues

## Example Output

### Input Betslip Text:
```
PSV Eindhoven – Fortuna Sittard
×
3 Way
Your Pick: Home
1.13
```

### Extracted Match Data:
```python
{
  'home_team': 'PSV Eindhoven',
  'away_team': 'Fortuna Sittard',
  'market': '3 Way',
  'selection': 'Home',
  'odds': 1.13,
  'league': 'Unknown League',
  'match_date': '2025-11-01T18:48:12Z'
}
```

### Full Betslip Data:
```python
{
  'bet_code': None,  # To be entered manually if not detected
  'total_odds': 12.93,
  'possible_win': 1329.41,
  'confidence': 98.32,
  'matches': [ ... 6 matches ... ]
}
```

## Testing

Tested with 6-match betslip:
- ✅ All 6 matches extracted correctly
- ✅ All picks (Home/Away) correct
- ✅ All odds accurate (1.13, 1.62, 2.19, 1.11, 2.55, 1.14)
- ✅ Total odds: 12.93
- ✅ Possible win: KSH 1,329.41

## Validation Rules

1. **Team Names:** Must be 3-50 characters each
2. **Odds:** Must be between 1.01 and 999.99
3. **Match Validation:** Must have both "Your Pick" and odds within 6 lines
4. **Total Odds:** Must be between 1.01 and 9999.99

## What to Monitor

When users upload betslips, check the Django logs for:
- `=== VERIFY TIP DEBUG ===` - Shows extracted OCR data
- `Skipping potential match` - Shows false positives being filtered
- `Parsed results` - Shows extraction summary

## Known Limitations

1. **Bet Code:** May not always detect bet codes - users need to enter manually
2. **League Detection:** Defaults to "Unknown League" if not recognized
3. **Match Date:** Defaults to tomorrow - users should adjust

## Recommendations

1. Monitor logs for skipped matches to tune validation
2. Consider adding more market patterns as needed
3. Add bet code patterns for more bookmakers
4. Implement proper date/time parsing in future

## Files Modified

- `apps/tips/ocr.py` - Core extraction logic
- `apps/tips/views.py` - Added debugging logs
- All changes are backward compatible
