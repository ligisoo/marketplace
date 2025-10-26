# Tips Marketplace - Planning Document

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
```
User Types:
• Buyers - Browse and purchase tips
• Tipsters - Post and sell tips  
• Admins - Manage platform

Registration/Login:
• Phone number + OTP verification
• Profile setup wizard

User Profiles:
Tipster Public Profile:
  - Username/display name
  - Bio (150 characters max)
  - Join date
  - Win rate % (auto-calculated)
  - Total tips sold
  - Average odds
  - Total tips: Won/Lost/Pending
  - Verified badge (if admin approved)
  - Recent tips (last 10)
  
Buyer Profile:
  - Username
  - Join date
  - Total purchases
  - Private stats (visible only to user)
```

#### 2. Tip Discovery & Marketplace
```
Homepage/Marketplace Layout:
• Live tips feed (grid view)
• Featured tips section (admin promoted)
• "Ending Soon" section (< 1 hour to kickoff)
• "Hot Tipsters" widget (top 5 performers)

Filters:
☑️ Sport (Football, Basketball, Tennis, etc.)
☑️ Odds range (2-5x, 5-10x, 10-50x, 50x+)
☑️ Price (Free, 1-100, 100-500, 500+)
☑️ Selections count (Single, 2-5, 5-10, 10+)
☑️ Time to kickoff (Next hour, Today, Tomorrow, This week)
☑️ Bookmaker (SportPesa, Betika, Bet365, 22Bet, etc.)

Sort Options:
• Newest first (default)
• Ending soon
• Highest odds
• Lowest price
• Best tipster (win rate)
• Most purchased

Search Bar:
• Search tipster by username
• Search by sport/league keywords
• Auto-suggestions as you type
```

#### 3. Leaderboard System 🏆
```
Leaderboard Tabs:

📊 Top Performers (This Month)
Rank | Tipster | Win Rate | Tips | Avg Odds
1    | @ProTips254 | 78% | 45 | 12.5x
2    | @BetKing_KE | 75% | 38 | 8.3x
...

💰 Top Earners (This Month)
Rank | Tipster | Earnings | Tips Sold
1    | @ProTips254 | KES 45,600 | 156
2    | @BetMaster | KES 38,200 | 201
...

⭐ Rising Stars (New Tipsters <30 days)
Rank | Tipster | Win Rate | Tips
1    | @NewPro23 | 85% | 12
2    | @FreshTips | 80% | 15
...

Leaderboard Updates:
• Real-time updates after each match result
• Monthly reset (archive previous months)
• Badge rewards for top 3 in each category
• Visible on homepage + dedicated page
```

#### 4. Rating & Trust System
```
Auto-Calculated Tipster Stats:
• Win Rate: 68% (Won/Total tips with results)
• Total Tips Posted: 156
• Won: 106 | Lost: 50 | Pending: 12
• Average Odds: 5.5x
• ROI: +34% (calculated based on performance)
• Member Since: Jan 2025
• Tips Sold: 234
• Active Streak: 5 wins in a row

Trust Badges (Auto-Awarded):
🏆 Top Performer - Win rate ≥ 70% (30+ tips)
⚡ Quick Seller - 50+ tips sold
🔥 Hot Streak - 10 consecutive wins
✅ Verified Tipster - Admin approved (auto-publish enabled)
⭐ Rising Star - New tipster (<30 days) with 80%+ win rate
💎 Consistent - 90%+ tips resulted (not pending)
🎯 Specialist - 70%+ win rate in specific sport

Stats Visibility:
• Prominently displayed on profile
• Shown in marketplace listings (mini version)
• Updated in real-time after match results
```

#### 5. Transaction & Wallet System
```
Buyer Dashboard:
My Purchases:
  • All purchased tips
  • Filters: Active | Archived | Won | Lost | Pending
  • Quick actions: Copy code, Download screenshot
  • Purchase date, amount, status
  • Dispute button (if within window)

Purchase History:
  • Transaction log (date, amount, tipster)
  • Download receipts
  • Total spent tracker

Tipster Dashboard:
My Wallet:
  • Available Balance: KES 1,250 (ready to withdraw)
  • Pending (in escrow): KES 450
  • Total Earned: KES 5,680
  • [Withdraw Funds] button (enabled when ≥ threshold)

My Tips:
  • All posted tips
  • Filters: Active | Archived | Pending Approval | Sold
  • Stats per tip: Views, Purchases, Earnings
  • Edit/Delete (if not purchased yet)
  • Sales performance graph

Earnings History:
  • Transaction log (date, tip, amount, status)
  • Filter by date range
  • Export to CSV

Withdrawal System:
  • Request withdrawal (≥ KES 500)
  • Enter M-Pesa number
  • Admin approval (or auto for trusted)
  • Track withdrawal status
  • Withdrawal history log
```

#### 6. Notifications System
```
SMS Notifications (Critical Only):
• Payment received (buyer purchase confirmation)
• Withdrawal approved (tipster payout)
• Dispute filed/resolved
• Account suspended/verified

In-App Notifications (Bell Icon):
• Tip purchased (for tipsters)
• Tip approved/rejected (for tipsters)
• Payment successful (for buyers)
• Tip ending soon (if viewed/saved)
• Match starting in 30 mins
• Withdrawal processed
• Dispute updates
• Admin announcements

Email Notifications (Optional):
• Weekly summary (earnings for tipsters)
• Monthly performance report
• Important account updates
• Password reset
```

#### 7. Admin Dashboard
```
Overview Metrics:
• Total Users: 1,234 (Buyers: 980 | Tipsters: 254)
• Active Tips: 45
• Today's Transactions: KES 12,500
• Pending Approvals: 8 tips
• Open Disputes: 3
• Revenue (last 30 days): KES 145,000

Quick Actions Panel:
• [Approve Tips] (8 pending)
• [Review Disputes] (3 open)
• [Featured Tips] (manage promoted)
• [User Management] (ban/verify)
• [Withdrawals] (5 pending)
• [Send Announcement]

Tips Management:
• View all tips (active/archived)
• Approve/reject new tipster submissions
• Feature/unfeature tips
• Toggle auto-publish for trusted tipsters
• Delete fraudulent tips
• View tip performance

User Management:
• View all users (filter: tipsters/buyers)
• User details (stats, history, transactions)
• Ban/suspend users
• Verify tipsters (enable auto-publish)
• Reset passwords
• Send direct messages

Disputes Management:
• View all disputes (open/resolved)
• Review evidence (screenshots, logs)
• Verify bet codes in bookmakers
• Approve/reject refunds
• Communicate with users
• Track dispute patterns

Financial Management:
• Transaction logs (all payments)
• Revenue reports (daily/weekly/monthly)
• Withdrawal requests queue
• Approve/reject withdrawals
• Adjust payout thresholds
• View platform earnings

Analytics:
• User growth charts
• Transaction volume trends
• Top performing tipsters
• Popular sports/bookmakers
• Average tip price
• Conversion rates (views → purchases)
• Export reports (CSV/PDF)
```

#### 8. One-Way Communication
```
Tipster → Buyers:
• Tipsters can add notes to tips (visible after purchase)
• Example: "Both teams in good form, expect goals"
• Limited to 200 characters
• Optional field when posting tip

Admin → Users:
• Platform announcements
• System notifications
• Broadcast messages (email/SMS)

Buyers → Admin:
• Report issue (disputes)
• Contact support (support tickets)
• Feedback form

NO direct buyer-to-tipster messaging in MVP
```

---

### Phase 2 Features (Post-Launch) 🚀

#### 1. Social Features
```
Follow System:
• Follow favorite tipsters
• "Following" feed on homepage
• Get notifications for new tips from followed tipsters
• Unfollow option
• Display follower count on profiles

Follower Benefits:
• Early access to tips (5-10 min before public)
• Exclusive tips (followers only)
• Price discounts for loyal followers
```

#### 2. Review System
```
Buyer Reviews:
• 5-star rating per tip (after match completes)
• Optional text review (200 characters)
• Can only review purchased tips
• One review per tip
• Display average rating on tipster profile

Review Moderation:
• Admin can hide inappropriate reviews
• Tipsters can report unfair reviews
• Verified purchase badge on reviews
```

#### 3. Advanced Analytics
```
For Tipsters:
• Performance graphs (win rate over time)
• Best performing sports/leagues
• Peak selling times/days
• Follower growth chart
• Revenue projections
• Competitor benchmarking

For Buyers:
• Portfolio tracking (total spent vs won)
• Best tipsters I follow
• Personal ROI tracker
• Purchase patterns
• Recommendations based on history
```

#### 4. Enhanced Communication
```
• Direct messaging (buyer ↔ tipster)
• Comment sections on tips
• Group chats for premium subscribers
• Integration with Telegram/WhatsApp
```

#### 5. Premium Features
```
• Tip packages/bundles
• Subscription to tipsters (monthly unlimited access)
• Private exclusive tips
• Video analysis from tipsters
• Live betting tips (in-play markets)
```

#### 6. Gamification
```
• Achievement system (more badges)
• Challenges (weekly competitions)
• Levels (bronze → silver → gold → platinum)
• Rewards program (cashback, discounts)
• Referral program
```

---

### Platform Details

**Platform Type:** Web Application (Responsive)
- Desktop optimized
- Mobile-friendly (responsive design)
- Can be used on mobile browsers
- No native mobile app in MVP
- Progressive Web App (PWA) capabilities (optional)

**Key UX Principles:**
- Mobile-first design approach
- Fast loading times
- Simple, intuitive navigation
- Clear call-to-action buttons
- Minimal clicks to purchase
- Thumb-friendly buttons on mobile

---

## 3. User Flows

### A. Tipster Submission Flow ✅

**Step 1: Quick Submit Form (4 Required Fields)**
```
1. Paste Bet Code: [Text Input] e.g., RSCEHO
2. Select Bookmaker: [Dropdown] SportPesa, Betika, Bet365, 22Bet, etc.
3. Upload Screenshot: [Image Upload - Required]
4. Set Price: [Number Input] KES _____ (Allow KES 0 for free tips)

[Submit Button]
```

**Step 2: OCR Processing**
- System extracts from screenshot:
  - Total odds
  - Number of selections
  - Sport type (if detectable)
  - Match details (for admin verification)

**Step 3: Tipster Verification Preview**
```
Review Your Tip Before Publishing:

📊 Extracted Info:
• Total Odds: 47.35
• Selections: 5
• Sport: Football
• Bookmaker: SportPesa
• Price: KES 200

Does this look correct?
[Edit] [Confirm & Submit]
```

**Step 4: Approval Process**
- **New Tipsters**: Tip goes to admin approval queue
- **Trusted Tipsters**: Tip publishes instantly (admin can toggle "Auto-Publish" status)

**Step 5: Live on Marketplace**
```
Auto-Generated Preview (What Buyers See):
🎯 Multi-Bet Accumulator
📊 Total Odds: 47.35
🎫 5 Selections
⚽ Sport: Football
💰 Potential Return: 47x your stake
📸 Verified Screenshot ✓

💎 Price: KES 200 (or FREE)

🔒 Bet Code & Matches Hidden Until Purchase
✅ Tipster: @Username (Win Rate: 68%)
```

**Key Features:**
- ✅ Minimal input (4 fields only)
- ✅ OCR automation (reduce manual work)
- ✅ Tipster verification step (ensure accuracy)
- ✅ Admin approval for new users
- ✅ Auto-publish toggle for trusted tipsters
- ✅ Free pricing option (KES 0 allowed)
- ✅ Screenshot required (builds trust)

---

### B. Buyer Purchase Flow ✅

**Step 1: Browse Marketplace**
```
Marketplace Listing:
- All live tips with preview info
- Filters: Sport, Odds range, Price, Tipster rating, Time to kickoff
- Sort by: Newest, Highest odds, Best tipster, Lowest price, Ending soon
```

**Step 2: View Tip Details**
```
[Tip Detail Page]

🎯 Multi-Bet Accumulator
📊 Total Odds: 47.35
🎫 5 Selections
⚽ Sport: Football
⏰ First match starts: 2 hours from now
⏰ Last match starts: 6 hours from now

💎 Price: KES 200 (or FREE)
📸 Screenshot preview available

✅ Tipster: @ProTips254
• Win Rate: 68% (23W-7L last 30 days)
• Avg Odds: 5.5
• Total Tips Sold: 156
• Member since: Jan 2025

[Purchase Now - KES 200] or [Get Free Tip]
```

**Step 3: Payment**
```
Payment Method: M-Pesa Only (MVP)

Process:
1. Enter M-Pesa number
2. Receive STK push
3. Enter PIN
4. Instant confirmation
```

**Step 4: Instant Access**
```
Purchase Successful! ✅

✅ BET CODE: RSCEHO
✅ Bookmaker: SportPesa Kenya

[Copy Code] ← One-click copy
[Download Screenshot] ← Watermarked with buyer info

📋 How to Use:
1. Open SportPesa app/website
2. Find "Load Betslip" or "Share Code"
3. Paste code: RSCEHO
4. Verify odds match (47.35)
5. Place your bet

⏰ First match in 2 hours
⏰ Last match in 6 hours

📍 Find this in "My Purchases" anytime
```

**Step 5: Access Purchased Tips**
```
My Purchases Section:
- View all purchased tips
- Filter: Active, Completed, Archived
- Copy bet code anytime
- Download watermarked screenshots
- Track results (Won/Lost/Pending)

Watermark includes:
"Purchased by @BuyerUsername on [Date/Time]"
```

**Step 6: Auto-Archive System**
```
Tips automatically archive when:
- Last match in the accumulator starts
- No longer available for new purchases
- Buyers can still access their purchased tips

Status indicators:
🟢 Active (available to purchase)
🟡 Ending Soon (< 30 mins to last match)
🔴 Archived (matches started)
```

**Key Features:**
- ✅ M-Pesa payment only (simple start)
- ✅ Instant access after purchase
- ✅ One-click code copy
- ✅ Watermarked downloads (prevent reselling)
- ✅ My Purchases section (lifetime access)
- ✅ Auto-archive after last match starts
- ✅ Time-based urgency indicators

---

## 4. Database Schema

### Entity Relationship Overview
```
Users (1) ----→ (Many) Tips
Users (1) ----→ (Many) Transactions (Purchases)
Users (1) ----→ (Many) Withdrawals
Tips (1) ----→ (Many) Transactions
Transactions (1) ----→ (0..1) Disputes
Users (1) ----→ (Many) Notifications
Tips (1) ----→ (Many) TipViews (analytics)
Tips (1) ----→ (0..1) ManualReviewQueue
```

---

### Tables & Schema (13 Core Tables)

