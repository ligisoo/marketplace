# Multi-Role Access Control Review

## 🎭 User Role Combinations

Users in the system can be:
1. **Buyer Only**: `is_buyer=True, is_tipster=False`
2. **Tipster Only**: `is_buyer=False, is_tipster=True`
3. **Both**: `is_buyer=True, is_tipster=True` ← Gladys (0725771129)
4. **Neither**: `is_buyer=False, is_tipster=False` ← Default new users

## 📊 Current Access Control Behavior

### Scenario 1: Pure Buyer (is_buyer=True, is_tipster=False)

**Marketplace Browsing:**
- ✅ Can see all active tips
- ✅ Sees preview of all tips
- ✅ Can filter/search tips

**Purchasing:**
- ✅ Can purchase any tip (except own - but they have none)
- ✅ Wallet balance checked
- ✅ Can't purchase same tip twice

**Tip Details:**
- ✅ Preview mode: First 2 matches, no picks/odds
- ✅ Full details after purchase

**Verdict**: ✅ **CORRECT BEHAVIOR**

---

### Scenario 2: Pure Tipster (is_buyer=False, is_tipster=True)

**Marketplace Browsing:**
- ✅ Can see all active tips (including competitors)
- ✅ Sees preview of competitor tips
- ⚠️ Sees competitors' strategies, markets, leagues

**Purchasing:**
- ❌ BLOCKED - Cannot purchase anything (line 313-316 in views.py)
```python
if not request.user.userprofile.is_buyer:
    return JsonResponse({'error': 'Only buyers can purchase tips.'})
```

**Tip Details:**
- ✅ Full details of own tips (because `user == tip.tipster`)
- ⚠️ Preview of competitor tips (can see teams/markets but no picks)

**Issues Identified:**
1. **Competitive Intelligence Leakage** ⚠️
   - Tipsters can browse competitor tips
   - Can see what leagues/markets competitors focus on
   - Can see team matchups (first 2)
   - **Risk**: Tipsters copy competitor strategies

2. **Cannot Research/Learn** ⚠️
   - Pure tipsters cannot purchase competitor tips to learn
   - Blocks legitimate use case: buying tips to improve own skills
   - **Limitation**: Forces tipsters to create separate buyer account

**Verdict**: ⚠️ **NEEDS REVIEW**

---

### Scenario 3: Both Tipster & Buyer (is_buyer=True, is_tipster=True)

**Example**: Gladys (0725771129) - This is the case you asked about!

**Marketplace Browsing:**
- ✅ Can see all active tips (own + competitors)
- ✅ Sees all 10 tips mixed together
- ⚠️ No visual distinction between own tips and others

**Purchasing:**
- ✅ Can purchase competitor tips
- ✅ Blocked from self-purchase (line 319-322)
- ✅ Can study competitor strategies after purchase

**Tip Details:**
- ✅ Full details of own tips (created by them)
- ✅ Full details of purchased tips
- ✅ Preview of non-purchased competitor tips

**Issues Identified:**
1. **No Role Context** ⚠️
   - Marketplace mixes "tips I created" with "tips I can buy"
   - No clear separation of "manage my tips" vs "browse to buy"
   - Confusing UX for dual-role users

2. **Competitive Analysis** ⚠️
   - Tipster-buyers can purchase ALL competitor tips
   - Learn exact strategies, picks, odds
   - Potentially replicate successful patterns
   - **Risk**: Top tipsters reverse-engineer each other

3. **Marketplace Clutter** ⚠️
   - Own tips appear in marketplace alongside others
   - Can't easily filter "show only others' tips"
   - **UX Issue**: Hard to browse as buyer without seeing own tips

**Verdict**: ⚠️ **UX ISSUES & SECURITY CONCERNS**

---

### Scenario 4: Neither Role (is_buyer=False, is_tipster=False)

**Marketplace Browsing:**
- ✅ Can see all active tips
- ✅ Can see previews

**Purchasing:**
- ❌ BLOCKED - Cannot purchase

**Tip Details:**
- ✅ Preview mode only (they own no tips)

**Verdict**: ✅ **CORRECT** (default state for new users)

---

## 🚨 Security & Business Logic Issues

### Issue 1: Competitive Intelligence Leakage

**Risk**: Tipsters can study competitors for free/cheap

