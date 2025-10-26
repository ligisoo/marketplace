# Create a Ligisoo Football Tips Marketplace

**Create a Ligisoo Football Tips Marketplace using the Technology Stack in this plan, then guided by the plan arranged in the order of what needs to be built first.**

---

## Quick Navigation

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Schema (13 Tables)](#database-schema)
- [Phase 0: Setup (Week 1)](#phase-0-setup)
- [Phase 1: User Management (Week 2)](#phase-1-user-management)
- [Phase 2: Tip Posting (Week 3-4)](#phase-2-tip-posting)
- [Phases 3-10 Overview](#phases-3-10)

---

## Project Overview

**What we're building:** A marketplace where tipsters sell football betting tips (bet codes) to buyers. Platform handles tip posting with OCR, M-Pesa payments, automated result verification, and tipster performance tracking.

**Business Model:**
- Revenue Split: 60/40 (Tipster gets 60%, Platform gets 40%)
- Payment: M-Pesa only (MVP)
- Escrow: 48-hour hold before payout
- Focus: Football tips only

**Timeline:** 15-16 weeks (4 months)  
**Budget:** KES 1.8M - 2.0M (~$13,500-15,000)

---

## Technology Stack

### Backend
- Django 5.0 (Python)
- PostgreSQL (Production)
- SQLite (Development)

### Frontend
- Django Templates
- HTMX (Dynamic updates)
- Tailwind CSS

### Infrastructure
- AWS EC2 (Hosting)
- AWS S3 (File storage)
- AWS Textract (OCR)
- Nginx + Gunicorn

### Integrations
- M-Pesa Daraja API
- API-Football (~$30-50/month)
- SMS Gateway

### Background Jobs
- schedule (Python library)

---

## Project Structure

```
ligisoo-marketplace/
├── manage.py
├── requirements.txt
├── .env
│
├── config/              # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/                # Django applications
│   ├── users/          # Authentication & profiles
│   ├── tips/           # Tip posting & marketplace
│   ├── transactions/   # Payments & purchases
│   ├── withdrawals/    # Tipster payouts
│   ├── disputes/       # Refund management
│   ├── notifications/  # Alerts
│   ├── leaderboard/    # Rankings & badges
│   └── analytics/      # Tracking
│
├── templates/          # HTML templates
│   ├── base.html
│   ├── partials/
│   └── pages/
│
├── static/            # CSS, JS, images
└── scripts/           # Cron jobs
```

---

## Database Schema

### Core Tables (13 Total)

1. **users** - User accounts (phone, username, user_type)
2. **tips** - Betting tips (bet_code, odds, price, screenshot)
3. **transactions** - Purchases (buyer, tip, amount, escrow)
4. **withdrawals** - Tipster payouts (amount, mpesa_phone, status)
5. **disputes** - Refund requests (issue_type, refund_amount)
6. **notifications** - User alerts (type, message, is_read)
7. **tipster_stats** - Performance metrics (win_rate, total_sold)
8. **badges** - Achievement definitions (Top Performer, Quick Seller)
9. **user_badges** - Awarded badges (user, badge, awarded_at)
10. **tip_views** - Analytics tracking (tip, user, viewed_at)
11. **manual_review_queue** - Flagged tips for admin
12. **platform_settings** - Configuration (min_withdrawal_threshold)
13. **admin_audit_log** - Track admin actions

---

## Phase 0: Setup (Week 1)

**Goal:** Development environment ready

### Quick Start Commands

```bash
# 1. Create project
mkdir ligisoo-marketplace && cd ligisoo-marketplace
python -m venv venv
source venv/bin/activate
pip install Django==5.0

# 2. Initialize Django
django-admin startproject config .

# 3. Create apps
python manage.py startapp users
python manage.py startapp tips
python manage.py startapp transactions
python manage.py startapp withdrawals
python manage.py startapp disputes
python manage.py startapp notifications
python manage.py startapp leaderboard
python manage.py startapp analytics

# 4. Install dependencies
pip install psycopg2-binary gunicorn python-decouple Pillow boto3 \
            schedule fuzzywuzzy python-Levenshtein requests django-htmx

# 5. Create requirements.txt
pip freeze > requirements.txt
```

### Key Files to Create

1. **`.env`** - Environment variables (SECRET_KEY, AWS keys, M-Pesa)
2. **`config/settings/base.py`** - Django settings
3. **`templates/base.html`** - Base template with navbar
4. **`config/urls.py`** - URL configuration

### Checklist
- ☐ Django project initialized
- ☐ All apps created
- ☐ Dependencies installed
- ☐ Settings configured
- ☐ Base templates created
- ☐ AWS account setup
- ☐ M-Pesa sandbox account
- ☐ API-Football key obtained

---

## Phase 1: User Management (Week 2)

**Goal:** Complete authentication system

### What to Build

1. **User Model** (apps/users/models.py)
   - Custom user with phone_number
   - UserProfile with wallet_balance
   - Auto-create profile on user creation

2. **Forms** (apps/users/forms.py)
   - RegistrationForm (phone, username, password, user_type)
   - LoginForm
   - ProfileEditForm (bio, profile_picture)

3. **Views** (apps/users/views.py)
   - register() - Create new account
   - user_login() - Authenticate
   - user_logout() - End session
   - profile() - View user profile
   - edit_profile() - Update profile

4. **Templates**
   - register.html - Sign up form
   - login.html - Login form
   - profile.html - User profile page
   - edit_profile.html - Edit form

### Run Migrations

```bash
python manage.py makemigrations users
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Testing
- ☐ Register as buyer
- ☐ Register as tipster
- ☐ Login works
- ☐ View profile
- ☐ Edit profile
- ☐ Upload profile picture

---

## Phase 2: Tip Posting (Week 3-4)

**Goal:** Tipsters can post tips with OCR

### What to Build

1. **Tip Model** (apps/tips/models.py)
   - bet_code, bookmaker, odds, price
   - screenshot (ImageField)
   - match_details (JSON - from OCR)
   - preview_data (JSON - for buyers)
   - status (pending_approval, active, archived)

2. **OCR Service** (apps/tips/ocr.py)
   - BetslipOCR class
   - extract_text() - AWS Textract
   - parse_betslip() - Extract bet code, odds, matches

3. **Views**
   - create_tip() - Upload screenshot
   - verify_tip() - Confirm OCR extraction
   - my_tips() - Tipster dashboard

4. **Forms**
   - TipSubmissionForm (bet_code, bookmaker, price, screenshot)
   - TipVerificationForm (select markets for each match)

### Key Features
- Upload betslip screenshot
- OCR extracts: bet code, odds, match names
- Tipster verifies and selects markets
- Admin approval (new tipsters)
- Auto-publish (verified tipsters)

---

## Phases 3-10 Overview

### Phase 3: Marketplace (Week 5)
- Browse active tips
- Filters (sport, odds, price, bookmaker)
- Search by tipster
- Tip detail page

### Phase 4: Payments (Week 6-7)
- M-Pesa STK Push integration
- Purchase flow
- Bet code reveal after payment
- Transaction tracking
- Escrow system (60/40 split)

### Phase 5: Wallet & Withdrawals (Week 8)
- Display wallet balance
- Withdrawal requests
- M-Pesa B2C payouts
- Admin approval
- Escrow automation (cron)

### Phase 6: Results & Stats (Week 9-10)
- API-Football integration
- Automated result checking (cron)
- Win rate calculation
- Badge system (Top Performer, Quick Seller)
- Leaderboard (top performers, earners)

### Phase 7: Admin Dashboard (Week 11)
- Dashboard metrics
- Tip approval queue
- User management
- Dispute handling
- Financial reports

### Phase 8: Notifications (Week 12)
- SMS integration (critical)
- In-app notifications (HTMX)
- Notification types:
  * Tip purchased
  * Payment received
  * Withdrawal approved
  * Result updated

### Phase 9: Testing & Polish (Week 13-14)
- End-to-end testing
- Security audit
- Performance optimization
- Bug fixes
- Mobile responsiveness

### Phase 10: Deployment (Week 15-16)
- Production server setup (AWS EC2)
- SSL certificate (Let's Encrypt)
- Production integrations (M-Pesa, API-Football)
- Monitoring setup
- Soft launch
- Public launch 🚀

---

## Key Business Logic

### Revenue Split
```python
# 60% to tipster, 40% to platform
tipster_earning = amount * 0.60
platform_fee = amount * 0.40
```

### Escrow System
```python
# Hold funds for 48 hours after last match
escrow_release_at = tip.last_match_starts_at + timedelta(hours=48)
```

### Win Rate Calculation
```python
# Minimum 10 resulted tips required
win_rate = (tips_won / total_resulted_tips) * 100
```

### Auto-Archive
```python
# Archive tips when last match starts
if tip.last_match_starts_at <= now():
    tip.status = 'archived'
```

---

## Success Metrics

### Month 1
- 50-100 users (20 tipsters, 30-80 buyers)
- 50-100 tips purchased
- KES 10,000-20,000 GMV
- Platform revenue: KES 4,000-8,000

### Month 3
- 500-800 users (100-150 tipsters, 400-650 buyers)
- 500-800 tips purchased
- KES 150,000-250,000 GMV
- Platform revenue: KES 60,000-100,000

### Break-even: Month 6-8
(When monthly revenue > monthly costs)

---

## Next Steps

1. **Start with Phase 0** - Setup development environment
2. **Build Phase 1** - User authentication
3. **Build Phase 2** - Tip posting with OCR
4. **Continue sequentially** through phases 3-10
5. **Test thoroughly** at each phase
6. **Deploy to production** in Week 15-16

---

**Full detailed document available at:**
`/mnt/user-data/outputs/ligisoo-execution-plan.md`

**Original planning document:**
`/mnt/user-data/outputs/tips-marketplace-plan.md`

---

*Ready to start building? Begin with Phase 0!* 🚀