#### 1. **users**
```sql
id                    UUID PRIMARY KEY
phone_number          VARCHAR(20) UNIQUE NOT NULL
phone_verified        BOOLEAN DEFAULT FALSE
email                 VARCHAR(255) UNIQUE (nullable)
username              VARCHAR(50) UNIQUE NOT NULL
display_name          VARCHAR(100)
bio                   TEXT (max 150 chars)
user_type             ENUM('buyer', 'tipster', 'admin') DEFAULT 'buyer'
profile_picture_url   VARCHAR(500)
is_verified_tipster   BOOLEAN DEFAULT FALSE (admin verified badge)
auto_publish_enabled  BOOLEAN DEFAULT FALSE (trusted tipster)
is_active             BOOLEAN DEFAULT TRUE
is_banned             BOOLEAN DEFAULT FALSE
ban_reason            TEXT
wallet_balance        DECIMAL(10,2) DEFAULT 0.00 (tipster earnings)
total_earned          DECIMAL(10,2) DEFAULT 0.00 (lifetime)
total_spent           DECIMAL(10,2) DEFAULT 0.00 (buyer purchases)
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()
last_login_at         TIMESTAMP

-- Indexes
INDEX idx_username (username)
INDEX idx_phone (phone_number)
INDEX idx_user_type (user_type)
INDEX idx_verified_tipster (is_verified_tipster)
```

#### 2. **tips**
```sql
id                    UUID PRIMARY KEY
tipster_id            UUID FOREIGN KEY → users(id)
bet_code              VARCHAR(50) NOT NULL
bookmaker             VARCHAR(50) NOT NULL (SportPesa, Betika, etc.)
sport                 VARCHAR(50) (Football, Basketball, etc.)
total_odds            DECIMAL(10,2) NOT NULL
selections_count      INTEGER NOT NULL (number of matches)
price                 DECIMAL(10,2) NOT NULL (can be 0 for free)
screenshot_url        VARCHAR(500) NOT NULL
watermarked_screenshot_url VARCHAR(500)

-- Auto-extracted info (from OCR)
match_details         JSON (array of matches if extracted)
leagues               JSON (array of leagues)

-- Preview information (what buyers see before purchase)
preview_data          JSON {
                        "partial_matches": ["Man United vs ___", ...],
                        "match_count": 5,
                        "first_match_time": "2025-10-25T19:00:00Z",
                        "last_match_time": "2025-10-25T21:00:00Z"
                      }

-- Status
status                ENUM('pending_approval', 'active', 'archived', 'rejected') DEFAULT 'pending_approval'
rejection_reason      TEXT
featured              BOOLEAN DEFAULT FALSE (admin promoted)
featured_until        TIMESTAMP

-- Match timing
first_match_starts_at TIMESTAMP NOT NULL
last_match_starts_at  TIMESTAMP NOT NULL

-- Results tracking
result_status         ENUM('pending', 'won', 'lost', 'void') DEFAULT 'pending'
result_updated_at     TIMESTAMP

-- Analytics
view_count            INTEGER DEFAULT 0
purchase_count        INTEGER DEFAULT 0
total_revenue         DECIMAL(10,2) DEFAULT 0.00 (tipster earnings from this tip)

-- Timestamps
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()
approved_at           TIMESTAMP
archived_at           TIMESTAMP

-- Indexes
INDEX idx_tipster (tipster_id)
INDEX idx_status (status)
INDEX idx_first_match (first_match_starts_at)
INDEX idx_last_match (last_match_starts_at)
INDEX idx_bookmaker (bookmaker)
INDEX idx_sport (sport)
INDEX idx_result_status (result_status)
INDEX idx_featured (featured, featured_until)
INDEX idx_active_tips (status, first_match_starts_at) -- for marketplace queries
```

#### 3. **transactions** (Purchases)
```sql
id                    UUID PRIMARY KEY
transaction_ref       VARCHAR(100) UNIQUE NOT NULL (M-Pesa ref)
buyer_id              UUID FOREIGN KEY → users(id)
tip_id                UUID FOREIGN KEY → tips(id)
tipster_id            UUID FOREIGN KEY → users(id) (denormalized for queries)

-- Payment details
amount                DECIMAL(10,2) NOT NULL
payment_method        VARCHAR(50) DEFAULT 'mpesa'
mpesa_phone           VARCHAR(20)
mpesa_receipt         VARCHAR(100)
payment_status        ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending'

-- Revenue split
platform_fee          DECIMAL(10,2) (40% of amount)
tipster_earning       DECIMAL(10,2) (60% of amount)
processing_fee        DECIMAL(10,2) (M-Pesa fee absorbed)

-- Escrow
escrow_status         ENUM('held', 'released', 'refunded') DEFAULT 'held'
escrow_release_at     TIMESTAMP (48 hours after last match)
released_at           TIMESTAMP

-- Watermarking (prevent reselling)
watermark_text        VARCHAR(200) (buyer username + timestamp)

-- Timestamps
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()
completed_at          TIMESTAMP

-- Indexes
INDEX idx_buyer (buyer_id)
INDEX idx_tip (tip_id)
INDEX idx_tipster (tipster_id)
INDEX idx_transaction_ref (transaction_ref)
INDEX idx_payment_status (payment_status)
INDEX idx_escrow (escrow_status, escrow_release_at)
INDEX idx_created_at (created_at)
```

#### 4. **disputes**
```sql
id                    UUID PRIMARY KEY
transaction_id        UUID FOREIGN KEY → transactions(id) UNIQUE
buyer_id              UUID FOREIGN KEY → users(id)
tipster_id            UUID FOREIGN KEY → users(id)
tip_id                UUID FOREIGN KEY → tips(id)

-- Dispute details
issue_type            ENUM('invalid_code', 'wrong_info', 'technical_error', 'other')
description           TEXT NOT NULL
evidence_url          VARCHAR(500) (screenshot of error)

-- Resolution
status                ENUM('open', 'under_review', 'resolved', 'rejected') DEFAULT 'open'
resolution            TEXT
refund_amount         DECIMAL(10,2)
refund_percentage     INTEGER (100, 80, or 0)
admin_notes           TEXT

-- Timestamps
created_at            TIMESTAMP DEFAULT NOW()
resolved_at           TIMESTAMP
reviewed_by           UUID FOREIGN KEY → users(id) (admin)

-- Indexes
INDEX idx_transaction (transaction_id)
INDEX idx_status (status)
INDEX idx_buyer (buyer_id)
INDEX idx_created_at (created_at)
```

#### 5. **withdrawals**
```sql
id                    UUID PRIMARY KEY
tipster_id            UUID FOREIGN KEY → users(id)
amount                DECIMAL(10,2) NOT NULL
mpesa_phone           VARCHAR(20) NOT NULL
mpesa_receipt         VARCHAR(100) (after completion)

status                ENUM('pending', 'approved', 'processing', 'completed', 'failed', 'rejected') DEFAULT 'pending'
rejection_reason      TEXT

-- Fees
withdrawal_fee        DECIMAL(10,2) DEFAULT 0.00
net_amount            DECIMAL(10,2) (amount - withdrawal_fee)

-- Admin actions
approved_by           UUID FOREIGN KEY → users(id) (admin)
approved_at           TIMESTAMP
processed_at          TIMESTAMP
completed_at          TIMESTAMP

created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_tipster (tipster_id)
INDEX idx_status (status)
INDEX idx_created_at (created_at)
```

#### 6. **notifications**
```sql
id                    UUID PRIMARY KEY
user_id               UUID FOREIGN KEY → users(id)
type                  VARCHAR(50) NOT NULL (tip_purchased, withdrawal_approved, etc.)
title                 VARCHAR(200) NOT NULL
message               TEXT NOT NULL
action_url            VARCHAR(500) (link to relevant page)

-- Related entities
related_tip_id        UUID FOREIGN KEY → tips(id) (nullable)
related_transaction_id UUID FOREIGN KEY → transactions(id) (nullable)

-- Status
is_read               BOOLEAN DEFAULT FALSE
sent_via_sms          BOOLEAN DEFAULT FALSE
sent_via_email        BOOLEAN DEFAULT FALSE

created_at            TIMESTAMP DEFAULT NOW()
read_at               TIMESTAMP

-- Indexes
INDEX idx_user (user_id, is_read)
INDEX idx_created_at (created_at)
INDEX idx_type (type)
```

#### 7. **tip_views** (Analytics)
```sql
id                    UUID PRIMARY KEY
tip_id                UUID FOREIGN KEY → tips(id)
user_id               UUID FOREIGN KEY → users(id) (nullable if not logged in)
session_id            VARCHAR(100) (for anonymous tracking)
ip_address            VARCHAR(50)
user_agent            TEXT

viewed_at             TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_tip (tip_id)
INDEX idx_user (user_id)
INDEX idx_viewed_at (viewed_at)
```

#### 8. **badges** (Tipster Achievements)
```sql
id                    UUID PRIMARY KEY
code                  VARCHAR(50) UNIQUE NOT NULL (top_performer, hot_streak, etc.)
name                  VARCHAR(100) NOT NULL (Top Performer)
description           TEXT
icon_url              VARCHAR(500)
criteria              JSON {
                        "win_rate_min": 70,
                        "tips_min": 30,
                        "period_days": 30
                      }

is_active             BOOLEAN DEFAULT TRUE
created_at            TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_code (code)
```

#### 9. **user_badges** (Many-to-Many)
```sql
id                    UUID PRIMARY KEY
user_id               UUID FOREIGN KEY → users(id)
badge_id              UUID FOREIGN KEY → badges(id)
awarded_at            TIMESTAMP DEFAULT NOW()
expires_at            TIMESTAMP (for temporary badges)

UNIQUE(user_id, badge_id)

-- Indexes
INDEX idx_user (user_id)
INDEX idx_badge (badge_id)
```

#### 10. **tipster_stats** (Calculated Stats - Materialized View or Cache)
```sql
id                    UUID PRIMARY KEY
tipster_id            UUID FOREIGN KEY → users(id) UNIQUE
calculation_period    VARCHAR(20) DEFAULT 'last_30_days'

-- Performance metrics
total_tips            INTEGER DEFAULT 0
tips_won              INTEGER DEFAULT 0
tips_lost             INTEGER DEFAULT 0
tips_pending          INTEGER DEFAULT 0
win_rate              DECIMAL(5,2) DEFAULT 0.00 (percentage)
average_odds          DECIMAL(10,2) DEFAULT 0.00
roi                   DECIMAL(10,2) DEFAULT 0.00 (percentage)

-- Sales metrics
total_sold            INTEGER DEFAULT 0
total_revenue         DECIMAL(10,2) DEFAULT 0.00
average_price         DECIMAL(10,2) DEFAULT 0.00

-- Engagement
total_views           INTEGER DEFAULT 0
conversion_rate       DECIMAL(5,2) DEFAULT 0.00 (sold/views %)

-- Streaks
current_win_streak    INTEGER DEFAULT 0
longest_win_streak    INTEGER DEFAULT 0

-- Rankings
rank_by_winrate       INTEGER
rank_by_earnings      INTEGER

last_calculated_at    TIMESTAMP DEFAULT NOW()
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_tipster (tipster_id)
INDEX idx_win_rate (win_rate)
INDEX idx_total_revenue (total_revenue)
INDEX idx_rank_winrate (rank_by_winrate)
INDEX idx_rank_earnings (rank_by_earnings)
```

#### 11. **platform_settings** (Admin Configuration)
```sql
id                    UUID PRIMARY KEY
setting_key           VARCHAR(100) UNIQUE NOT NULL
setting_value         TEXT NOT NULL
data_type             ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string'
description           TEXT
category              VARCHAR(50) (payment, limits, features, etc.)

updated_by            UUID FOREIGN KEY → users(id) (admin)
updated_at            TIMESTAMP DEFAULT NOW()
created_at            TIMESTAMP DEFAULT NOW()

-- Example settings:
-- 'min_withdrawal_threshold': 500
-- 'tipster_commission_rate': 60
-- 'platform_commission_rate': 40
-- 'escrow_hold_hours': 48
-- 'dispute_window_minutes': 30
-- 'featured_tip_price': 500

-- Indexes
INDEX idx_key (setting_key)
INDEX idx_category (category)
```

#### 12. **admin_audit_log** (Track Admin Actions)
```sql
id                    UUID PRIMARY KEY
admin_id              UUID FOREIGN KEY → users(id)
action_type           VARCHAR(100) NOT NULL (approve_tip, ban_user, etc.)
entity_type           VARCHAR(50) (tip, user, withdrawal, etc.)
entity_id             UUID
old_value             JSON
new_value             JSON
ip_address            VARCHAR(50)
notes                 TEXT

created_at            TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_admin (admin_id)
INDEX idx_action_type (action_type)
INDEX idx_entity (entity_type, entity_id)
INDEX idx_created_at (created_at)
```

#### 13. **manual_review_queue** (Flagged Tips for Manual Verification)
```sql
id                    UUID PRIMARY KEY
tip_id                UUID FOREIGN KEY → tips(id) UNIQUE
reason                VARCHAR(500) NOT NULL
details               TEXT
flagged_by            VARCHAR(50) DEFAULT 'system' (system, tipster, buyer, admin)

-- Status
status                ENUM('pending', 'reviewing', 'resolved', 'escalated') DEFAULT 'pending'
priority              INTEGER DEFAULT 0 (higher = more urgent)

-- Resolution
resolved_by           UUID FOREIGN KEY → users(id) (admin)
resolution_notes      TEXT
resolved_at           TIMESTAMP

-- Timestamps
flagged_at            TIMESTAMP DEFAULT NOW()
created_at            TIMESTAMP DEFAULT NOW()

-- Indexes
INDEX idx_tip (tip_id)
INDEX idx_status (status)
INDEX idx_priority (priority, flagged_at)
INDEX idx_flagged_at (flagged_at)
```

---

### Key Relationships Summary

```
1. User → Tips (One-to-Many)
   - A tipster can post many tips
   
2. User → Transactions (One-to-Many) 
   - A buyer can purchase many tips
   - A tipster receives many purchases
   
3. Tip → Transactions (One-to-Many)
   - A tip can be purchased by many buyers
   
4. Transaction → Dispute (One-to-One optional)
   - A transaction may have one dispute
   
5. User → Withdrawals (One-to-Many)
   - A tipster can make many withdrawal requests
   
6. User → Notifications (One-to-Many)
   - A user receives many notifications
   
7. Tip → TipViews (One-to-Many)
   - A tip is viewed many times
   
8. User ↔ Badges (Many-to-Many via user_badges)
   - Users can have multiple badges
   - Badges can be awarded to multiple users
```

---

### Calculated Fields & Queries