**Current State:**
- Tipster-buyers can purchase all competitor tips
- See exact picks, odds, strategies, timing
- Can reverse-engineer successful tipsters

**Example Scenario:**
```
1. Gladys (tipster+buyer) sees Walter has 80% win rate
2. Gladys purchases all Walter's tips (KES 500 total)
3. Gladys learns Walter specializes in Over 2.5 goals in EPL
4. Gladys copies Walter's strategy in her own tips
5. Gladys undercuts Walter's prices
6. Result: Market cannibalization
```

**Recommendations:**
- ⚠️ Consider: Block tipsters from purchasing competitor tips
- ⚠️ Consider: Add premium pricing for tipster-to-tipster purchases
- ⚠️ Consider: Anonymize tipster identities in marketplace
- ✅ Accept: This is market competition (current approach)

### Issue 2: No Role Separation in UI

**Problem**: Users with both roles see everything mixed together

**Current Marketplace View (for Gladys):**
```
Marketplace
├─ IBUSRE (Gladys - her own)
├─ MPCPYA (Gladys - her own)
├─ MISLUX (Walter - can buy)
├─ MISLUT (Walter - can buy)
├─ MISLUP (Gladys - her own)
...
```

**Better UX:**
```
My Tips Dashboard (Tipster View)
├─ IBUSRE (mine)
├─ MPCPYA (mine)
├─ MISLUP (mine)

Browse Marketplace (Buyer View)
├─ MISLUX (Walter - can buy)
├─ MISLUT (Walter - can buy)
...
```

**Recommendations:**
- ✅ Keep "My Tips" page (already exists for tipsters)
- ⚠️ Filter OUT own tips from marketplace when user is tipster
- ⚠️ Add tab/toggle: "Buy Tips" vs "Manage Tips"

### Issue 3: Preview Information Leakage

**What Competitors Can See (Without Purchasing):**
- ✅ Bet code (partially masked)
- ✅ Price
- ✅ Bookmaker
- ✅ Total odds
- ✅ Number of matches
- ✅ First 2 matches (teams + markets)
- ✅ Leagues
- ❌ Picks/selections (protected)
- ❌ Individual odds (protected)

**Risk**: Free market research

**Example:**
```
Tipster A sees Tipster B's preview:
- "Oh, they focus on La Liga Over 2.5"
- "They price at KES 100"
- "They get 3.5x total odds"
- "I'll target the same market but price at KES 80"
```

**Recommendations:**
- ⚠️ Consider: Hide league names in preview
- ⚠️ Consider: Show only "X matches" without team names
- ⚠️ Consider: Blur more info for tipster viewers
- ✅ Accept: This info is standard for marketplaces

---

## 💡 Recommended Changes

### Priority 1: UI Separation for Dual-Role Users

**Change Marketplace Filtering:**

```python
# apps/tips/views.py - marketplace view
def marketplace(request):
    tips = Tip.objects.filter(status='active', expires_at__gte=timezone.now())

    # NEW: Exclude own tips for tipsters in marketplace
    if request.user.is_authenticated and request.user.userprofile.is_tipster:
        tips = tips.exclude(tipster=request.user)

    # ... rest of code
```

**Benefits:**
- ✅ Tipsters don't see their own tips in marketplace
- ✅ Clear separation: "My Tips" page for managing, Marketplace for buying
- ✅ Reduces clutter for dual-role users

**Downside:**
- ⚠️ Tipsters can't browse their own tips in marketplace view
- ⚠️ But they have "My Tips" page for that

### Priority 2: Add Visual Indicators

**For Dual-Role Users, show context:**

```django
<!-- In marketplace -->
{% if user.userprofile.is_tipster %}
    <div class="alert">
        <p>📋 Your tips are in <a href="{% url 'tips:my_tips' %}">My Tips</a> dashboard</p>
        <p>🛒 Browse competitor tips below:</p>
    </div>
{% endif %}
```

### Priority 3: Purchase Restrictions (Optional)

**Option A: Block Tipster-to-Tipster Purchases**
```python
# In purchase_tip view
if request.user.userprofile.is_tipster and tip.tipster.userprofile.is_tipster:
    return JsonResponse({
        'error': 'Tipsters cannot purchase from other tipsters. Set is_buyer=True to buy tips.'
    })
```

