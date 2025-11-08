# Enabling New Bookmakers

This guide explains how to enable additional bookmakers beyond SportPesa when you're ready to expand.

## Current Status (MVP1)

**Available**: SportPesa only
**Coming Soon**: Betika, Odibets, Mozzart, Betin, and others

---

## How to Enable New Bookmakers

### Step 1: Update Form Choices

Open `/home/walter/marketplace/apps/tips/forms.py` and uncomment the bookmakers you want to enable:

#### In `TipSubmissionForm` (Create Tip form):
```python
AVAILABLE_BOOKMAKERS = [
    ('sportpesa', 'SportPesa'),
    ('betika', 'Betika'),      # Uncomment to enable
    ('odibets', 'Odibets'),    # Uncomment to enable
    ('mozzart', 'Mozzart'),    # Uncomment to enable
    ('betin', 'Betin'),        # Uncomment to enable
    ('other', 'Other'),        # Uncomment to enable
]
```

#### In `TipSearchForm` (Marketplace filter):
```python
AVAILABLE_BOOKMAKERS = [
    ('sportpesa', 'SportPesa'),
    ('betika', 'Betika'),      # Uncomment to enable
    ('odibets', 'Odibets'),    # Uncomment to enable
    ('mozzart', 'Mozzart'),    # Uncomment to enable
    ('betin', 'Betin'),        # Uncomment to enable
    ('other', 'Other'),        # Uncomment to enable
]
```

### Step 2: Implement OCR/Processing for the Bookmaker

You'll need to add processing logic for the new bookmaker:

1. **For Screenshot OCR** (Betika, Odibets, Mozzart, etc.):
   - Update `/home/walter/marketplace/apps/tips/ocr.py`
   - Train/configure OCR to recognize the new bookmaker's betslip format
   - Test with sample betslips

2. **For Link Scraping** (if bookmaker supports sharing links):
   - Add scraper method in OCR module
   - Update form validation to accept the bookmaker's link format
   - Add link validation logic

### Step 3: Update UI Notices

Remove or update the MVP notices:

1. **Homepage** (`templates/home.html` - line 69-102):
   - Remove the "Launching with SportPesa" banner
   - OR update to reflect newly available bookmakers

2. **Create Tip Page** (`templates/tips/create_tip.html` - line 17-39):
   - Remove the MVP notice
   - OR update text to show which bookmakers are now live

3. **Marketplace** (`templates/tips/marketplace.html` - line 11-24):
   - Remove the "Currently showing SportPesa tips" notice
   - OR update to say "Now supporting multiple bookmakers"

### Step 4: Test Thoroughly

Before going live:

✅ Create test tips with the new bookmaker
✅ Verify OCR/scraping extracts data correctly
✅ Check marketplace filtering works
✅ Verify purchase flow
✅ Test tip detail pages
✅ Ensure result verification works

---

## Quick Enable Checklist

When you're ready to enable a new bookmaker (e.g., Betika):

- [ ] Uncomment in `TipSubmissionForm.AVAILABLE_BOOKMAKERS`
- [ ] Uncomment in `TipSearchForm.AVAILABLE_BOOKMAKERS`
- [ ] Implement/test OCR processing for Betika betslips
- [ ] Update form validation (if using sharing links)
- [ ] Update UI notices to reflect Betika is available
- [ ] Test create → verify → publish → purchase flow
- [ ] Deploy changes

---

## Example: Enabling Betika

```python
# In apps/tips/forms.py

class TipSubmissionForm(forms.ModelForm):
    AVAILABLE_BOOKMAKERS = [
        ('sportpesa', 'SportPesa'),
        ('betika', 'Betika'),      # ✅ NOW ENABLED
    ]
```

```python
class TipSearchForm(forms.Form):
    AVAILABLE_BOOKMAKERS = [
        ('sportpesa', 'SportPesa'),
        ('betika', 'Betika'),      # ✅ NOW ENABLED
    ]
```

Then remove/update the MVP notices in templates.

---

## Notes

- **Database**: The model already supports all bookmakers in `Tip.BOOKMAKER_CHOICES`. You're just controlling what's shown in forms.
- **Existing Tips**: Old tips from other bookmakers (if any) will still work - you're only limiting new tip creation.
- **Gradual Rollout**: You can enable bookmakers one at a time, testing each thoroughly before enabling the next.

---

**Last Updated**: November 2024
**Version**: MVP1 (SportPesa Only)
