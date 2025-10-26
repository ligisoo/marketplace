# Tips Marketplace - Complete Planning Document

> **Total Pages:** 100+  
> **Status:** Planning Complete - Ready for Development  
> **Timeline:** 15-16 weeks (4 months)  
> **Investment:** KES 1.8M - 2.0M

---

## Table of Contents

1. [Information Reveal Strategy](#1-information-reveal-strategy)
2. [Core Features](#2-core-features)
3. [User Flows](#3-user-flows)
4. [Database Schema](#4-database-schema)
5. [Technical Stack](#5-technical-stack)
6. [Trust & Verification System](#6-trust--verification-system)
7. [Payment & Monetization](#7-payment--monetization)
8. [Legal & Compliance](#8-legal--compliance)
9. [MVP Scope & Timeline](#9-mvp-scope--timeline)
10. [Next Steps](#10-next-steps)

---

## 1. Information Reveal Strategy

### Option 1: Partial Match Information (SELECTED)

**Before Purchase (Public Preview):**
```
🎯 5-Match Accumulator
📊 Total Odds: 47.35
💰 Potential Payout: KES 4,735 (on KES 100 stake)
⚽ Sport: Football
🏆 League Mix: EPL, La Liga, Serie A
📅 Matches start: Today 7:00 PM

Preview:
• Man United vs ______ (Market: Hidden)
• ______ vs Liverpool (Market: Hidden)  
• 3 more matches (Hidden)

✅ Tipster Win Rate: 68%
✅ Last 10 Tips: 7 Won, 3 Lost
```

**After Purchase (Full Reveal):**
```
✅ BET CODE: RSCEHO
✅ Bookmaker: SportPesa Kenya

Full Ticket Details:
1. Man United vs Chelsea - Over 2.5 Goals @ 1.85
2. Barcelona vs Real Madrid - BTTS Yes @ 1.75
3. Bayern vs Dortmund - Home Win @ 1.45
4. Inter vs Juventus - Under 3.5 @ 1.60
5. Arsenal vs Spurs - Away Win @ 3.20

Total Odds: 47.35

Instructions:
1. Open SportPesa
2. Tap "Load Betslip"  
3. Enter code: RSCEHO
4. Verify matches and odds
5. Place your bet
```

**Why This Works:**
- Prevents free-riding (market selections hidden)
- Builds trust (shows leagues, teams, odds)
- Creates urgency (shows match times)
- Protects tipster's "secret sauce"

---

## 2. Core Features

### MVP (Phase 1) - Launch Features ✅

#### 1. User Management
- Phone number + OTP registration
- User types: Buyer, Tipster, Admin
- Profile system with stats
- Avatar uploads

#### 2. Tip Discovery & Marketplace
- Live tips feed (grid view)
- Featured tips section
- "Ending Soon" section
- Filters: Sport, Odds range, Price, Bookmaker, Time
- Sort: Newest, Ending soon, Highest odds, Best tipster
- Search by tipster username

#### 3. Leaderboard System 🏆
**Three Tabs:**
- Top Performers (Win Rate)
- Top Earners (Revenue)
- Rising Stars (New Tipsters)

Updates: Real-time after results

#### 4. Rating & Trust System
Auto-calculated stats:
- Win Rate: 68% (Last 30 days)
- Total Tips: 156
- Won/Lost/Pending breakdown
- Average Odds: 5.5x
- ROI: +34%

Trust Badges:
- 🏆 Top Performer (70%+ win rate)
- ⚡ Quick Seller (50+ tips sold)
- 🔥 Hot Streak (10 consecutive wins)
- ⭐ Rising Star (New, 80%+ win rate)
- ✅ Verified Tipster (Admin approved)

#### 5. Transaction & Wallet System
**Buyer:**
- My Purchases dashboard
- Filter: Active, Archived, Won, Lost
- Copy bet code anytime
- Download watermarked screenshots

**Tipster:**
- Wallet balance (Available + Pending)
- Earnings history
- Withdrawal requests
- Transaction logs

#### 6. Notifications
- SMS (critical only): Payment, Withdrawal, Disputes
- In-app (HTMX real-time): Purchases, Approvals, Results
- Email (optional): Weekly summaries

#### 7. Admin Dashboard
- Overview metrics & charts
- Tip management (Approve/Reject/Feature)
- User management (Ban/Verify)
- Dispute management
- Financial reports
- Manual review queue
- Audit logs

#### 8. One-Way Communication
- Tipsters add notes to tips (200 chars)
- Admin announcements
- Buyers contact support only

---

### Phase 2 Features (Post-Launch) 🚀

- Follow system
- Buyer reviews (5-star ratings)
- ROI calculation display
- Advanced analytics graphs
- Direct messaging
- Tip packages/bundles
- Premium features

---

## 3. User Flows

### A. Tipster Submission Flow ✅

**Step 1: Quick Submit (4 Fields)**
1. Paste Bet Code: RSCEHO
2. Select Bookmaker: SportPesa
3. Upload Screenshot: [Image]
4. Set Price: KES 200 (or 0 for free)

**Step 2: OCR Processing (Automatic)**
- AWS Textract extracts text
- Parse: bet code, odds, matches
- Store in match_details JSON

**Step 3: Tipster Verification**
```
Review Extracted Info:
✓ Bet Code: RSCEHO
✓ Total Odds: 47.35
✓ Selections: 5
✓ Sport: Football

Match 1: Man United vs Chelsea
Select Market: [Over 2.5 Goals ▼]

Match 2: Barcelona vs Real Madrid
Select Market: [BTTS Yes ▼]

[Confirm & Submit]
```

**Step 4: Approval**
- New Tipsters: Admin approval queue
- Verified Tipsters: Auto-publish

**Step 5: Live**
- Visible on marketplace
- Buyers can purchase

---

### B. Buyer Purchase Flow ✅

**Step 1: Browse Marketplace**
- Apply filters
- View tip previews
- Check tipster stats

**Step 2: View Tip Details**
- Partial match info
- Tipster performance
- Price & countdown

**Step 3: Payment (M-Pesa)**
1. Click "Purchase"
2. Enter M-Pesa number
3. Receive STK push
4. Enter PIN
5. Instant confirmation

**Step 4: Access Bet Code**
```
Purchase Successful! ✅

BET CODE: RSCEHO
Bookmaker: SportPesa

[Copy Code] button

Full Match Details:
1. Man United vs Chelsea - Over 2.5 @ 1.85
2. ...

[Download Screenshot]
```

**Step 5: Saved in "My Purchases"**
- Access anytime
- Track results

**Step 6: Auto-Archive**
- When last match starts
- No longer purchasable
- Buyers retain access

---

## 4. Database Schema

### 13 Core Tables

**1. users** - User accounts (UUID, phone, username, user_type, wallet_balance)

**2. tips** - Betting tips (bet_code, bookmaker, odds, price, screenshot, match_details JSON, preview_data JSON, status, result_status)

**3. transactions** - Purchases (buyer, tip, tipster, amount, mpesa_receipt, payment_status, escrow_status, platform_fee 40%, tipster_earning 60%)

**4. withdrawals** - Payouts (tipster, amount, mpesa_phone, status, approved_by)

**5. disputes** - Refunds (transaction, issue_type, status, refund_amount)

**6. notifications** - Alerts (user, type, title, message, is_read, sent_via_sms)

**7. tipster_stats** - Performance (tipster, total_tips, tips_won/lost, win_rate, avg_odds, total_sold, revenue, streaks, rankings)

**8. badges** - Achievements (code, name, description, criteria JSON)

**9. user_badges** - Awards (user, badge, awarded_at)

**10. tip_views** - Analytics (tip, user, viewed_at)

**11. manual_review_queue** - Flagged tips (tip, reason, status)

**12. platform_settings** - Config (setting_key, setting_value)

**13. admin_audit_log** - Actions (admin, action_type, entity_type/id)

### Key Relationships
```
Users (1) → (Many) Tips
Users (1) → (Many) Transactions
Tips (1) → (Many) Transactions
Transactions (1) → (0..1) Disputes
Users (1) → (Many) Withdrawals
Users (1) → (Many) Notifications
```

---

## 5. Technical Stack

### Backend
- **Django 5.0** - Python web framework
- **PostgreSQL** - Production database
- **SQLite** - Development

### Frontend
- **Django Templates** - Server-side rendering
- **HTMX** - Real-time updates
- **Tailwind CSS** - Styling

### Infrastructure
- **AWS EC2** - Hosting
- **AWS S3** - File storage
- **AWS Textract** - OCR
- **Nginx** - Web server
- **Gunicorn** - WSGI server
- **Systemd** - Process management

### Integrations
- **M-Pesa Daraja API** - Payments & withdrawals
- **API-Football** - Match results (~$30-50/month)
- **SMS Gateway** - Notifications

### Background Jobs
- **schedule** - Python cron library

### Packages
```
Django==5.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-decouple==3.8
Pillow==10.1.0
boto3==1.34.0
schedule==1.2.2
fuzzywuzzy==0.18.0
requests==2.31.0
django-htmx==1.17.0
```

---

## 6. Trust & Verification System

### Result Verification (PRIMARY - MVP)

**Automated via API-Football:**
```python
# Every 30 minutes cron job
1. Query pending tips (last_match + 2 hours passed)
2. For each tip, get match results from API
3. Compare with tip selections
4. Mark as won/lost/void
5. Update tipster stats
6. Send notifications
```

**Manual Review (Fallback):**
- API can't find match
- Market not recognized
- Admin marks manually

### Win Rate Calculation

**Formula:**
```
Win Rate = (Won Tips / Total Resulted Tips) × 100

Minimum: 10 resulted tips
Time periods: 7, 30, 90 days, All time
```

**Example:**
- 68 won, 27 lost, 5 pending
- Win Rate = 68 / (68 + 27) × 100 = 71.58%

### Badge System

**🏆 Top Performer**
- Win rate ≥ 70%
- Min 30 tips (30 days)
- Active (posted in 7 days)

**⚡ Quick Seller**
- 50+ tips sold (all time)
- Never revoked

**🔥 Hot Streak**
- 10 consecutive wins
- Revoked on loss

**⭐ Rising Star**
- Account < 30 days
- Win rate ≥ 80%
- Min 10 tips

**✅ Verified Tipster**
- Admin awarded
- Auto-publish enabled
- Higher visibility

### Anti-Fraud Measures

**Screenshot Verification:**
- Valid image file
- Reasonable dimensions
- Admin review (new users)
- Phase 2: Image forensics

**Code Verification:**
- Test in actual bookmaker
- Verify odds match
- Check selections count

**Multi-Account Detection:**
- Track IP, device, phone, M-Pesa
- Flag coordinated activity

**New Account Restrictions:**
- Manual approval first 10 tips
- Max 3 tips/day initially
- Phone verification required
- Can't withdraw until 10 sold

---

## 7. Payment & Monetization

### Revenue Split: 60/40

**Example (KES 200 tip):**
```
Buyer pays: KES 200
M-Pesa fee: KES 3 (Platform absorbs)
Net: KES 197

Split:
- Tipster: KES 118 (60%)
- Platform: KES 79 (40%)
```

**Free Tips:**
- No transaction
- Builds reputation
- Platform benefits from growth

### Payout System

**Escrow: 48 Hours**
```
Purchase → Hold 48hrs → Auto-release

Timeline:
- After last match + 48 hours
- Ensures bet code worked
- Auto-transfer to wallet
```

**Minimum Threshold:**
- Default: KES 500 (adjustable)
- Batch smaller amounts
- Reduce transaction fees

**Withdrawal Process:**
1. Tipster requests (≥ KES 500)
2. Admin approves (or auto for trusted)
3. M-Pesa B2C transfer
4. Confirmation sent

### Refund Policy

**Full Refund (100%):**
- Invalid/expired bet code
- Wrong matches loaded
- Odds differ >20%
- Platform error

**Partial Refund (80% buyer, 20% platform):**
- Minor discrepancies (odds <20%)
- One match already started
- Incorrect selection count

**No Refund:**
- Code works but bet loses
- Buyer changes mind
- Matches already started

### Dispute Process

**Window:**
- 30 minutes after purchase
- OR until first match starts

**Process:**
1. Buyer reports issue
2. Select type + upload proof
3. Admin reviews
4. Decision within 2 hours
5. Auto-refund if approved

**Tipster Accountability:**
- Invalid code → Suspension
- 3 invalid codes → Ban
- Rating drops on disputes
- Funds held until resolved

### Future Revenue (Phase 2)

1. **Featured Listings** - KES 200-500 for 24hr top placement
2. **Verified Badge** - KES 500/month subscription
3. **Premium Tiers** - Better revenue splits
4. **Bookmaker Affiliates** - Commission on signups
5. **Advertising** - Banner ads from bookmakers

---

## 8. Legal & Compliance

### Kenya Requirements

**Business Registration:**
- Register company/business
- KRA tax registration
- Business bank account

**Betting Control & Licensing Board (BCLB):**
- Consult for tips marketplace status
- Age verification (18+)
- Responsible gambling notices

**Required Documents:**
1. **Terms of Service** - User responsibilities, refunds, liability
2. **Privacy Policy** - Data collection, usage, sharing, rights
3. **Responsible Gambling** - Age restrictions, self-exclusion, resources

**Tax Compliance:**
- Platform revenue taxes
- Issue statements to tipsters
- Tipsters handle own taxes

---

## 9. MVP Scope & Timeline

### What's IN (MVP - Phase 1)

✅ User registration (phone + OTP)
✅ User profiles (tipster & buyer)
✅ Tip posting with OCR
✅ Marketplace with filters & search
✅ M-Pesa payments
✅ Bet code reveal
✅ Automated result verification
✅ Win rate calculation
✅ Badge system (3-4 badges)
✅ Leaderboard (3 tabs)
✅ Wallet & withdrawals
✅ Admin dashboard
✅ Notifications (SMS + in-app)
✅ 48-hour escrow
✅ Dispute management

### What's OUT (Phase 2)

❌ Follow system
❌ Buyer reviews/ratings
❌ Direct messaging
❌ Advanced analytics
❌ ROI calculation
❌ Multi-sport support
❌ Mobile native apps
❌ Tip packages

---

### Development Timeline

```
Phase 0:  Setup & Infrastructure      → Week 1      (5-7 days)
Phase 1:  User Management            → Week 2      (5-7 days)
Phase 2:  Tip Posting System         → Week 3-4    (10-12 days)
Phase 3:  Marketplace & Discovery    → Week 5      (5-7 days)
Phase 4:  Payment & Transactions     → Week 6-7    (10-12 days)
Phase 5:  Wallet & Withdrawals       → Week 8      (5-7 days)
Phase 6:  Result Verification & Stats → Week 9-10   (10-12 days)
Phase 7:  Admin Dashboard            → Week 11     (5-7 days)
Phase 8:  Notifications & Alerts     → Week 12     (5-7 days)
Phase 9:  Polish & Testing           → Week 13-14  (10-12 days)
Phase 10: Deployment & Launch        → Week 15-16  (10-14 days)

TOTAL: 15-16 WEEKS (4 MONTHS)
```

### Team Recommendation

**Small Team (2-3 People) - RECOMMENDED**
```
Timeline: 3-4 months

Structure:
1. Backend Developer (Django, APIs, Database) - 40hrs/week
2. Frontend Developer (HTMX, Tailwind, UI/UX) - 40hrs/week
3. DevOps (optional, part-time) - 10-20hrs/week
```

### Cost Estimate

**Development:**
- Backend Dev: KES 200K/month × 4 = KES 800K
- Frontend Dev: KES 180K/month × 4 = KES 720K
- **Total:** ~KES 1,520,000

**Infrastructure (Monthly):**
- AWS EC2, S3, Textract: KES 10-15K
- API-Football: KES 5-7K
- Domain & SSL: KES 2-5K
- SMS: KES 0.50-1.50 per SMS
- **Total:** KES 15-35K/month

**Grand Total: KES 1.8M - 2.0M**

---

### Success Metrics

**Month 1:**
- 50-100 users (20 tipsters, 30-80 buyers)
- 50-100 tips purchased
- KES 10-20K GMV
- Revenue: KES 4-8K

**Month 3:**
- 500-800 users (100-150 tipsters, 400-650 buyers)
- 500-800 tips purchased
- KES 150-250K GMV
- Revenue: KES 60-100K

**Break-even: Month 6-8**
(Monthly revenue > monthly costs)

---

## 10. Next Steps

### Immediate Actions (Week 0)

**1. Assemble Team**
- Hire developers or agency
- Setup communication (Slack/Discord)
- Create project board (GitHub Projects)

**2. Legal Setup**
- Register business
- Consult lawyer (gambling regulations)
- Draft Terms & Privacy Policy
- Open business bank account
- Apply for M-Pesa Paybill

**3. Financial Setup**
- KRA registration
- Business account
- Accounting system

**4. Third-Party Accounts**
- AWS account
- M-Pesa sandbox
- API-Football subscription
- SMS gateway
- Domain registration

### Week 1: Kick-off

**Day 1: Project Meeting**
- Review this plan
- Q&A
- Assign responsibilities
- Setup Git repo
- Create task board

**Day 2-5: Phase 0**
- Django project setup
- Database design
- AWS configuration
- Base templates

**End of Week 1:**
✅ Development environment ready
✅ Team aligned
✅ Ready for Phase 1

### Sprint Planning (Weekly)

**Every Monday:**
- Review last week
- Plan current week
- Assign tasks
- Identify blockers

**Daily Standups (15 mins):**
- What did you do?
- What will you do?
- Any blockers?

**Every Friday:**
- Demo features
- Code review
- Deploy to staging
- Retrospective

---

### Critical Milestones

```
✓ Week 1:  Environment ready
✓ Week 2:  Users can register
✓ Week 4:  Tipsters can post tips
✓ Week 5:  Marketplace functional
✓ Week 7:  Payments working
✓ Week 10: Results auto-verified
✓ Week 14: MVP complete
✓ Week 16: LAUNCH 🚀
```

---

### Risk Mitigation

**Technical Risks:**
- OCR accuracy → Hybrid (tipster verifies)
- API downtime → Manual fallback
- M-Pesa issues → Comprehensive testing
- Server downtime → Monitoring + alerts

**Business Risks:**
- Low quality tipsters → Verification + tracking
- Fraud → Admin approval + audit logs
- Low adoption → Beta testing + marketing
- Regulatory → Legal consultation

---

## Launch Checklist

### Pre-Launch (1 Week Before)

```
☐ All features tested
☐ Security audit complete
☐ SSL installed
☐ Database backed up
☐ Error tracking configured
☐ Admin accounts created
☐ Terms of Service live
☐ Privacy Policy live
☐ FAQ page complete
☐ Social media accounts
☐ Support email setup
☐ Beta feedback incorporated
☐ Payment flows tested
☐ Mobile responsive verified
☐ Monitoring alerts setup
☐ Rollback plan ready
```

### Launch Day

```
☐ Final smoke tests
☐ Monitor error logs
☐ Watch server metrics
☐ Test registration
☐ Test payments
☐ Check notifications
☐ Monitor M-Pesa
☐ Be ready for fixes
☐ Social media announcement
☐ Support first users
☐ Track transactions
☐ Log all issues
```

---

**Status:** Planning Complete - Ready for Development  
**Total Timeline:** 15-16 weeks  
**Total Investment:** KES 1.8M - 2.0M  
**Break-even:** Month 6-8  

🚀 **Ready to build!**