#### Leaderboard Queries
```sql
-- Top Performers (This Month)
SELECT 
    u.id, u.username, u.display_name,
    ts.win_rate, ts.total_tips, ts.average_odds
FROM users u
JOIN tipster_stats ts ON u.id = ts.tipster_id
WHERE u.user_type = 'tipster'
  AND u.is_active = TRUE
  AND ts.total_tips >= 10
ORDER BY ts.win_rate DESC, ts.total_tips DESC
LIMIT 10;

-- Top Earners (This Month)
SELECT 
    u.id, u.username, u.display_name,
    ts.total_revenue, ts.total_sold
FROM users u
JOIN tipster_stats ts ON u.id = ts.tipster_id
WHERE u.user_type = 'tipster'
  AND u.is_active = TRUE
ORDER BY ts.total_revenue DESC
LIMIT 10;

-- Rising Stars (New Tipsters)
SELECT 
    u.id, u.username, u.display_name,
    ts.win_rate, ts.total_tips
FROM users u
JOIN tipster_stats ts ON u.id = ts.tipster_id
WHERE u.user_type = 'tipster'
  AND u.is_active = TRUE
  AND u.created_at >= NOW() - INTERVAL '30 days'
  AND ts.total_tips >= 5
ORDER BY ts.win_rate DESC
LIMIT 10;
```

#### Marketplace Query (with filters)
```sql
SELECT 
    t.*,
    u.username, u.display_name, u.is_verified_tipster,
    ts.win_rate, ts.total_sold
FROM tips t
JOIN users u ON t.tipster_id = u.id
LEFT JOIN tipster_stats ts ON u.id = ts.tipster_id
WHERE t.status = 'active'
  AND t.first_match_starts_at > NOW()
  -- Filters
  AND t.sport = ? (if filter applied)
  AND t.total_odds BETWEEN ? AND ? (if filter applied)
  AND t.price BETWEEN ? AND ? (if filter applied)
  AND t.bookmaker = ? (if filter applied)
ORDER BY t.created_at DESC -- or other sort option
LIMIT 20 OFFSET 0;
```

#### Auto-Archive Cron Job
```sql
-- Archive tips where last match has started
UPDATE tips
SET status = 'archived', archived_at = NOW()
WHERE status = 'active'
  AND last_match_starts_at <= NOW();
```

#### Escrow Release Cron Job
```sql
-- Release funds from escrow after 48 hours
UPDATE transactions
SET escrow_status = 'released', released_at = NOW()
WHERE escrow_status = 'held'
  AND escrow_release_at <= NOW()
  AND payment_status = 'completed';

-- Update tipster wallets
UPDATE users u
SET wallet_balance = wallet_balance + (
    SELECT COALESCE(SUM(t.tipster_earning), 0)
    FROM transactions t
    WHERE t.tipster_id = u.id
      AND t.escrow_status = 'released'
      AND t.released_at >= NOW() - INTERVAL '1 minute'
)
WHERE u.user_type = 'tipster';
```

---

### Data Integrity Rules

1. **Cascade Deletes:**
   - User deleted → Soft delete (set is_active = false)
   - Keep transaction history for audit