**Option B: Premium Pricing for Tipsters**
```python
# In purchase_tip view
price = tip.price
if request.user.userprofile.is_tipster:
    price = tip.price * 2  # Double price for competitive research
```

**Option C: Keep Current (Allow Purchases)**
- Accept competitive intelligence as part of business
- Market will self-regulate

### Priority 4: Analytics & Monitoring

**Track Competitive Research:**
```python
# Add to TipPurchase model
is_competitor_purchase = models.BooleanField(default=False)

# In purchase_tip view
purchase = TipPurchase.objects.create(
    tip=tip,
    buyer=request.user,
    is_competitor_purchase=(
        request.user.userprofile.is_tipster and
        tip.tipster.userprofile.is_tipster
    )
)
```

**Benefits:**
- Track how much competitive analysis happens
- Identify if this is a problem
- Make data-driven decisions

---

## 🎯 Recommended Implementation Plan

### Phase 1: Quick UX Fixes (No DB changes)

1. **Filter own tips from marketplace for tipsters**
   - Modify `marketplace()` view
   - Add exclusion: `tips.exclude(tipster=request.user)`

2. **Add role context banners**
   - Update marketplace template
   - Show "Browsing as Buyer" or "Your tips in My Tips" messages

3. **Add filter toggle (optional)**
   - "Show all tips" vs "Hide my tips"
   - User preference

**Effort**: 1-2 hours
**Impact**: High - Better UX for dual-role users

### Phase 2: Purchase Policy Decision (Business decision needed)

**Question for stakeholders**: Should tipsters be able to purchase competitor tips?

**Option A: Yes (Current)**
- Pros: Freedom, learning, benchmarking
- Cons: Competitive intelligence, strategy copying

**Option B: No**
- Pros: Protects IP, prevents copying
- Cons: Restricts learning, forces dual accounts

**Option C: Yes but Premium**
- Pros: Allows research, generates revenue, adds friction
- Cons: Complex pricing

**Effort**: 30 minutes - 2 hours depending on choice
**Impact**: Medium - Affects business model

### Phase 3: Analytics & Monitoring (Optional)

1. Track competitor purchases
2. Monitor if strategy copying occurs
3. Make data-driven policy changes

**Effort**: 2-4 hours
**Impact**: Low initially - Enables future decisions

---

## 📋 Current Code Review

### ✅ What's Working Well

1. **Self-purchase prevention** (Line 319-322)
```python
if request.user == tip.tipster:
    return JsonResponse({'error': 'You cannot purchase your own tip.'})
```

2. **Duplicate purchase prevention** (Line 326-330)
```python
if TipPurchase.objects.filter(tip=tip, buyer=request.user).exists():
    return JsonResponse({'error': 'You have already purchased this tip.'})
```

3. **Template access control**
```django
{% if has_purchased or user == tip.tipster %}
    <!-- Full details -->
{% else %}
    <!-- Preview -->
{% endif %}
```

### ⚠️ What Needs Consideration

1. **No role-based marketplace filtering**
   - Tipsters see own tips mixed with others
   - Confusing for dual-role users

2. **No purchase restrictions based on roles**
   - Tipster-buyers can freely purchase competitors
   - Potential competitive intelligence issue

3. **No analytics on competitor purchases**
   - Can't measure if this is a problem
   - Flying blind on market dynamics

---

## 🎬 Recommended Next Steps

1. **Immediate**: Implement Phase 1 (UX fixes)
   - Filter own tips from marketplace for tipsters
   - Add contextual banners

2. **Short-term**: Decide on purchase policy
   - Discuss with stakeholders
   - Implement chosen approach

3. **Long-term**: Add analytics
   - Track competitor purchases
   - Monitor for abuse
   - Adjust policy as needed

---

## 🤔 Questions for You

1. **Should tipsters be able to see competitor tips in marketplace?**
   - Current: Yes
   - Alternative: No, only in "My Tips" page

2. **Should tipsters be able to buy competitor tips?**
   - Current: Yes (if is_buyer=True)
   - Alternatives: No / Yes but premium price

3. **Is competitive intelligence a feature or bug?**
   - Feature: Encourages quality, market learns
   - Bug: Leads to copying, cannibalization

4. **Should we track competitor purchases?**
   - Helps make data-driven decisions
   - Adds slight complexity

Let me know your preferences and I'll implement the chosen approach! 🚀
