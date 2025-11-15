# Tip Approval Guide

## Current Situation

**Gladys's Status**:
- Phone: 0725771129
- Is Tipster: ✅ Yes
- Is Verified: ❌ **No** (Tips require approval)
- Pending Tips: 2
  - Bet Code: JYRCAV
  - Bet Code: TEMP_1761850388932105

**Admin Users**: ❌ None

## Understanding the Approval System

### How It Works

When a tipster creates a tip, the system checks their verification status:

```python
if user.userprofile.is_verified:
    tip.status = 'active'  # Goes live immediately ✅
else:
    tip.status = 'pending_approval'  # Requires admin approval ⏳
```

### Who Can Approve Tips?

1. **Django Admin Users** (staff/superuser)
2. **Automated** (for verified tipsters)

---

## Solution 1: Approve Gladys's Current Tips

### Quick Approval (Recommended)

```bash
python manage.py approve_gladys_tips
```

**What it does**:
- ✅ Approves all Gladys's pending tips
- ✅ Makes them visible on marketplace
- ✅ Buyers can purchase them immediately

### Expected Output:
```
=== Approving Gladys's Tips ===

Found Gladys: 0725771129

Found 2 pending tip(s):

  • Bet Code: JYRCAV
    Odds: 32.83
    Price: KES 50
    Created: 2025-10-30 19:04
    ✓ Approved!

  • Bet Code: TEMP_1761850388932105
    Odds: ...
    Price: KES ...
    Created: 2025-10-30 ...
    ✓ Approved!

✓ Successfully approved 2 tip(s)!
Tips are now live on the marketplace.
```

---

## Solution 2: Verify Gladys (Recommended for Long-term)

### Verify as Trusted Tipster

```bash
python manage.py verify_tipster Gladys
```

**What it does**:
- ✅ Marks Gladys as verified tipster
- ✅ Future tips go live **automatically**
- ✅ No more manual approvals needed
- ⚠️ Does NOT approve existing pending tips (use Solution 1 first)

### Expected Output:
```
Searching for tipster: Gladys...

✓ Found user: Gladys
  Phone: 0725771129
  Is Tipster: True
  Currently Verified: False

✓ Gladys is now a verified tipster!
  Future tips will go live automatically.
  Verified on: 2025-10-30 19:30

📊 Tip Statistics:
  Total Tips: 2
  Active: 0
  Pending: 2

⚠ Note: 2 tip(s) still pending approval
  Run: python manage.py approve_gladys_tips
```

### Unverify if Needed

```bash
python manage.py verify_tipster Gladys --unverify
```

---

## Solution 3: Create Admin User

### For Platform Management

```bash
python manage.py shell < create_admin.py
```

**Follow the prompts**:
1. Enter admin phone number
2. Enter username (optional)
3. Enter password

### Use Django Admin Interface

1. **Access Admin Panel**:
   ```
   http://localhost:8000/admin/
   ```

2. **Login** with admin credentials

3. **Navigate to Tips**:
   - Click "Tips" in sidebar

4. **Filter by Status**:
   - Select "Pending approval" from filter

5. **Approve Tips**:
   - Check boxes for tips to approve
   - Select "Approve selected tips" from Actions dropdown
   - Click "Go"

6. **Result**:
   - ✅ Tips move to 'active' status
   - ✅ Visible on marketplace
   - 📧 Notification sent to tipster (if configured)

---

## Complete Workflow (Recommended)

### Step 1: Approve Current Tips
```bash
python manage.py approve_gladys_tips
```

### Step 2: Verify Gladys for Future
```bash
python manage.py verify_tipster Gladys
```

### Step 3: Create Admin (Optional)
```bash
python manage.py shell < create_admin.py
```

---

## Verification Criteria

### When to Verify a Tipster

✅ **Verify if**:
- Tipster has good track record
- Tips have high accuracy
- Trusted community member
- Professional tipster

❌ **Don't verify if**:
- New tipster (< 5 tips)
- Low win rate
- Suspicious activity
- Spam/low quality tips

### Benefits of Verification

**For Tipster**:
- ✅ Tips go live instantly
- ✅ No approval delays
- ✅ Verified badge (if implemented)
- ✅ Higher trust from buyers

**For Platform**:
- ✅ Faster tip availability
- ✅ Better user experience
- ✅ Less admin workload

---

## Monitoring & Management

### Check Pending Tips

```bash
python manage.py shell -c "
from apps.tips.models import Tip
pending = Tip.objects.filter(status='pending_approval')
print(f'Pending tips: {pending.count()}')
for tip in pending:
    print(f'  {tip.bet_code} - {tip.tipster.username} - {tip.created_at}')
"
```

### List All Tipsters

```bash
python manage.py shell -c "
from apps.users.models import User
tipsters = User.objects.filter(userprofile__is_tipster=True)
print('Tipsters:')
for t in tipsters:
    v = '✓' if t.userprofile.is_verified else '✗'
    print(f'  {v} {t.username or t.phone_number} (verified: {t.userprofile.is_verified})')
"
```

### Bulk Approve All Pending

```bash
python manage.py shell -c "
from apps.tips.models import Tip
count = Tip.objects.filter(status='pending_approval').update(status='active')
print(f'Approved {count} tips')
"
```

---

## Automation Ideas

### Auto-Verify Based on Performance

Create a cron job or scheduled task:

```python
# apps/tips/management/commands/auto_verify_tipsters.py
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.tips.models import Tip

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Find tipsters with good track record
        tipsters = User.objects.filter(userprofile__is_tipster=True, userprofile__is_verified=False)

        for tipster in tipsters:
            tips = Tip.objects.filter(tipster=tipster, is_resulted=True)
            if tips.count() >= 5:  # At least 5 tips
                won = tips.filter(is_won=True).count()
                win_rate = (won / tips.count()) * 100

                if win_rate >= 70:  # 70% win rate
                    tipster.userprofile.is_verified = True
                    tipster.userprofile.save()
                    print(f'✓ Auto-verified {tipster.username} (win rate: {win_rate}%)')
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python manage.py approve_gladys_tips` | Approve Gladys's pending tips |
| `python manage.py verify_tipster Gladys` | Verify Gladys as trusted tipster |
| `python manage.py verify_tipster Gladys --unverify` | Remove verification |
| `python manage.py createsuperuser` | Create admin user (alternative) |
| Access `/admin/` | Django admin interface |

---

## Next Steps

1. ✅ **Immediate**: Approve Gladys's tips
   ```bash
   python manage.py approve_gladys_tips
   ```

2. ✅ **Short-term**: Verify Gladys
   ```bash
   python manage.py verify_tipster Gladys
   ```

3. ✅ **Long-term**: Create admin account
   ```bash
   python manage.py shell < create_admin.py
   ```

4. ✅ **Monitor**: Check pending tips regularly
   ```bash
   http://localhost:8000/admin/tips/tip/?status__exact=pending_approval
   ```

---

## Support

If you encounter issues:
- Check logs: `python manage.py shell -c "from apps.tips.models import Tip; print(Tip.objects.filter(status='pending_approval').count())"`
- Verify database: Tips should have `status='active'` to be visible
- Check marketplace: Tips should appear after approval