2. **Constraints:**
   - Tips can only be posted by tipsters (user_type = 'tipster')
   - Transactions: buyer_id ≠ tipster_id (can't buy own tips)
   - Withdrawal amount ≤ wallet_balance
   - Price >= 0 (allow free tips)

3. **Triggers:**
   - Update tip.purchase_count when transaction created
   - Update tip.view_count when tip_view created
   - Update user.wallet_balance when escrow released
   - Update tipster_stats when tip result updated
   - Archive tips when last_match_starts_at passes

4. **Validation:**
   - Phone numbers: Kenyan format (+254...)
   - Bet codes: Alphanumeric, 4-20 characters
   - Odds: Must be > 1.0
   - Price: Max 100,000 KES (reasonable limit)

---

## 5. Technical Implementation

### Tech Stack ✅

#### Backend Framework
```
Django 5.0 (Python web framework)
- Mature, battle-tested framework
- Built-in admin panel (perfect for admin dashboard)
- ORM for database operations
- Authentication system included
- Form handling and validation
- Template engine
- Security features (CSRF, XSS protection)

Key Django Apps:
- users (authentication, profiles)
- tips (tip posting, marketplace)
- transactions (payments, purchases)
- withdrawals (payout system)
- notifications (alerts system)
- leaderboard (rankings)
- disputes (refund management)
```

#### Database
```
PostgreSQL (Production)
- Robust relational database
- JSON field support for flexible data
- Full-text search capabilities
- Reliable for financial transactions
- ACID compliance
- Excellent for complex queries

SQLite (Development)
- Lightweight for local development
- Easy setup, no server needed
- Quick iterations
```

#### Frontend Stack
```
Django Templates (Server-side rendering)
- Simple, maintainable
- No complex build process
- SEO-friendly
- Fast initial page loads

HTMX (Dynamic interactions)
- Real-time updates without page reloads
- Minimal JavaScript
- Progressive enhancement
- Perfect for:
  * Live marketplace updates
  * Notification polling
  * Form submissions without reload
  * Dynamic filters
  * Infinite scroll

Tailwind CSS (Styling)
- Utility-first CSS framework
- Rapid UI development
- Responsive design out-of-the-box
- Small production bundle
- Consistent design system
```

#### Infrastructure
```
Hosting: AWS EC2
- Scalable compute instances
- Multiple availability zones
- Auto-scaling capabilities (future)
- Cost-effective for startup

Web Server: Nginx
- Reverse proxy for Django
- Static file serving
- Load balancing (future)
- SSL/TLS termination
- Gzip compression

Application Server: Gunicorn
- WSGI HTTP server for Django
- Multiple worker processes
- Production-ready

Process Management: Systemd
- Service management
- Auto-restart on failure
- Log management
- Startup on boot
```

#### Payment Integration
```
M-Pesa API (Daraja API)
- STK Push (Lipa Na M-Pesa Online)
- Payment confirmation callbacks
- Transaction status queries
- Withdrawal API (B2C)

Implementation:
- django-mpesa or custom integration
- Webhook endpoints for callbacks
- Transaction logging
- Retry logic for failed payments
```

#### Sports Data API Integration
```
API-Football (Primary for MVP)
- Endpoint: api-football.com / api-sports.io
- Real-time match results and scores
- Coverage: 1000+ leagues worldwide
- Good African league coverage
- Pricing: ~$30-50/month basic plan

Implementation:
- requests library for API calls
- Cron job checks results every 30 minutes
- Match ID mapping from OCR extraction
- Result parsing and verification
- Fallback to manual review if API fails

Alternative APIs (Phase 2):
- The Odds API (multi-sport)
- SportMonks (comprehensive data)
- API-Basketball (for basketball tips)
```

#### OCR Processing
```
AWS Textract
- Extract text from bet slip screenshots
- Detect tables and structured data
- High accuracy for printed text
- Supports various image formats

boto3 (AWS SDK for Python)
- Python library for AWS services
- Textract integration
- S3 for image storage

Regex Patterns
- Parse extracted text
- Identify:
  * Bet codes
  * Odds values
  * Match names
  * Totals
  * Bookmaker names
```

#### Background Jobs
```
schedule 1.2.2 (Python library)
- Lightweight job scheduler
- No additional infrastructure needed
- Cron-like syntax

Scheduled Tasks:
1. Auto-archive tips (every 5 minutes)
   - Check tips where last_match_starts_at <= NOW()
   - Update status to 'archived'

2. Release escrow (every hour)
   - Check transactions where escrow_release_at <= NOW()
   - Transfer to tipster wallets
   - Send notifications

3. Update tipster stats (every 30 minutes)
   - Recalculate win rates
   - Update rankings
   - Award/revoke badges

4. Process pending withdrawals (manual or scheduled)
   - Check approved withdrawals
   - Initiate M-Pesa B2C
   - Update status

5. Match result checking (every 2 hours)
   - Optional: API integration with sports data provider
   - Update tip result_status

6. Send digest notifications (daily)
   - Weekly performance reports
   - Pending actions reminders

Alternative for Scale:
- Celery + Redis (when background jobs become complex)
```

#### Development Environment
```
Python Virtual Environment (venv)
- Isolated dependencies
- requirements.txt for package management

Django Management Commands
- Custom commands for:
  * Data seeding
  * Database migrations
  * Cron job execution
  * Admin utilities

Template Structure:
base.html
├── partials/
│   ├── _navbar.html
│   ├── _tip_card.html
│   ├── _filters.html
│   ├── _notification_item.html
│   └── _leaderboard_row.html
├── pages/
│   ├── home.html
│   ├── marketplace.html
│   ├── tip_detail.html
│   ├── profile.html
│   ├── dashboard.html
│   └── admin/
└── components/
    ├── _button.html
    ├── _modal.html
    └── _form_field.html

Custom Template Tags:
- {% format_currency amount %}
- {% time_until datetime %}
- {% win_rate_badge percentage %}
- {% user_avatar user %}
```

#### File Storage
```
Development: Local filesystem
Production: AWS S3
- Bet slip screenshots
- Watermarked images
- User profile pictures

django-storages
- Seamless S3 integration
- Automatic URL generation
```

#### Security & Monitoring
```
Security:
- Django security middleware (enabled by default)
- HTTPS/SSL (Let's Encrypt)
- CSRF protection
- SQL injection prevention (ORM)
- Password hashing (PBKDF2)
- Rate limiting (django-ratelimit)
- API authentication (Django REST framework tokens)

Monitoring:
- Django logging framework
- Error tracking: Sentry (optional)
- Application logs
- Nginx access logs
- Database query monitoring

Environment Variables:
- python-decouple or django-environ
- Separate settings for dev/staging/prod
- Secret key management
- API keys (M-Pesa, AWS)
```

#### API Endpoints (If needed)
```
Django REST Framework (optional for mobile app later)
- RESTful API
- Serializers for data validation
- Token authentication
- API documentation (drf-spectacular)

Potential endpoints:
- GET /api/tips (marketplace)
- POST /api/tips (create tip)
- POST /api/transactions (purchase)
- GET /api/profile/{username}
- GET /api/leaderboard
```

---

### Development Workflow

#### Local Development
```bash
1. Clone repository
2. Create virtual environment
   python -m venv venv
   source venv/bin/activate

3. Install dependencies
   pip install -r requirements.txt

4. Setup database
   python manage.py migrate

5. Create superuser
   python manage.py createsuperuser

6. Load sample data (optional)
   python manage.py seed_data

7. Run development server
   python manage.py runserver

8. Run background jobs (separate terminal)
   python manage.py run_scheduler
```

#### Database Migrations
```bash
# Create migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate app_name previous_migration_name
```

#### Deployment Process
```bash
1. Push code to Git repository
2. SSH into EC2 instance
3. Pull latest code
4. Activate virtual environment
5. Install/update dependencies
6. Run migrations
7. Collect static files
   python manage.py collectstatic --noinput
8. Restart services
   sudo systemctl restart gunicorn
   sudo systemctl restart nginx
9. Check logs
   sudo journalctl -u gunicorn -f
```

---

### Key Django Apps Structure

#### tips/models.py
```python
class Tip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tipster = models.ForeignKey(User, on_delete=models.CASCADE)
    bet_code = models.CharField(max_length=50)
    bookmaker = models.CharField(max_length=50)
    total_odds = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    screenshot = models.ImageField(upload_to='betslips/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... more fields
    
    class Meta:
        db_table = 'tips'
        indexes = [
            models.Index(fields=['status', 'first_match_starts_at']),
        ]
```

#### transactions/models.py
```python
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    escrow_status = models.CharField(max_length=20)
    # ... more fields
```

#### users/models.py (Extending Django User)
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True)
    bio = models.TextField(max_length=150, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_verified_tipster = models.BooleanField(default=False)
    # ... more fields
```

---

### Third-Party Packages

#### Essential
```txt
Django==5.0
psycopg2-binary==2.9.9  # PostgreSQL adapter
gunicorn==21.2.0  # WSGI server
python-decouple==3.8  # Environment variables
Pillow==10.1.0  # Image processing
boto3==1.34.0  # AWS SDK (Textract, S3)
schedule==1.2.2  # Background jobs
fuzzywuzzy==0.18.0  # Fuzzy string matching for team names
python-Levenshtein==0.21.1  # Faster fuzzy matching (optional speedup)
```

#### Payment & Integration
```txt
requests==2.31.0  # HTTP library for M-Pesa API and Sports API
```

#### Frontend & Templates
```txt
django-htmx==1.17.0  # HTMX integration helpers
```

#### Development
```txt
django-debug-toolbar==4.2.0  # Debug panel
black==23.12.0  # Code formatter
flake8==6.1.0  # Linting
```

#### Optional (Phase 2)
```txt
celery==5.3.4  # Advanced task queue
redis==5.0.1  # Celery broker
django-storages==1.14.2  # S3 storage backend
djangorestframework==3.14.0  # API framework
django-cors-headers==4.3.1  # CORS for API
sentry-sdk==1.39.0  # Error tracking
```

---

### Project Structure
```
tipster-marketplace/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── config/  (project settings)
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── tips/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── ocr.py  (AWS Textract integration)
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── transactions/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── mpesa.py  (M-Pesa integration)
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── withdrawals/
│   ├── disputes/
│   ├── notifications/
│   ├── leaderboard/
│   └── analytics/
│
├── templates/
│   ├── base.html
│   ├── partials/
│   └── pages/
│
├── static/
│   ├── css/
│   │   └── output.css  (Tailwind compiled)
│   ├── js/
│   │   ├── htmx.min.js
│   │   └── app.js
│   └── images/
│
├── media/  (development only)
│   ├── betslips/
│   ├── watermarked/
│   └── profiles/
│
└── scripts/
    ├── scheduler.py  (background jobs)
    └── seed_data.py  (test data)
```

---

## 6. Trust & Verification System

### Overview
The trust system is the backbone of the marketplace. It ensures buyers can confidently purchase tips and tipsters are fairly evaluated based on actual performance.

---

### 1. Result Verification Process

#### Automated Verification (PRIMARY - MVP)

**Sports Data API Integration:**
```
Recommended APIs for Kenya Market:

Option 1: API-Football (Best for Football)
- Endpoint: api-football.com
- Coverage: 1000+ leagues worldwide
- Real-time scores and results
- Pricing: ~$30-50/month for basic plan
- Supports: Match results, scores, statistics

Option 2: The Odds API
- Endpoint: the-odds-api.com
- Coverage: Multiple sports
- Real-time odds + results
- Pricing: Free tier (500 requests/month), Paid $25+/month
- Good for multi-sport coverage

Option 3: SportMonks
- Endpoint: sportmonks.com
- Comprehensive sports data
- Good African league coverage
- Pricing: ~$35-75/month

Recommendation for MVP: API-Football (focus on football first)
```

**Automated Process Flow:**
```
1. Tip Creation:
   - Tipster submits bet code
   - OCR extracts match details from screenshot
   - System parses match names, dates, times
   - Match with API data to get match IDs
   - Store match IDs + markets in tip.match_details JSON

2. Background Job (Every 30 minutes):
   - Query all tips where:
     * result_status = 'pending'
     * last_match_starts_at < NOW() - 2 hours (grace period)
   
3. For Each Pending Tip:
   - Call API with match IDs
   - Get final scores and results
   - Compare with tip selections
   - Determine if won/lost/void
   
4. Update Results:
   - Set tip.result_status = 'won' | 'lost' | 'void'
   - Set tip.result_updated_at = NOW()
   - Trigger:
     * Update tipster stats
     * Check badge criteria
     * Send buyer notification
     * Send tipster notification

5. Error Handling:
   - If API fails: Retry 3 times
   - If match not found: Flag for manual review
   - If ambiguous result: Flag for manual review
```

**Implementation Example:**
```python
# tips/result_checker.py

import requests
from django.conf import settings
from datetime import datetime, timedelta

class ResultChecker:
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.base_url = "https://v3.football.api-sports.io"
    
    def check_pending_tips(self):
        """
        Main function called by cron job
        Checks all tips pending results
        """
        from apps.tips.models import Tip
        
        # Get tips ready for result checking
        cutoff_time = datetime.now() - timedelta(hours=2)
        pending_tips = Tip.objects.filter(
            result_status='pending',
            last_match_starts_at__lt=cutoff_time,
            status='active'
        )
        
        print(f"Checking results for {pending_tips.count()} tips...")
        
        for tip in pending_tips:
            try:
                result = self.verify_tip_result(tip)
                if result:
                    tip.result_status = result['status']
                    tip.result_updated_at = datetime.now()
                    tip.save()
                    
                    # Trigger notifications
                    self.send_result_notification(tip)
                    
                    # Update stats
                    self.update_tipster_stats(tip.tipster_id)
                    
                    print(f"✓ Tip {tip.id}: {result['status']}")
                else:
                    # Flag for manual review
                    self.flag_for_manual_review(tip, "API verification failed")
                    
            except Exception as e:
                print(f"✗ Error checking tip {tip.id}: {str(e)}")
                self.flag_for_manual_review(tip, str(e))
    
    def verify_tip_result(self, tip):
        """
        Verify a single tip's result
        Returns: {'status': 'won'|'lost'|'void', 'confidence': 0-100}
        """
        match_details = tip.match_details  # JSON from OCR
        
        if not match_details:
            return None
        
        all_won = True
        any_void = False
        
        # Check each selection in the accumulator
        for selection in match_details.get('selections', []):
            match_id = selection.get('api_match_id')
            market = selection.get('market')  # e.g., "Over 2.5", "Home Win"
            
            # Get match result from API
            match_result = self.get_match_result(match_id)
            
            if not match_result:
                return None
            
            # Check if match was cancelled/postponed
            if match_result['status'] in ['CANC', 'PST', 'SUSP']:
                any_void = True
                continue
            
            # Verify selection outcome
            selection_won = self.check_selection(match_result, market)
            
            if not selection_won:
                all_won = False
                break  # One loss means entire accumulator lost
        
        # Determine final status
        if any_void:
            return {'status': 'void', 'confidence': 100}
        elif all_won:
            return {'status': 'won', 'confidence': 100}
        else:
            return {'status': 'lost', 'confidence': 100}
    
    def get_match_result(self, match_id):
        """
        Fetch match result from API
        """
        headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        
        url = f"{self.base_url}/fixtures"
        params = {'id': match_id}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['results'] > 0:
                return data['response'][0]
        
        return None
    
    def check_selection(self, match_result, market):
        """
        Check if a specific market selection won
        Examples: "Over 2.5", "Home Win", "BTTS Yes"
        """
        fixture = match_result['fixture']
        goals = match_result['goals']
        score = match_result['score']
        
        home_score = goals['home']
        away_score = goals['away']
        total_goals = home_score + away_score
        
        # Parse market and check outcome
        if "Over" in market:
            threshold = float(market.split()[1])
            return total_goals > threshold
        
        elif "Under" in market:
            threshold = float(market.split()[1])
            return total_goals < threshold
        
        elif "Home Win" in market or "1" == market:
            return home_score > away_score
        
        elif "Away Win" in market or "2" == market:
            return away_score > home_score
        
        elif "Draw" in market or "X" == market:
            return home_score == away_score
        
        elif "BTTS" in market:
            if "Yes" in market:
                return home_score > 0 and away_score > 0
            else:  # BTTS No
                return home_score == 0 or away_score == 0
        
        # Add more market types as needed
        # If market not recognized, flag for manual review
        return None
    
    def flag_for_manual_review(self, tip, reason):
        """
        Flag tip for admin manual verification
        """
        from apps.tips.models import ManualReviewQueue
        
        ManualReviewQueue.objects.create(
            tip=tip,
            reason=reason,
            flagged_at=datetime.now()
        )
        
        # Send admin notification
        self.notify_admin_manual_review(tip, reason)
```

**Cron Job Setup:**
```python
# scripts/scheduler.py

import schedule
import time
from apps.tips.result_checker import ResultChecker

def check_results():
    checker = ResultChecker()
    checker.check_pending_tips()

def run_scheduler():
    # Check results every 30 minutes
    schedule.every(30).minutes.do(check_results)
    
    # Also check at specific times (after major leagues finish)
    schedule.every().day.at("23:00").do(check_results)  # After EPL evening games
    schedule.every().day.at("01:00").do(check_results)  # After late games
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

#### Manual Review Queue (FALLBACK ONLY)

**When Manual Review Is Needed:**
```
Automatic flagging for manual review when:
1. API cannot find match (match_id not matched)
2. API returns ambiguous result
3. Exotic markets not supported by parser
4. API is down/unavailable
5. Tipster or buyer disputes automated result

Manual Review Queue Dashboard:
- Admin sees flagged tips
- Can manually mark as won/lost/void
- Notes field for reasoning
- Audit trail of all manual changes
```

**Admin Dashboard - Manual Review Section:**
```
Pending Manual Review (3 tips):

Tip #1234
Tipster: @ProTips254
Reason: "Market type not recognized: Asian Handicap -1.5"
Match: Man United vs Chelsea
Screenshot: [View]
[Mark as Won] [Mark as Lost] [Mark as Void]

Tip #5678
Tipster: @BetKing_KE
Reason: "API match not found: Gor Mahia vs AFC Leopards"
Match: Kenyan Premier League
Screenshot: [View]
[Verify Manually] - Opens bookmaker link to check
```

#### OCR Enhancement for Match Matching

**Match Parsing from Screenshots:**
```python
# tips/ocr.py

import boto3
import re
from datetime import datetime

class BetslipOCR:
    def __init__(self):
        self.textract = boto3.client('textract')
    
    def extract_matches(self, screenshot_url):
        """
        Extract match details from betslip screenshot
        Returns structured data for API matching
        """
        # Call AWS Textract
        text = self.extract_text(screenshot_url)
        
        # Parse structured data
        matches = self.parse_matches(text)
        
        return matches
    
    def parse_matches(self, text):
        """
        Parse match names and markets from extracted text
        """
        matches = []
        
        # Common patterns in betslips
        patterns = {
            'match': r'([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)',
            'odds': r'(\d+\.\d{2})',
            'total_odds': r'Total Odds[:\s]+(\d+\.\d{2})',
            'bet_code': r'Code[:\s]+([A-Z0-9]+)'
        }
        
        # Extract all matches
        match_pattern = re.finditer(patterns['match'], text)
        
        for match in match_pattern:
            home_team = match.group(1).strip()
            away_team = match.group(2).strip()
            
            matches.append({
                'home_team': home_team,
                'away_team': away_team,
                'match_name': f"{home_team} vs {away_team}"
            })
        
        # Extract bet code
        code_match = re.search(patterns['bet_code'], text)
        bet_code = code_match.group(1) if code_match else None
        
        # Extract total odds
        odds_match = re.search(patterns['total_odds'], text)
        total_odds = float(odds_match.group(1)) if odds_match else None
        
        return {
            'matches': matches,
            'bet_code': bet_code,
            'total_odds': total_odds,
            'selection_count': len(matches)
        }
    
    def match_with_api(self, extracted_matches):
        """
        Match extracted team names with API match IDs
        Uses fuzzy matching for team name variations
        """
        from fuzzywuzzy import fuzz
        
        matched_selections = []
        
        for match in extracted_matches:
            # Search API for this match (today and tomorrow)
            api_matches = self.search_api_matches(
                match['home_team'], 
                match['away_team']
            )
            
            # Find best match using fuzzy string matching
            best_match = None
            best_score = 0
            
            for api_match in api_matches:
                score = fuzz.ratio(
                    match['match_name'].lower(),
                    f"{api_match['home']} vs {api_match['away']}".lower()
                )
                
                if score > best_score:
                    best_score = score
                    best_match = api_match
            
            if best_score > 80:  # 80% confidence threshold
                matched_selections.append({
                    'extracted_name': match['match_name'],
                    'api_match_id': best_match['id'],
                    'api_match_name': f"{best_match['home']} vs {best_match['away']}",
                    'match_date': best_match['date'],
                    'confidence': best_score
                })
            else:
                # Could not match - flag for manual review
                matched_selections.append({
                    'extracted_name': match['match_name'],
                    'api_match_id': None,
                    'error': 'No confident match found',
                    'confidence': best_score
                })
        
        return matched_selections
```

**Market Detection from Screenshot:**
```python
def detect_markets(text, matches):
    """
    Detect what markets were selected (Over/Under, BTTS, 1X2, etc.)
    This is challenging and may require manual input
    """
    markets = []
    
    # Look for common market keywords
    market_keywords = {
        'over': r'Over\s+(\d+\.?\d*)',
        'under': r'Under\s+(\d+\.?\d*)',
        'btts': r'BTTS|Both Teams To Score',
        'home_win': r'1|Home Win',
        'away_win': r'2|Away Win',
        'draw': r'X|Draw'
    }
    
    # Parse markets (this is complex and may need refinement)
    # For MVP, may need tipster to confirm/select markets
    
    return markets
```

#### Hybrid Approach (RECOMMENDED FOR MVP)

**Combine Automated + Manual:**
```
Step 1: OCR extracts match names
Step 2: Tipster verifies and selects markets from dropdown
        (since OCR might not accurately detect "Over 2.5" vs "Over 3.5")
Step 3: System matches with API data
Step 4: After matches complete, automated result checking

Tipster Verification Screen:
┌─────────────────────────────────────────┐
│ Verify Extracted Information           │
├─────────────────────────────────────────┤
│ ✓ Bet Code: RSCEHO                     │
│ ✓ Total Odds: 47.35                    │
│ ✓ Bookmaker: SportPesa                 │
│                                         │
│ Match 1: Man United vs Chelsea          │
│ Market: [Select] ▼                      │
│   - Over 2.5 Goals                      │
│   - Under 2.5 Goals                     │
│   - BTTS Yes                            │
│   - Home Win                            │
│   ...                                   │
│                                         │
│ Match 2: Barcelona vs Real Madrid       │
│ Market: [Select] ▼                      │
│                                         │
│ [Confirm & Submit]                      │
└─────────────────────────────────────────┘
```

This approach:
- ✅ Reduces manual work (OCR does heavy lifting)
- ✅ Ensures accuracy (tipster confirms markets)
- ✅ Enables full automation (once data is verified)
- ✅ Scales well (once submitted, everything is automatic)



---

### 2. Win Rate Calculation

#### Formula
```
Win Rate = (Total Won Tips / Total Resulted Tips) × 100

Where:
- Total Won Tips = Tips where result_status = 'won'
- Total Resulted Tips = Tips where result_status IN ('won', 'lost')
- Excludes: Pending tips, Void tips, Rejected tips

Example:
Tipster has posted 100 tips:
- Won: 68
- Lost: 27
- Pending: 3
- Void: 2

Win Rate = (68 / (68 + 27)) × 100 = 71.58%
```

#### Time Period Filters
```
Calculate win rate for different periods:

Last 7 Days:
- Only tips where result_updated_at >= NOW() - 7 days

Last 30 Days (Default Display):
- Only tips where result_updated_at >= NOW() - 30 days

Last 90 Days:
- Only tips where result_updated_at >= NOW() - 90 days

All Time:
- All resulted tips regardless of date

Minimum Requirement:
- Show "Insufficient Data" if resulted tips < 10
- Prevents misleading stats (e.g., 100% with only 2 tips)
```

#### Display Logic
```python
def calculate_win_rate(tipster_id, days=30):
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    tips = Tip.objects.filter(
        tipster_id=tipster_id,
        result_status__in=['won', 'lost'],
        result_updated_at__gte=cutoff_date
    )
    
    total_resulted = tips.count()
    total_won = tips.filter(result_status='won').count()
    
    if total_resulted < 10:
        return {
            'win_rate': None,
            'total_tips': total_resulted,
            'message': 'Insufficient data (min 10 tips required)'
        }
    
    win_rate = (total_won / total_resulted) * 100
    
    return {
        'win_rate': round(win_rate, 2),
        'total_won': total_won,
        'total_lost': total_resulted - total_won,
        'total_tips': total_resulted
    }
```

---

### 3. ROI (Return on Investment) Calculation

#### Formula
```
ROI = ((Total Profit - Total Cost) / Total Cost) × 100

Where:
- Total Cost = Sum of all tip prices purchased
- Total Profit = (Number of Won Tips × Average Stake × Average Odds) - Total Cost
- Assumes flat stake betting (e.g., 100 KES per tip)

Simplified for Display:
ROI = ((Won Tips × Avg Odds) - Total Tips) / Total Tips × 100

Example:
Tipster with 30 resulted tips:
- 21 Won (average odds: 5.0x)
- 9 Lost
- ROI = ((21 × 5.0) - 30) / 30 × 100 = +250%

This means: For every 100 KES stake across all tips, profit is 250 KES
```

#### Implementation
```python
def calculate_roi(tipster_id, days=30):
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    tips = Tip.objects.filter(
        tipster_id=tipster_id,
        result_status__in=['won', 'lost'],
        result_updated_at__gte=cutoff_date
    )
    
    total_tips = tips.count()
    if total_tips < 10:
        return None
    
    won_tips = tips.filter(result_status='won')
    
    # Calculate weighted return
    total_return = sum(tip.total_odds for tip in won_tips)
    
    # ROI formula
    roi = ((total_return - total_tips) / total_tips) * 100
    
    return round(roi, 2)
```

#### Display Guidelines
```
Positive ROI (+): Green color, good performance
Zero ROI (0): Yellow/neutral color
Negative ROI (-): Red color, poor performance

Display format:
+125% → Excellent (making profit)
+15% → Good (profitable)
0% → Break even
-20% → Poor (losing)
```

---

### 4. Badge System

#### Badge Definitions

##### A. Performance Badges (Auto-Awarded)

**🏆 Top Performer**
```
Criteria:
- Win rate ≥ 70%
- Minimum 30 resulted tips (last 30 days)
- Active account (posted tip in last 7 days)

Check Frequency: Daily

Removal:
- Win rate drops below 65%
- Or inactive for 14 days
```

**⚡ Quick Seller**
```
Criteria:
- Total tips sold ≥ 50 (all time)

Check Frequency: After each sale

Removal:
- Never removed (milestone badge)
```

**🔥 Hot Streak**
```
Criteria:
- 10 consecutive won tips (no losses in between)
- All tips must be resulted (not pending)

Check Frequency: After each result update

Removal:
- Streak broken by a loss
- Shows highest streak achieved
```

**⭐ Rising Star**
```
Criteria:
- Account created < 30 days ago
- Win rate ≥ 80%
- Minimum 10 resulted tips

Check Frequency: Daily

Removal:
- Account age > 30 days (auto-transitions to other badges)
```

**💎 Consistent**
```
Criteria:
- 90% or more tips have results (not stuck in pending)
- Minimum 20 tips posted

Check Frequency: Weekly

Removal:
- Pending ratio increases above 20%
```

**🎯 Specialist**
```
Criteria:
- 70%+ win rate in a specific sport
- Minimum 20 tips in that sport
- Display sport name with badge

Examples:
- 🎯 Football Specialist
- 🎯 Basketball Specialist

Check Frequency: Weekly

Removal:
- Win rate drops below 60% in that sport
```

##### B. Verification Badges (Admin-Awarded)

**✅ Verified Tipster**
```
Criteria (Admin Review):
- Identity verification completed
- Phone number verified
- At least 20 tips posted
- Win rate ≥ 60%
- No disputes or fraud flags
- Active for 30+ days

Benefits:
- Auto-publish enabled (no approval needed)
- Higher visibility in marketplace
- Trust indicator for buyers

Revocation:
- Fraud detected
- Multiple disputes
- Terms violation
```

**💼 Professional**
```
Criteria (Manual Award):
- Paid subscription to premium tier
- Or admin recognizes exceptional quality

Benefits:
- Priority support
- Featured listings discount
- Custom profile badge color
```

#### Badge Display Priority
```
Profile Badge Order (Max 3 shown):
1. ✅ Verified Tipster (if applicable)
2. 🏆 Top Performer (if applicable)
3. 🔥 Hot Streak OR ⭐ Rising Star
4. Other badges (shown in "View All" modal)
```

---

### 5. Tipster Statistics Dashboard

#### Key Metrics (Auto-Calculated)

```python
# Stored in tipster_stats table, updated every 30 minutes

class TipsterStats:
    # Performance
    total_tips: int              # All posted tips
    tips_won: int                # Won tips
    tips_lost: int               # Lost tips
    tips_pending: int            # Awaiting results
    tips_void: int               # Cancelled/void
    win_rate: float              # Percentage (2 decimals)
    roi: float                   # Percentage (2 decimals)
    average_odds: float          # Mean odds across all tips
    
    # Sales
    total_sold: int              # Number of purchases
    total_revenue: float         # KES earned (after commission)
    average_price: float         # Mean tip price
    conversion_rate: float       # (sold / views) × 100
    
    # Engagement
    total_views: int             # Tip detail page views
    unique_buyers: int           # Count distinct buyers
    repeat_buyers: int           # Buyers who purchased 2+ tips
    
    # Streaks
    current_win_streak: int      # Ongoing consecutive wins
    longest_win_streak: int      # Best streak ever
    current_loss_streak: int     # Ongoing consecutive losses (warning sign)
    
    # Rankings
    rank_by_winrate: int         # Position in win rate leaderboard
    rank_by_earnings: int        # Position in earnings leaderboard
    
    # Freshness
    last_tip_posted_at: datetime # When last tip was posted
    last_result_updated_at: datetime  # When last result was verified
    
    # Calculation period
    calculation_period: str      # 'last_30_days'
    last_calculated_at: datetime # Cache timestamp
```

#### Update Trigger Events
```
Stats recalculated when:
1. New tip posted
2. Tip result updated (won/lost)
3. Tip purchased
4. Scheduled cron job (every 30 minutes)

Immediate updates (no delay):
- Total sold (after purchase)
- Total revenue (after escrow release)

Delayed updates (cron job):
- Win rate (after result verification)
- Rankings (after all tipsters updated)
```

---

### 6. Anti-Fraud Measures

#### Detection Systems

**A. Fake Screenshot Detection**
```
Basic Checks (MVP):
- Verify file is valid image
- Check image dimensions (not too small)
- Verify upload timestamp (recent)
- Admin manual review for new users

Advanced (Phase 2):
- Image metadata analysis
- Detect photoshop/edit markers
- OCR consistency checks
- Reverse image search (check if stolen)
```

**B. Code Verification**
```
Admin Tools:
- Test bet code in actual bookmaker
- Verify odds match screenshot
- Check number of selections
- Flag mismatches for review

Automated (Phase 2):
- API integration with bookmakers
- Auto-verify codes before approval
- Flag invalid codes
```

**C. Result Manipulation Prevention**
```
Rules:
1. Only admin can mark results (tipsters can't)
2. Results locked after 48 hours (prevent tampering)
3. Audit log for all result changes
4. Buyers can dispute incorrect results

Admin Alerts:
- Tipster with 100% win rate (suspicious)
- Sudden drop in win rate (possible account sale)
- Multiple rejected tips (pattern)
- High dispute rate (fraud indicator)
```

**D. Multi-Account Detection**
```
Track:
- IP addresses
- Device fingerprints
- Phone numbers
- M-Pesa numbers
- Posting patterns

Flags:
- Same IP posting from multiple accounts
- Same M-Pesa number on multiple accounts
- Coordinated fake purchases (wash trading)
```

**E. Sybil Attack Prevention**
```
New Account Restrictions:
- Manual approval for first 10 tips
- Cannot post more than 3 tips per day initially
- Phone verification required
- Cannot withdraw until 10 tips sold

Trust Building:
- Auto-publish unlocked after:
  * 20+ tips posted
  * 60%+ win rate
  * No disputes
  * Admin approval
```

---

### 7. Trust Score Algorithm (Optional - Phase 2)

```python
def calculate_trust_score(tipster_id):
    """
    Trust Score: 0-100 points
    Higher = More trustworthy
    """
    score = 0
    
    # Win Rate (0-30 points)
    win_rate = get_win_rate(tipster_id)
    if win_rate >= 70:
        score += 30
    elif win_rate >= 60:
        score += 20
    elif win_rate >= 50:
        score += 10
    
    # Volume (0-20 points)
    total_tips = get_total_tips(tipster_id)
    if total_tips >= 100:
        score += 20
    elif total_tips >= 50:
        score += 15
    elif total_tips >= 20:
        score += 10
    
    # Account Age (0-15 points)
    account_age_days = get_account_age(tipster_id)
    if account_age_days >= 180:
        score += 15
    elif account_age_days >= 90:
        score += 10
    elif account_age_days >= 30:
        score += 5
    
    # Sales Performance (0-15 points)
    total_sold = get_total_sold(tipster_id)
    if total_sold >= 100:
        score += 15
    elif total_sold >= 50:
        score += 10
    elif total_sold >= 20:
        score += 5
    
    # Verification Status (0-10 points)
    if is_verified(tipster_id):
        score += 10
    
    # Dispute Rate (0-10 points, negative impact)
    dispute_rate = get_dispute_rate(tipster_id)
    if dispute_rate == 0:
        score += 10
    elif dispute_rate < 0.05:  # <5%
        score += 5
    elif dispute_rate > 0.20:  # >20%
        score -= 10  # Penalty
    
    return max(0, min(100, score))  # Clamp between 0-100
```

#### Trust Score Display
```
90-100: ⭐⭐⭐⭐⭐ Excellent
75-89:  ⭐⭐⭐⭐ Very Good
60-74:  ⭐⭐⭐ Good
40-59:  ⭐⭐ Average
0-39:   ⭐ New/Unproven
```

---

### 8. Data Freshness & Update Schedule

#### Cron Jobs Schedule

```python
# scheduler.py

import schedule
import time

def run_scheduler():
    # Every 5 minutes
    schedule.every(5).minutes.do(auto_archive_tips)
    
    # Every 30 minutes - PRIMARY RESULT CHECKING
    schedule.every(30).minutes.do(check_match_results)  # Automated API verification
    schedule.every(30).minutes.do(update_tipster_stats)
    schedule.every(30).minutes.do(award_badges)
    
    # Every hour
    schedule.every().hour.do(release_escrow)
    schedule.every().hour.do(check_pending_withdrawals)
    
    # After major leagues typically finish (for immediate updates)
    schedule.every().day.at("23:00").do(check_match_results)  # After EPL evening games
    schedule.every().day.at("01:00").do(check_match_results)  # After late European games
    schedule.every().day.at("06:00").do(check_match_results)  # After Asian leagues
    
    # Daily at 2 AM
    schedule.every().day.at("02:00").do(update_leaderboards)
    schedule.every().day.at("02:00").do(calculate_trust_scores)
    schedule.every().day.at("02:00").do(send_daily_summaries)
    
    # Weekly on Monday at 3 AM
    schedule.every().monday.at("03:00").do(archive_old_notifications)
    schedule.every().monday.at("03:00").do(clean_expired_sessions)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    run_scheduler()
```

#### Real-Time Updates (HTMX)
```
Components that update without page reload:
- Notification bell (every 30 seconds)
- Tip countdown timers (every minute)
- Live leaderboard (when user on page)
- Wallet balance (after transactions)
- Tip status changes (after admin actions)
```

---

### 9. Transparency Features

#### Public Stats Page
```
/tipster/{username}/stats

Display:
- Win rate chart (last 90 days)
- Tips posted per week
- Average odds trend
- Best performing sport
- Worst performing sport
- Revenue graph (if tipster opts in)
- Badge history
- Recent tips (last 10)
```

#### Result History
```
Every tip shows:
- Date posted
- Date resulted
- Actual result (Won/Lost)
- Number of purchases
- Buyer reviews (Phase 2)

Builds transparency and trust
```

#### Admin Transparency
```
Admin Actions Log (visible to affected users):
- "Tip approved by Admin on [date]"
- "Result marked as Won by Admin on [date]"
- "Badge awarded: Top Performer on [date]"
- "Account verified on [date]"
```

---

### 10. Implementation Checklist

**MVP (Phase 1):**
- [x] **Automated result verification via API** (API-Football integration)
- [x] Manual review queue (fallback for unmatched/ambiguous results)
- [x] Hybrid OCR + tipster verification (extract matches, tipster confirms markets)
- [x] Win rate calculation (30-day window)
- [x] Basic badges (Top Performer, Quick Seller, Rising Star)
- [x] Admin approval for new tipsters
- [x] Screenshot required for all tips
- [x] Basic stats dashboard
- [x] Fraud detection (admin review for flagged tips)
- [x] Result checking cron job (every 30 minutes)

**Phase 2 Enhancements:**
- [ ] Advanced OCR (fully automatic market detection)
- [ ] Multiple sports API integration (basketball, tennis, etc.)
- [ ] ROI calculation and prominent display
- [ ] Advanced badges (Hot Streak, Specialist, Consistent)
- [ ] Trust score algorithm (0-100 points)
- [ ] Multi-account detection (IP tracking, device fingerprints)
- [ ] Image forensics (detect photoshopped screenshots)
- [ ] Buyer reviews/ratings system
- [ ] Detailed analytics graphs (performance over time)
- [ ] Transparent public stats page per tipster
- [ ] Dispute automated resolution suggestions

---

## 7. Payment & Monetization

### Payment Integration
```
Primary Method: M-Pesa (MVP)
- STK Push integration
- Instant payment confirmation
- Transaction fees: [TBD - typically 1-3%]
```

### Refund & Dispute Policy ✅

**Full Refund (100%)**
Issued for:
- Invalid/expired bet code (code doesn't load at all)
- Code loads completely wrong matches
- Significantly wrong information (odds differ by >20%)
- Technical error on platform side

**Partial Refund (80% to buyer, 20% platform admin fee)**
Issued for:
- Minor discrepancies (odds differ by <20%)
- Code works but one match already started
- Incorrect number of selections (buyer can still use it)

**No Refund**
Applied when:
- Code works perfectly but bet loses (buyer took betting risk)
- Buyer changes mind after code is revealed
- All matches already started when purchased (buyer's responsibility to check)
- Buyer claims they "didn't like" the selections

### Dispute Process

**Dispute Window:**
- Buyers have 30 minutes after purchase to report issues
- OR until first match starts (whichever comes first)
- No disputes accepted after matches begin

**How to Dispute:**
```
1. Buyer clicks "Report Issue" in My Purchases
2. Selects issue type:
   - Code doesn't work
   - Wrong information
   - Technical error
3. Upload proof (screenshot of error)
4. Submit for review
```

**Admin Review Process:**
```
1. Admin receives dispute notification
2. Reviews buyer's evidence
3. Verifies bet code in bookmaker
4. Checks tipster's original submission
5. Decision within 2 hours (during business hours)
6. Refund processed automatically if approved
```

**Tipster Accountability:**
- Invalid code = Automatic suspension pending review
- 3 invalid codes = Permanent ban
- Rating automatically drops on each dispute
- Funds held in escrow until dispute resolved

**Buyer Protection:**
- Screenshot of purchase confirmation
- Transaction ID for all payments
- Dispute history tracked
- Watermarked downloads as proof of purchase

### Revenue Split Model ✅

**Commission Structure: 60/40 Split**
```
Tipster: 60%
Platform: 40%

Example Transaction (KES 200 tip):
1. Buyer pays: KES 200
2. M-Pesa fee (~1.5%): KES 3 (Platform absorbs)
3. Net amount: KES 197
4. Split:
   • Tipster receives: KES 118 (60%)
   • Platform receives: KES 79 (40%)
```

**Payment Processing Fees:**
- Platform absorbs all M-Pesa transaction fees
- Transparent pricing for buyers
- Simpler UX (no hidden fees)

**For Free Tips (KES 0):**
- No transaction occurs
- No commission taken
- Helps new tipsters build reputation
- Benefits platform through user growth

### Payout System ✅

**Escrow Period: 48 Hours**
```
Timeline:
Purchase → Money held 48 hours → Auto-release to tipster wallet

Escrow holds until:
- 48 hours after last match in accumulator
- Dispute window closes
- Ensures bet code worked properly
```

**Minimum Payout Threshold:**
```
Default: KES 500 (Adjustable by admin)

How it works:
- Tipster earnings accumulate in wallet
- Withdrawal available when balance ≥ threshold
- Reduces transaction fees
- Admin can adjust threshold as needed

Tipster Dashboard shows:
• Available Balance: KES 1,250
• Pending (in escrow): KES 450
• Total Earned: KES 5,680
[Withdraw] button (enabled when ≥ KES 500)
```

**Payout Process:**
```
1. Tipster requests withdrawal
2. Enters M-Pesa number
3. Admin approves (or auto-approve for trusted users)
4. M-Pesa transfer initiated
5. Confirmation sent to tipster
6. Withdrawal fee (if any): [TBD]
```

### Future Revenue Streams 💡

**Phase 2+ Opportunities:**

1. **Featured Listings**
   - Tipsters pay KES 200-500 to feature tip at top
   - 24-hour featured placement
   - "Sponsored" badge shown

2. **Verified Tipster Badge**
   - Monthly subscription: KES 500
   - Blue checkmark badge
   - Higher visibility in search
   - Priority customer support

3. **Premium Tipster Tiers**
   ```
   Free Tier: 60/40 split
   Bronze (KES 1,000/month): 65/35 split + verified badge
   Silver (KES 2,500/month): 70/30 split + featured weekly
   Gold (KES 5,000/month): 75/25 split + priority support
   ```

4. **Bookmaker Affiliate Commissions**
   - Partner with SportPesa, Betika, etc.
   - Earn commission when users sign up via platform
   - Track via referral links/codes

5. **Advertising Space**
   - Banner ads from bookmakers
   - Sponsored tips from betting companies
   - Native advertising

6. **Premium Buyer Subscriptions**
   - Monthly fee for unlimited access
   - Discount on all tips
   - Early access to top tipsters

7. **Tipster Analytics Dashboard (Premium)**
   - Advanced stats and insights
   - Performance tracking tools
   - KES 300/month for tipsters

8. **Tip Packages**
   - Tipsters bundle multiple tips
   - Weekend specials, month passes
   - Platform takes same 40% cut

**Priority for Phase 2:**
1. Featured listings (easiest to implement, immediate revenue)
2. Verified badges (recurring revenue)
3. Bookmaker affiliates (high potential, no user cost)
4. Premium tiers (when user base grows)

---

## 8. Legal & Compliance

### Overview
Operating a tips marketplace in Kenya requires compliance with gambling regulations, data protection laws, and consumer protection standards. While the platform doesn't directly facilitate betting, it deals with betting-related content and must navigate regulatory requirements carefully.

---

### 1. Kenya Regulatory Framework

#### Betting Control and Licensing Board (BCLB)

**Regulatory Uncertainty:**
```
CRITICAL QUESTION: Does a tips marketplace require a license?

The platform is NOT:
- A bookmaker (doesn't accept bets)
- A betting operator (doesn't facilitate gambling)
- A gambling website (doesn't host games)

The platform IS:
- A marketplace for information/predictions
- A content platform (user-generated tips)
- A payment facilitator (between tipsters and buyers)

RECOMMENDATION:
1. Seek legal counsel from Kenya gambling law specialist
2. Apply for clarification letter from BCLB
3. Potentially classify as "betting advisory service"
4. May need license or registration with BCLB

Contact BCLB:
- Website: bclb.go.ke
- Email: info@bclb.go.ke
- Phone: +254 20 221 1909
- Location: Nairobi, Kenya
```

**Possible License Requirements:**
```
If BCLB determines licensing is needed:

Betting Advisory License (if such category exists):
- Application fee: KES 50,000 - 200,000 (estimated)
- Annual license fee: KES 100,000 - 500,000 (estimated)
- Processing time: 3-6 months
- Requirements:
  * Business registration
  * Tax compliance certificate
  * Background checks on directors
  * Business plan
  * Proof of capital
  * Responsible gambling measures
  * AML/CFT compliance plan

NOTE: These are estimates - actual requirements TBD by BCLB
```

#### Alternative: Operate as Information Service
```
If no gambling license needed:

Register as:
- Digital Content Platform
- Information Service Provider
- Online Marketplace

Advantages:
- Lower regulatory burden
- Faster to launch
- Lower costs

Risks:
- Regulatory changes
- Potential shutdown if BCLB objects
- Gray area legally

MITIGATION:
- Obtain legal opinion
- Get clarification from BCLB
- Have "pivot plan" ready
- Strong disclaimers
```

---

### 2. Business Registration

#### Required Registrations

**A. Business Registration (Mandatory)**
```
Register with Business Registration Service (BRS):

Options:
1. Sole Proprietorship
   - Cheapest (~KES 5,000)
   - Personal liability
   - Quick setup

2. Limited Liability Company (Recommended)
   - KES 10,000 - 15,000
   - Limited liability protection
   - More credible to partners
   - Better for fundraising

Process:
1. Reserve company name (eCitizen portal)
2. Prepare incorporation documents
3. Submit to Registrar of Companies
4. Receive Certificate of Incorporation
5. Timeline: 7-14 days

Documents needed:
- ID copies of directors
- Memorandum & Articles of Association
- CR12 form (particulars of directors)
- Registered office address
```

**B. PIN Registration (Tax)**
```
KRA PIN (Personal/Business):
- Free registration
- Online via iTax portal
- Required for all business operations

VAT Registration (if turnover > KES 5M/year):
- Register once revenue threshold reached
- 16% VAT on services
- Monthly/quarterly returns
```

**C. Nairobi City County License**
```
Single Business Permit:
- Required if physical office in Nairobi
- Cost: KES 10,000 - 30,000/year (depending on category)
- Renewable annually
- Apply via county portal

For online-only business:
- May not need physical permit
- Check with county authorities
```

---

### 3. Terms of Service (ToS)

#### Essential Clauses

**A. Platform Description**
```
Clearly state:
- Platform is a marketplace for betting tips/predictions
- Platform does NOT operate as a bookmaker
- Platform does NOT place bets on behalf of users
- Platform facilitates information exchange only
- Tips are opinions, not guaranteed outcomes
```

**B. User Eligibility**
```
Must include:
- Users must be 18+ years old
- Users must comply with local gambling laws
- Platform reserves right to verify age
- Restricted jurisdictions (if any)
- Right to refuse service
```

**C. Disclaimer of Liability**
```
CRITICAL - Include:
"The Platform provides a marketplace for betting tips and predictions. 
All tips are user-generated opinions and NOT guarantees. Users 
acknowledge that:

1. Betting involves financial risk
2. Past performance does not guarantee future results
3. Users are responsible for their own betting decisions
4. Platform is not liable for losses incurred
5. Tips should not be considered professional advice
6. Users should only bet what they can afford to lose

BY USING THIS PLATFORM, YOU ACCEPT ALL RISKS ASSOCIATED WITH 
BETTING AND WAIVE ANY CLAIMS AGAINST THE PLATFORM FOR LOSSES."
```

**D. Tipster Obligations**
```
Tipsters agree to:
- Provide genuine, honest tips
- Not manipulate results
- Not upload fraudulent screenshots
- Not operate multiple accounts
- Comply with platform policies
- Accept platform commission structure
```

**E. Payment Terms**
```
Clearly state:
- Commission rates (60/40 split)
- Escrow period (48 hours)
- Refund policy
- Withdrawal terms
- Minimum payout threshold
- Platform fees (if any)
- Dispute resolution process
```

**F. Intellectual Property**
```
Define ownership:
- User content remains user property
- Platform has license to display/distribute
- Users grant perpetual license to platform
- Platform owns source code, design, branding
```

**G. Prohibited Activities**
```
Explicitly ban:
- Match-fixing information
- Fraudulent tips
- Money laundering
- Underage access
- Multi-accounting for manipulation
- Harassment of other users
- Spam or automated posting
```

**H. Termination Rights**
```
Platform can:
- Suspend/ban accounts for violations
- Withhold payments for fraud
- Terminate service with notice
- Modify terms with 30 days notice
```

**I. Dispute Resolution**
```
Specify:
- Internal dispute process (30-minute window)
- Admin final decision authority
- Arbitration clause (Kenya law)
- Jurisdiction: Kenya courts
- Governing law: Laws of Kenya
```

**J. Limitation of Liability**
```
Platform not liable for:
- User losses from betting
- Third-party actions (bookmakers, payment providers)
- Service interruptions
- Data loss
- Consequential or indirect damages

Maximum liability: Amount paid by user to platform (past 12 months)
```

---

### 4. Privacy Policy (GDPR-Style + Kenya DPA)

#### Kenya Data Protection Act 2019 Compliance

**A. Data Controller Registration**
```
Register with Office of Data Protection Commissioner:
- Required if processing personal data
- Fee: KES 5,000 - 20,000/year
- Online registration: odpc.go.ke
- Annual data protection impact assessment
- Appoint Data Protection Officer (if >10 employees)
```

**B. Privacy Policy Must Include:**

```
1. Data Collection:
   What we collect:
   - Phone numbers (for login, M-Pesa)
   - Email addresses
   - Usernames
   - Transaction history
   - IP addresses
   - Device information
   - Uploaded screenshots
   - Browsing behavior

2. Purpose of Processing:
   - User authentication
   - Payment processing
   - Service delivery
   - Fraud prevention
   - Analytics and improvement
   - Legal compliance

3. Legal Basis (Kenya DPA):
   - Consent (users accept ToS)
   - Contract performance (service delivery)
   - Legal obligation (tax, AML)
   - Legitimate interest (fraud prevention)

4. Data Sharing:
   We share data with:
   - Payment processors (M-Pesa/Safaricom)
   - Cloud services (AWS)
   - Analytics providers
   - Legal authorities (when required)
   
   We DO NOT sell personal data.

5. Data Retention:
   - Active accounts: Indefinite
   - Closed accounts: 7 years (tax compliance)
   - Transaction records: 7 years
   - Marketing data: Until consent withdrawn

6. User Rights (Kenya DPA):
   Users can:
   - Access their data (data portability)
   - Correct inaccurate data
   - Delete data (right to be forgotten)*
   - Withdraw consent
   - Object to processing
   - Lodge complaint with ODPC
   
   *Exceptions: Legal obligations, active disputes

7. Security Measures:
   - Encryption (HTTPS, database)
   - Access controls
   - Regular security audits
   - Incident response plan
   - Data breach notification (within 72 hours)

8. International Transfers:
   - Data stored on AWS (may be outside Kenya)
   - Adequate safeguards in place
   - EU-US Privacy Shield compliance (if applicable)

9. Cookies:
   - Session cookies (essential)
   - Analytics cookies (optional)
   - Cookie consent mechanism

10. Contact:
    Data Protection Officer: dpo@yourplatform.com
    Office: [Physical address]
```

---

### 5. Age Verification & Responsible Gambling

#### Age Verification (18+)

**Implementation Requirements:**
```
MANDATORY:
- Prominent 18+ warning on homepage
- Age confirmation checkbox during registration
- "I confirm I am 18 years or older" declaration
- Block registration if declined

RECOMMENDED (Phase 2):
- ID verification via IPRS (Integrated Population Registration System)
- Phone number verification (links to registered adult)
- Facial recognition age estimation
- Document upload (ID/Passport)

Penalties for non-compliance:
- Legal liability if minors access platform
- Potential license revocation
- Reputational damage
```

#### Responsible Gambling Measures

**Must-Have Features:**
```
1. Gambling Addiction Resources:
   - Link to National Authority for the Campaign Against Alcohol and Drug Abuse (NACADA)
   - Helpline: 1192 (toll-free in Kenya)
   - Self-exclusion option
   - Reality checks (time spent on platform)

2. Risk Warnings:
   Prominent display:
   "⚠️ WARNING: Gambling can be addictive. Only bet what you can afford to lose."
   
   On every tip:
   "This is a prediction, not a guarantee. Bet responsibly."

3. Limits (Optional but good practice):
   - Daily purchase limits for buyers
   - Cooling-off periods
   - Self-exclusion mechanism
   - Deposit limits

4. Education:
   - Blog posts on responsible gambling
   - Understanding odds
   - Bankroll management tips
   - Warning signs of addiction
```

---

### 6. Anti-Money Laundering (AML) & Counter-Terrorist Financing (CTF)

#### Proceeds of Crime and Anti-Money Laundering Act (POCAMLA)

**KYC Requirements:**
```
Know Your Customer:
1. Collect and verify:
   - Full name
   - ID number (Kenyan ID or Passport)
   - Phone number
   - Physical address
   
2. Enhanced Due Diligence for:
   - High-value tipsters (earning >KES 500,000/month)
   - Unusual transaction patterns
   - Politically Exposed Persons (PEPs)

3. Record Keeping:
   - Maintain KYC records for 7 years
   - Transaction logs (all payments)
   - Audit trail
```

**Suspicious Activity Reporting:**
```
Report to FRC (Financial Reporting Centre) if:
- Transactions with no apparent economic purpose
- Rapid movement of large sums
- Multiple accounts with same details
- Structuring (breaking large amounts into smaller ones)
- Unusual betting patterns

Reporting: File Suspicious Transaction Report (STR) to FRC
- Website: frc.go.ke
- Within 24 hours of identification
```

**Transaction Limits (Good Practice):**
```
To minimize AML risk:
- Maximum tip price: KES 10,000
- Maximum daily withdrawals: KES 50,000
- Flag accounts with >KES 100,000/month transactions
- Enhanced verification for high earners
```

---

### 7. Consumer Protection

#### Kenya Consumer Protection Act 2012

**Fair Trading Practices:**
```
Must NOT:
- Make false or misleading claims
- Advertise guaranteed wins
- Hide fees or charges
- Refuse legitimate refunds (per policy)
- Discriminate against users

Must PROVIDE:
- Clear pricing (no hidden fees)
- Transparent refund policy
- Easy complaint mechanism
- Timely customer support
- Fair dispute resolution
```

**Consumer Rights:**
```
Users entitled to:
- Accurate information about tips
- Timely delivery of purchased content
- Refunds for invalid/fraudulent tips
- Protection from unfair practices
- Complaint redressal within 14 days
```

---

### 8. Tax Obligations

#### Revenue Authority Requirements

**Corporate Tax:**
```
Income Tax:
- 30% on net profits (for companies)
- File annual returns via iTax
- Pay provisional tax quarterly
- Due: Within 6 months of financial year-end
```

**Withholding Tax:**
```
Platform must withhold:
- Management fees: 5% of payments to tipsters
- Remit to KRA monthly
- Issue withholding certificates

Tipsters responsible for:
- Declaring income on personal returns
- Paying tax on earnings
- Platform provides transaction statements
```

**VAT (if applicable):**
```
If annual turnover > KES 5 million:
- Register for VAT
- Charge 16% on platform fees
- File monthly/quarterly returns
- Remit collected VAT to KRA
```

**Digital Service Tax (DST):**
```
1.5% tax on gross transaction value:
- Applies to digital marketplaces
- Calculated on total tip sales
- May apply even below VAT threshold
- Quarterly returns required

Clarification needed: Does DST apply to tips marketplace?
```

---

### 9. Website Policies & Pages

#### Required Legal Pages

**A. Terms of Service** ✓
**B. Privacy Policy** ✓
**C. Refund Policy**
```
- 100% refund conditions
- 80% refund conditions
- No refund conditions
- Processing time (24-48 hours)
- How to request refund
```

**D. Cookie Policy**
```
- Types of cookies used
- Purpose of each cookie
- How to disable cookies
- Third-party cookies (if any)
```

**E. Disclaimer**
```
Betting Disclaimer:
"This platform provides betting tips and predictions for entertainment 
and informational purposes only. All tips are opinions and NOT 
guarantees. Past performance does not indicate future results. 
You are solely responsible for your betting decisions. Gamble responsibly."
```

**F. About Us**
```
- Company registration details
- Physical address
- Contact information
- Company directors (may be required)
```

**G. Contact Us**
```
- Email support
- Phone number
- Physical office (if any)
- Business hours
- Response time expectations
```

---

### 10. Disclaimers & Notices

#### Prominent Warnings Required

**Homepage:**
```
🔞 18+ Only | ⚠️ Gamble Responsibly | 📞 Help: 1192

Clearly visible on every page (footer):
"This platform does not operate as a bookmaker. We provide a 
marketplace for betting tips. Betting involves risk. Only gamble 
what you can afford to lose."
```

**Before Registration:**
```
☑️ I confirm I am 18 years or older
☑️ I understand betting involves financial risk
☑️ I have read and agree to Terms of Service
☑️ I agree to Privacy Policy
```

**Before Purchase:**
```
"⚠️ This is a prediction, not a guarantee. 
Past performance: [Tipster win rate]
Purchase at your own risk."
```

**On Every Tip:**
```
"⚠️ No Guaranteed Outcome | For Entertainment Only | 18+"
```

---

### 11. Implementation Checklist

**Before Launch (Critical):**
- [ ] Consult gambling law attorney in Kenya
- [ ] Seek clarification from BCLB (license requirements)
- [ ] Register business entity (Limited Company)
- [ ] Obtain KRA PIN and tax compliance certificate
- [ ] Draft Terms of Service (lawyer-reviewed)
- [ ] Draft Privacy Policy (DPA-compliant)
- [ ] Register with Data Protection Commissioner
- [ ] Implement 18+ age gate
- [ ] Add responsible gambling resources
- [ ] Display all required warnings
- [ ] Set up AML/KYC procedures
- [ ] Create complaint handling process
- [ ] Get business insurance (liability)

**Within 3 Months of Launch:**
- [ ] File first tax returns
- [ ] Review compliance status
- [ ] Update policies based on operations
- [ ] Train staff on compliance
- [ ] Conduct security audit

**Ongoing:**
- [ ] Annual license renewal (if required)
- [ ] Quarterly tax filings
- [ ] Annual data protection assessment
- [ ] Policy updates (as laws change)
- [ ] Staff compliance training
- [ ] Audit logs review

---

### 12. Risk Mitigation Strategies

**Legal Risks:**
```
Risk: Regulatory shutdown
Mitigation:
- Seek pre-launch legal opinion
- Maintain open dialogue with BCLB
- Have "pivot" business model ready
- Keep separate reserves for legal defense

Risk: Underage access
Mitigation:
- Strong age verification
- Clear warnings
- Monitor for suspicious accounts
- Immediate action on violations

Risk: Money laundering allegations
Mitigation:
- Robust KYC
- Transaction monitoring
- Suspicious activity reporting
- Regular compliance audits

Risk: Consumer complaints
Mitigation:
- Fair refund policy
- Quick dispute resolution
- Customer support team
- Transparent operations
```

**Insurance Coverage:**
```
Consider:
- Professional Indemnity Insurance
- Cyber Liability Insurance
- General Business Insurance
- Directors & Officers Insurance

Cost: KES 50,000 - 200,000/year (varies)
```

---

### 13. Key Contacts & Resources

**Regulatory Bodies:**
```
1. Betting Control & Licensing Board (BCLB)
   Website: bclb.go.ke
   Email: info@bclb.go.ke
   Phone: +254 20 221 1909

2. Office of Data Protection Commissioner
   Website: odpc.go.ke
   Email: info@odpc.go.ke
   Phone: +254 20 2675 600

3. Kenya Revenue Authority (KRA)
   Website: kra.go.ke
   iTax Portal: itax.kra.go.ke
   Call Centre: 0711 099 999

4. Financial Reporting Centre (AML)
   Website: frc.go.ke
   Email: info@frc.go.ke

5. Business Registration Service
   Website: brs.go.ke
   eCitizen: ecitizen.go.ke
```

**Legal Resources:**
```
- Kenya Law Reports: kenyalaw.org
- Consumer Protection: cak.go.ke
- NACADA (Gambling Addiction): nacada.go.ke / 1192
```

---

### 14. Recommended Legal Budget

**Initial Setup:**
```
Legal consultation: KES 50,000 - 150,000
Business registration: KES 15,000 - 30,000
License application (if needed): KES 100,000 - 300,000
Data Protection registration: KES 10,000
Policy drafting: KES 30,000 - 80,000
Insurance: KES 50,000 - 100,000/year

TOTAL ESTIMATED: KES 255,000 - 660,000
```

**Ongoing (Annual):**
```
License renewal: KES 100,000 - 500,000 (if applicable)
Tax compliance: KES 50,000 - 100,000
Legal retainer: KES 100,000 - 200,000
Insurance: KES 50,000 - 100,000
Audits: KES 30,000 - 50,000

TOTAL ESTIMATED: KES 330,000 - 950,000/year
```

---

### DISCLAIMER
```
⚠️ IMPORTANT: This information is for general guidance only and does 
not constitute legal advice. Gambling and betting laws in Kenya are 
complex and evolving. You MUST consult with a qualified Kenyan attorney 
specializing in gambling law before launching this platform. Regulations 
may change, and specific circumstances may require different approaches.
```

---

## 9. MVP Scope & Timeline

### MVP Definition - What's IN vs OUT

#### ✅ IN Scope (MVP - Phase 1)

**Core Functionality:**
- ✅ User registration (phone + OTP)
- ✅ User profiles (tipsters & buyers)
- ✅ Tip posting with OCR (screenshot → extract matches → tipster verifies markets)
- ✅ Marketplace with filters & search
- ✅ Tip purchase flow (M-Pesa only)
- ✅ Bet code reveal after purchase
- ✅ Automated result verification (API-Football)
- ✅ Win rate calculation & display
- ✅ Basic badge system (3-4 badges)
- ✅ Leaderboard (top performers, earners, rising stars)
- ✅ Wallet system (tipster earnings, withdrawals)
- ✅ Admin dashboard (approvals, disputes, stats)
- ✅ Notifications (SMS for critical, in-app for others)
- ✅ Auto-archive tips after matches start
- ✅ 48-hour escrow system
- ✅ Dispute management (refund flow)
- ✅ Manual review queue (fallback)

**Technical:**
- ✅ Django backend
- ✅ PostgreSQL database
- ✅ HTMX + Tailwind frontend
- ✅ AWS Textract OCR
- ✅ AWS S3 file storage
- ✅ M-Pesa integration
- ✅ API-Football integration
- ✅ Background cron jobs
- ✅ Admin audit logs

**Deployment:**
- ✅ AWS EC2 hosting
- ✅ Nginx web server
- ✅ SSL/HTTPS
- ✅ Systemd service management

#### ❌ OUT of Scope (Phase 2+)

**Features Deferred:**
- ❌ Follow system
- ❌ Buyer reviews/ratings
- ❌ Direct messaging
- ❌ Advanced analytics graphs
- ❌ ROI calculation (Phase 2)
- ❌ Trust score algorithm
- ❌ Multi-sport support (focus on football only in MVP)
- ❌ Mobile native apps (web responsive only)
- ❌ Multiple bookmaker code loading
- ❌ Tip packages/bundles
- ❌ Video analysis uploads
- ❌ Social sharing features
- ❌ Referral program
- ❌ Advanced fraud detection (image forensics)
- ❌ Multiple payment methods (card payments)

---

### Development Phases

#### Phase 0: Setup & Infrastructure (Week 1)
**Duration:** 5-7 days

**Tasks:**
```
□ Project setup
  - Initialize Django project
  - Setup virtual environment
  - Configure settings (dev/prod)
  - Create app structure (users, tips, transactions, etc.)
  
□ Database setup
  - Design & create all 13 tables
  - Setup PostgreSQL locally
  - Create migrations
  - Seed test data
  
□ Infrastructure
  - Setup AWS account
  - Configure S3 buckets
  - Setup Textract
  - Configure EC2 instance (staging)
  
□ Third-party integrations prep
  - M-Pesa sandbox account
  - API-Football account & API key
  - Test API endpoints
  
□ Frontend foundation
  - Tailwind CSS setup
  - HTMX integration
  - Base templates (base.html, navbar, footer)
  - Design system (colors, buttons, forms)
```

**Deliverable:** Working development environment, database schema, base templates

---

#### Phase 1: User Management (Week 2)
**Duration:** 5-7 days

**Tasks:**
```
□ Authentication system
  - Phone number registration
  - OTP verification (SMS)
  - Login/logout
  - Password reset
  
□ User profiles
  - Tipster profile creation
  - Buyer profile
  - Profile editing
  - Avatar upload
  
□ User types & permissions
  - Tipster vs Buyer vs Admin roles
  - Permission checks
  - Profile access control
  
□ Admin user management
  - View all users
  - Ban/unban users
  - Verify tipsters
```

**Deliverable:** Complete user authentication and profile system

---

#### Phase 2: Tip Posting System (Week 3-4)
**Duration:** 10-12 days

**Tasks:**
```
□ Tip submission form
  - Bet code input
  - Bookmaker selection
  - Screenshot upload
  - Price setting
  
□ OCR integration
  - AWS Textract setup
  - Text extraction from screenshots
  - Parse bet codes, odds, matches
  - Error handling
  
□ Tipster verification flow
  - Display extracted data
  - Market selection dropdowns
  - Match confirmation
  - Preview before submit
  
□ Tip approval system
  - Admin review queue
  - Approve/reject tips
  - Auto-publish for verified tipsters
  - Email/SMS notifications
  
□ Tip model & storage
  - Save tip data
  - Store screenshots (S3)
  - Generate watermarked versions
  - Track tip status
```

**Deliverable:** Complete tip posting workflow from upload to approval

---

#### Phase 3: Marketplace & Discovery (Week 5)
**Duration:** 5-7 days

**Tasks:**
```
□ Marketplace listing page
  - Display all active tips
  - Grid/list view
  - Tip card design
  - Pagination
  
□ Filters & sorting
  - Sport filter
  - Odds range filter
  - Price filter
  - Bookmaker filter
  - Time to kickoff filter
  - Sort by: newest, ending soon, highest odds, best tipster
  
□ Search functionality
  - Search by tipster username
  - Search by sport/league
  - Auto-suggestions
  
□ Tip detail page
  - Full tip preview (partial info)
  - Tipster stats display
  - Purchase button
  - Countdown timer
  
□ Featured tips section
  - Admin can feature tips
  - Display prominently on homepage
```

**Deliverable:** Fully functional marketplace with filters and search

---

#### Phase 4: Payment & Transactions (Week 6-7)
**Duration:** 10-12 days

**Tasks:**
```
□ M-Pesa integration
  - STK Push implementation
  - Payment callback handling
  - Transaction logging
  - Error handling & retries
  
□ Purchase flow
  - Buy button → payment screen
  - Enter M-Pesa number
  - Receive STK push
  - Payment confirmation
  
□ Post-purchase reveal
  - Show bet code
  - Display full tip details
  - Copy code button
  - Download watermarked screenshot
  
□ Transaction management
  - Save all transactions
  - Escrow calculation
  - Revenue split (60/40)
  - Escrow release timer
  
□ My Purchases (Buyer)
  - View all purchased tips
  - Filter by status
  - Access bet codes anytime
  - Track results
  
□ My Tips (Tipster)
  - View posted tips
  - See purchase count
  - Track earnings per tip
  - Edit/delete unpurchased tips
```

**Deliverable:** Complete payment system and transaction management

---

#### Phase 5: Wallet & Withdrawals (Week 8)
**Duration:** 5-7 days

**Tasks:**
```
□ Tipster wallet
  - Display available balance
  - Show pending (in escrow)
  - Transaction history
  - Earnings breakdown
  
□ Withdrawal system
  - Withdrawal request form
  - M-Pesa number input
  - Minimum threshold check
  - Request submission
  
□ Admin withdrawal management
  - View pending requests
  - Approve/reject withdrawals
  - M-Pesa B2C integration
  - Track withdrawal status
  
□ Escrow release automation
  - Cron job: release after 48 hours
  - Update wallet balances
  - Send notifications
  
□ Payout notifications
  - SMS on withdrawal approval
  - In-app notifications
  - Email confirmations
```

**Deliverable:** Complete wallet and withdrawal system

---

#### Phase 6: Result Verification & Stats (Week 9-10)
**Duration:** 10-12 days

**Tasks:**
```
□ API-Football integration
  - Setup API client
  - Match ID mapping logic
  - Result fetching
  - Error handling
  
□ Automated result checking
  - Cron job setup (every 30 mins)
  - Check pending tips
  - Parse match results
  - Determine win/loss
  - Update tip status
  
□ Manual review queue
  - Flag tips that can't auto-verify
  - Admin review interface
  - Manual result marking
  - Resolution tracking
  
□ Tipster stats calculation
  - Win rate calculation
  - Update tipster_stats table
  - Calculate streaks
  - Update rankings
  
□ Badge system
  - Define badge criteria
  - Auto-award badges
  - Auto-revoke badges
  - Display on profiles
  
□ Leaderboard
  - Top performers (win rate)
  - Top earners (revenue)
  - Rising stars (new tipsters)
  - Real-time updates
```

**Deliverable:** Automated result verification and statistics system

---

#### Phase 7: Admin Dashboard (Week 11)
**Duration:** 5-7 days

**Tasks:**
```
□ Dashboard overview
  - Key metrics display
  - Charts & graphs
  - Quick action buttons
  
□ Tip management
  - Approve/reject queue
  - Feature tips
  - Verify codes manually
  - Delete fraudulent tips
  
□ User management
  - View all users
  - Ban/verify users
  - Toggle auto-publish
  - View user details
  
□ Dispute management
  - Review disputes
  - Check evidence
  - Approve/reject refunds
  - Communicate with users
  
□ Financial management
  - Transaction logs
  - Revenue reports
  - Withdrawal queue
  - Platform earnings
  
□ Manual review queue
  - Flagged tips interface
  - Mark results manually
  - Add notes
  
□ Audit logs
  - Track all admin actions
  - Export reports
```

**Deliverable:** Complete admin control panel

---

#### Phase 8: Notifications & Alerts (Week 12)
**Duration:** 5-7 days

**Tasks:**
```
□ Notification system
  - Database model
  - Notification creation
  - Delivery logic
  
□ SMS notifications
  - Integration with SMS gateway
  - Critical notifications only
  - Template management
  
□ In-app notifications
  - Notification bell icon
  - Real-time updates (HTMX)
  - Mark as read
  - Notification center
  
□ Email notifications (optional)
  - Setup email service
  - Email templates
  - Async sending
  
□ Notification triggers
  - Tip purchased
  - Payment received
  - Withdrawal approved
  - Tip approved/rejected
  - Match starting soon
  - Result updated
```

**Deliverable:** Complete notification system

---

#### Phase 9: Polish & Testing (Week 13-14)
**Duration:** 10-12 days

**Tasks:**
```
□ UI/UX polish
  - Responsive design testing
  - Mobile optimization
  - Loading states
  - Error messages
  - Success feedback
  
□ Performance optimization
  - Database query optimization
  - Add indexes
  - Cache frequently accessed data
  - Image optimization
  
□ Security hardening
  - CSRF protection
  - SQL injection prevention
  - Rate limiting
  - Input validation
  - XSS prevention
  
□ Testing
  - User flow testing
  - Payment testing (sandbox)
  - OCR accuracy testing
  - Result verification testing
  - Admin functions testing
  
□ Bug fixes
  - Fix identified issues
  - Handle edge cases
  - Error logging setup
  
□ Documentation
  - User guide
  - Admin manual
  - API documentation (internal)
  - README
```

**Deliverable:** Production-ready application

---

#### Phase 10: Deployment & Launch (Week 15-16)
**Duration:** 10-14 days

**Tasks:**
```
□ Production infrastructure
  - Setup production EC2
  - Configure production database
  - Setup S3 production buckets
  - Configure domain & DNS
  
□ Production deployment
  - Deploy code to production
  - Run migrations
  - Setup Nginx
  - Configure Gunicorn
  - Setup Systemd services
  
□ SSL & Security
  - Install SSL certificate (Let's Encrypt)
  - Configure HTTPS redirect
  - Setup firewall rules
  - Security audit
  
□ Production integrations
  - Switch to production M-Pesa API
  - Configure production API-Football
  - Setup production SMS gateway
  
□ Monitoring & Logging
  - Setup error tracking (Sentry)
  - Configure logging
  - Setup uptime monitoring
  - Alert configuration
  
□ Soft launch
  - Invite beta users (10-20)
  - Monitor for issues
  - Gather feedback
  - Fix critical bugs
  
□ Marketing prep
  - Landing page content
  - Social media setup
  - Launch announcement
  - User onboarding flow
  
□ Public launch
  - Remove beta restrictions
  - Announce publicly
  - Monitor closely
  - Support first users
```

**Deliverable:** Live production application

---

### Timeline Summary

```
Phase 0:  Setup & Infrastructure         → Week 1       (5-7 days)
Phase 1:  User Management               → Week 2       (5-7 days)
Phase 2:  Tip Posting System            → Week 3-4     (10-12 days)
Phase 3:  Marketplace & Discovery       → Week 5       (5-7 days)
Phase 4:  Payment & Transactions        → Week 6-7     (10-12 days)
Phase 5:  Wallet & Withdrawals          → Week 8       (5-7 days)
Phase 6:  Result Verification & Stats   → Week 9-10    (10-12 days)
Phase 7:  Admin Dashboard               → Week 11      (5-7 days)
Phase 8:  Notifications & Alerts        → Week 12      (5-7 days)
Phase 9:  Polish & Testing              → Week 13-14   (10-12 days)
Phase 10: Deployment & Launch           → Week 15-16   (10-14 days)

TOTAL ESTIMATED TIME: 15-16 WEEKS (3.5-4 MONTHS)
```

**With Buffer for Unexpected Issues: 4-5 MONTHS**

---

### Team Requirements

#### Option 1: Solo Developer (Full-Stack)
```
Timeline: 4-5 months
Requirements:
- Strong Django/Python experience
- Frontend skills (HTML, CSS, JavaScript, HTMX)
- Database design knowledge
- AWS experience
- API integration experience
- DevOps basics

Pros: Lower cost, full control
Cons: Longer timeline, single point of failure
```

#### Option 2: Small Team (2-3 People) - RECOMMENDED
```
Timeline: 3-4 months

Team Structure:
1. Backend Developer (Django, APIs, Database)
   - 40 hours/week
   - Handles: Models, views, APIs, integrations
   
2. Frontend Developer (HTMX, Tailwind, UI/UX)
   - 40 hours/week
   - Handles: Templates, styling, user experience
   
3. DevOps/Part-time (optional)
   - 10-20 hours/week
   - Handles: Deployment, monitoring, infrastructure

Pros: Faster delivery, specialization, backup
Cons: Higher cost, coordination needed
```

#### Option 3: Experienced Team (3-4 People)
```
Timeline: 2-3 months

Team Structure:
1. Senior Full-Stack Developer (Lead)
2. Backend Developer
3. Frontend Developer
4. QA/Testing Engineer

Pros: Fastest delivery, highest quality
Cons: Highest cost
```

**Recommended for MVP: Option 2 (2-3 people, 3-4 months)**

---

### Development Costs Estimate

#### Team Costs (Kenya Market Rates)
```
Junior Developer: KES 80,000 - 150,000/month
Mid-Level Developer: KES 150,000 - 250,000/month
Senior Developer: KES 250,000 - 400,000/month

Option 2 Team (4 months):
- Backend Dev (Mid): KES 200,000/month × 4 = KES 800,000
- Frontend Dev (Mid): KES 180,000/month × 4 = KES 720,000
- Total: ~KES 1,520,000 ($11,500 USD)
```

#### Infrastructure & Services (Monthly)
```
AWS EC2 (t3.medium):        KES 5,000 - 10,000
AWS S3 Storage:             KES 1,000 - 3,000
AWS Textract:               KES 2,000 - 5,000 (usage-based)
API-Football:               KES 5,000 - 7,000 (~$40-50)
PostgreSQL RDS (optional):  KES 8,000 - 15,000
Domain & SSL:               KES 2,000 - 5,000
SMS Gateway:                KES 0.50 - 1.50 per SMS
M-Pesa API:                 Transaction fees only

Initial Setup: ~KES 20,000 - 40,000
Monthly Running: ~KES 15,000 - 35,000 ($100-250 USD)
```

#### Total MVP Investment
```
Development: ~KES 1,500,000
Infrastructure (4 months): ~KES 100,000
Testing & Buffer: ~KES 200,000

TOTAL: KES 1,800,000 - 2,000,000 ($13,500 - 15,000 USD)
```

---

### Launch Checklist

#### Pre-Launch (1 Week Before)
```
□ All features tested thoroughly
□ Security audit completed
□ SSL certificate installed
□ Production database backed up
□ Error tracking configured
□ Admin accounts created
□ Terms of Service finalized
□ Privacy Policy posted
□ About/Contact pages complete
□ FAQ page created
□ Social media accounts set up
□ Customer support email set up
□ Beta user feedback incorporated
□ Performance tested (load testing)
□ Mobile responsiveness verified
□ Payment flows tested end-to-end
□ Email/SMS notifications working
□ Domain DNS configured
□ Monitoring alerts set up
□ Backup strategy in place
□ Rollback plan prepared
```

#### Launch Day
```
□ Final smoke tests
□ Monitor error logs closely
□ Watch server metrics
□ Test user registration
□ Test payment flow
□ Check notification delivery
□ Monitor M-Pesa callbacks
□ Be ready for quick fixes
□ Announce on social media
□ Send launch emails (if list exists)
□ Monitor user feedback
□ Track first transactions
□ Log all issues
```

#### Post-Launch (First Week)
```
□ Daily monitoring
□ Quick bug fixes
□ Gather user feedback
□ Address critical issues
□ Monitor API usage/costs
□ Check server performance
□ Review transaction success rates
□ Verify result checking accuracy
□ Support early users
□ Document common issues
□ Plan immediate improvements
□ Track key metrics (signups, transactions)
```

---

### Success Metrics (First 3 Months)

#### User Acquisition
```
Month 1:  50-100 users (20 tipsters, 30-80 buyers)
Month 2:  200-300 users (50 tipsters, 150-250 buyers)
Month 3:  500-800 users (100-150 tipsters, 400-650 buyers)
```

#### Transaction Volume
```
Month 1:  50-100 tips purchased (KES 10,000 - 20,000 GMV)
Month 2:  200-400 tips purchased (KES 50,000 - 100,000 GMV)
Month 3:  500-800 tips purchased (KES 150,000 - 250,000 GMV)
```

#### Platform Revenue (40% commission)
```
Month 1:  KES 4,000 - 8,000
Month 2:  KES 20,000 - 40,000
Month 3:  KES 60,000 - 100,000
```

**Break-even Target: Month 6-8** (when monthly revenue > monthly costs)

---

### Post-MVP Roadmap (Phase 2)

#### Month 4-5: Quick Wins
```
□ Follow system
□ Buyer reviews/ratings
□ ROI calculation display
□ Email newsletter
□ Referral program
□ More sports (basketball, tennis)
```

#### Month 6-8: Growth Features
```
□ Direct messaging
□ Tip packages/bundles
□ Advanced analytics
□ Trust score display
□ Premium tipster tiers
□ Featured listings (paid)
```

#### Month 9-12: Scaling
```
□ Mobile apps (iOS/Android)
□ Multiple bookmaker support
□ API for third parties
□ White-label solution
□ International expansion
```

---

### Risk Mitigation

#### Technical Risks
```
Risk: OCR accuracy issues
Mitigation: Hybrid approach (tipster verifies), manual review queue

Risk: API-Football downtime
Mitigation: Manual review fallback, retry logic, status page

Risk: M-Pesa integration issues
Mitigation: Comprehensive testing, sandbox environment, fallback support

Risk: Server downtime
Mitigation: Monitoring, alerts, backup server, quick rollback plan

Risk: Database corruption
Mitigation: Daily backups, point-in-time recovery, replica database
```

#### Business Risks
```
Risk: Low tipster quality
Mitigation: Verification process, performance tracking, ban system

Risk: Fraud/scams
Mitigation: Admin approval, dispute system, audit logs, pattern detection

Risk: Low user adoption
Mitigation: Beta testing, user feedback, marketing, referral program

Risk: Regulatory issues
Mitigation: Legal consultation, terms of service, age verification

Risk: Competition
Mitigation: Focus on UX, quality tipsters, fair pricing, good support
```

---

## 10. Next Steps

### Immediate Actions (Week 0)

1. **Assemble Team**
   - Hire developers or engage development agency
   - Setup communication tools (Slack, Discord)
   - Define workflows and responsibilities
   - Create project management board (Jira, Trello, GitHub Projects)

2. **Legal Setup** (Parallel to Development)
   - Register company/business
   - Consult lawyer for gambling/betting regulations in Kenya
   - Draft Terms of Service
   - Draft Privacy Policy
   - Age verification requirements
   - BCLB (Betting Control and Licensing Board) consultation

3. **Financial Setup**
   - Open business bank account
   - Apply for M-Pesa Paybill/Till number
   - Setup accounting system
   - Tax registration (KRA PIN)

4. **Marketing Preparation** (Parallel to Development)
   - Build landing page (coming soon)
   - Setup social media accounts (Twitter, Facebook, Instagram)
   - Create brand assets (logo, colors, fonts)
   - Outreach to potential tipsters (beta testers)
   - Build email list
   - Content strategy

### Week 1: Kick-off

**Day 1: Project Kick-off Meeting**
```
□ Review this planning document with team
□ Clarify questions and requirements
□ Assign Phase 0 responsibilities
□ Setup Git repository
□ Create project board with all tasks
□ Define daily standup schedule
□ Setup development environments
```

**Day 2-5: Infrastructure & Setup**
```
□ Complete Phase 0 tasks (see timeline above)
□ Daily standups (15 mins)
□ Document setup process
□ Test local development environment
```

**Week 1 Milestone:** Team ready, environment configured, database designed

### Sprint Planning (Weekly)

**Every Monday:**
```
□ Review previous week progress
□ Plan current week tasks
□ Assign tickets to team members
□ Identify blockers
□ Update timeline if needed
```

**Daily:**
```
□ 15-minute standup
□ What did you do yesterday?
□ What will you do today?
□ Any blockers?
```

**Every Friday:**
```
□ Demo completed features
□ Code review session
□ Deploy to staging
□ Update stakeholders
□ Retrospective (what went well, what to improve)
```

### Critical Milestones

```
Week 4:  First working feature (user registration) ✓
Week 7:  Tip posting functional ✓
Week 10: Payments working ✓
Week 14: Full MVP complete ✓
Week 16: LAUNCH 🚀
```

### Success Criteria

**MVP is ready when:**
```
✓ User can register and login
✓ Tipster can post tips with screenshots
✓ OCR extracts data accurately (80%+ success rate)
✓ Marketplace displays tips correctly
✓ Filters and search work
✓ Payment flow works end-to-end
✓ Bet codes are revealed after purchase
✓ Results are verified automatically
✓ Win rates calculate correctly
✓ Leaderboard updates properly
✓ Admin can manage everything
✓ Notifications are sent
✓ Withdrawals process successfully
✓ Mobile responsive on all pages
✓ Load time < 3 seconds
✓ No critical bugs
✓ SSL/HTTPS working
✓ Terms and Privacy Policy published
```

---

*Last Updated: October 25, 2025*
*Status: Planning Complete - Ready for Development*
*Total Pages: 100+*
*Estimated MVP Timeline: 15-16 weeks (4 months)*
*Estimated Investment: KES 1.8M - 2.0M*
