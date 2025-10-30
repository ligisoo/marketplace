# 🚨 URGENT: Rotate Your AWS Credentials

## ⚠️ Why You Need to Rotate

Your AWS credentials were shared in this conversation, which means they are **publicly exposed** and could be compromised. Anyone who saw these credentials could:
- Use your AWS Textract service (incur charges)
- Access other AWS resources if permissions expand
- Potentially cause security issues

## ✅ Current Status

**GOOD NEWS**:
- ✓ Credentials are working and configured
- ✓ .env file is in .gitignore (won't be committed to git)
- ✓ You can use the OCR functionality now

**ACTION REQUIRED**:
- ⚠️ Rotate these credentials within the next 24 hours
- ⚠️ Delete the exposed access key

## 📋 How to Rotate AWS Credentials (Step-by-Step)

### Step 1: Create New Access Key (DO THIS FIRST)

1. Go to AWS IAM Console:
   https://us-east-1.console.aws.amazon.com/iam/home?region=af-south-1#/users/details/textract-user?section=security_credentials

2. Under "Access keys" section, click **"Create access key"**

3. Select use case: **"Application running outside AWS"**

4. Click **"Next"** → **"Create access key"**

5. **IMMEDIATELY SAVE** both credentials:
   - Access key ID
   - Secret access key

6. Click **"Download .csv file"** (backup)

### Step 2: Update Your .env File

Replace the old credentials with new ones:

```bash
# Edit .env file
nano .env
```

Update these lines:
```env
AWS_ACCESS_KEY_ID=YOUR_NEW_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_NEW_SECRET_ACCESS_KEY
AWS_REGION_NAME=us-east-1
```

### Step 3: Test New Credentials

```bash
python test_aws_connection.py
```

You should see:
```
✓ AWS Textract client created successfully!
✓ Credentials are valid and loaded correctly!
```

### Step 4: Delete Old Access Key

**IMPORTANT**: Only do this AFTER confirming new credentials work!

1. Go back to IAM Console (same link as Step 1)

2. Find the OLD access key: **AKIA47CRYLMGROYNFL5L**

3. Click **"Actions"** → **"Delete"**

4. Confirm deletion

5. Verify only the new key is listed

### Step 5: Test Application

```bash
# Test OCR with a betslip image
python manage.py test_ocr /path/to/betslip.jpg

# Or start the server and test through web interface
python manage.py runserver
```

## 🔐 Security Best Practices Going Forward

### DO:
✅ Keep credentials in .env file only
✅ Never share credentials in chat, email, or commits
✅ Rotate credentials every 90 days
✅ Use IAM roles when deploying to AWS
✅ Monitor AWS CloudTrail for unusual activity
✅ Set up AWS billing alerts

### DON'T:
❌ Share credentials in conversations
❌ Commit .env to git
❌ Email credentials
❌ Screenshot credentials
❌ Use credentials in code directly
❌ Share credentials across multiple projects

## 📊 Monitoring Your Usage

### Check AWS Costs
1. Go to: https://console.aws.amazon.com/billing/
2. Check "Bills" section for Textract charges
3. Expected costs: ~$1.50 per 1,000 betslips processed

### Set Up Billing Alert
1. Go to: https://console.aws.amazon.com/billing/home#/budgets
2. Create budget: "Monthly Textract Budget"
3. Set amount: $50 (or your preference)
4. Add email alert

## 🆘 If You Suspect Compromise

If you see unexpected charges or activity:

1. **Immediately disable the access key**:
   - IAM Console → textract-user → Security credentials
   - Click "Actions" → "Deactivate" on the key

2. **Check CloudTrail logs**:
   - https://console.aws.amazon.com/cloudtrail/
   - Look for unusual API calls

3. **Contact AWS Support**:
   - https://console.aws.amazon.com/support/

4. **Create new credentials** and update .env

## ✅ Checklist

After rotating, verify:

- [ ] New access key created
- [ ] New credentials added to .env
- [ ] New credentials tested and working
- [ ] Old access key **AKIA47CRYLMGROYNFL5L** deleted
- [ ] Application still works with new credentials
- [ ] This file deleted (or credentials redacted)

## 📞 Questions?

If you have issues:
1. Check the OCR_SETUP.md documentation
2. Test with: `python test_aws_connection.py`
3. Verify IAM permissions are correct
4. Check AWS service health dashboard

---

**Timeline**: Complete rotation within 24 hours for security.

**Priority**: HIGH - These credentials are exposed and should be rotated ASAP.
