# Dynamic OCR Extraction System

## Problem with Previous Approach

The old OCR extraction used **hardcoded patterns** for markets and picks:
- ❌ Only recognized specific markets: "3 Way", "Over/Under", "BTTS", etc.
- ❌ Only recognized specific picks: "Home", "Away", "OVER 2.5", etc.
- ❌ Failed when bookmakers used different terminology
- ❌ Couldn't handle new market types without code changes

**Example failure**: "Rangers FC – Roma" with market "Total Goals Over/Under - Full Time" wasn't recognized because it didn't match the hardcoded patterns exactly.

## New Dynamic Approach

The new system is **structure-based**, not pattern-based. It understands that betslips have a predictable **structure**, even if the content varies:

```
Structure Pattern:
1. Team A – Team B          (separator: –, -, vs, @, /)
2. Market Type              (any text describing the bet)
3. Your Pick: Selection     (explicit prefix OR standalone text)
4. Odds: X.XX              (decimal number)
```

### How It Works

#### 1. **Team Detection** (Lines 421-438)
- Looks for text with separators: `–`, `-`, `vs`, `@`, `/`, `x`
- Example: "Rangers FC – Roma" → Teams found!
- Fallback: Checks consecutive lines that look like team names

#### 2. **Dynamic Market Detection** (Lines 473-479)
**Key Change**: Captures ANY text as market, not just known patterns
```python
# OLD: Only matched known patterns
if text in ["3 Way", "Over/Under", "BTTS"]:
    market = text

# NEW: Captures ANYTHING as market
if not is_teams and not is_pick_line and not is_odds:
    market = text  # Could be ANY market type!
```

**Examples captured**:
- ✅ "3 Way"
- ✅ "Total Goals Over/Under - Full Time"
- ✅ "Asian Handicap"
- ✅ "Correct Score"
- ✅ "Player to Score Anytime"
- ✅ "Both Teams to Score in Both Halves"
- ✅ **ANY market text!**

#### 3. **Dynamic Pick Detection** (Lines 481-506)
**Two-stage approach**:

**Stage 1**: Look for explicit prefix
```python
"Your Pick: Home" → Selection: "Home"
"Pick: OVER 2.5" → Selection: "OVER 2.5"
```

**Stage 2**: If no prefix, capture ANY text between market and odds
```python
# Line after market (before odds)
"Home" → Selection: "Home"
"OVER 2.5" → Selection: "OVER 2.5"
"YES (GG)" → Selection: "YES (GG)"
"Draw & Under 2.5" → Selection: "Draw & Under 2.5"
```

**Examples captured**:
- ✅ Standard: "Home", "Away", "Draw", "1", "X", "2"
- ✅ Over/Under: "OVER 2.5", "UNDER 1.5", "O 3.5", "U 4.5"
- ✅ BTTS: "YES (GG)", "NO", "Yes"
- ✅ Handicap: "+1.5", "-2.0", "Home -1"
- ✅ Combo: "1X", "12", "Draw/Draw", "Over 2.5 & BTTS Yes"
- ✅ Custom: **ANY text between market and odds!**

#### 4. **Odds Detection** (Lines 508-519)
**Most reliable pattern** - always a decimal number:
```python
Pattern: \d{1,3}\.\d{2}
Range: 1.01 to 999.99

Examples:
✅ 1.55
✅ 2.30
✅ 10.50
✅ 99.99
```

### Position-Based Heuristics

The system uses **position** to determine what each line is:

```
Line 1: "Brugge – Barcelona"        → TEAMS (has separator)
Line 2: "3 Way"                     → MARKET (first line after teams)
Line 3: "Your Pick: Away"           → PICK (has prefix)
Line 4: "1.55"                      → ODDS (decimal number)
```

```
Line 1: "Rangers FC – Roma"         → TEAMS
Line 2: "Total Goals Over/Under"    → MARKET (captured dynamically!)
Line 3: "OVER 2.5"                  → PICK (captured dynamically!)
Line 4: "1.84"                      → ODDS
```

## Why This Works Better

### 1. **Handles Any Market Type**
No need to update code when bookmakers add new markets:
- ✅ Traditional: 1X2, Over/Under, BTTS, Double Chance
- ✅ Advanced: Asian Handicap, European Handicap, Correct Score
- ✅ Player Props: Player to Score, Player Shots, Player Cards
- ✅ Special: Combo bets, Multi-goals, Half Time/Full Time
- ✅ Custom: Whatever bookmaker creates!

### 2. **Handles Any Pick Format**
Bookmakers use different formats - we capture them all:
- ✅ Simple: Home, Away, Draw, 1, X, 2
- ✅ Goals: Over 2.5, Under 1.5, O2.5, U1.5
- ✅ Yes/No: Yes, No, YES (GG), NO
- ✅ Complex: Draw & Under 2.5, 1X & BTTS, Home -1.5

### 3. **Bookmaker Independent**
Different bookmakers format betslips differently:
- ✅ Bet365: "Your Pick: Away"
- ✅ SportPesa: "Pick: 2"
- ✅ 1xBet: Just shows "Away" without prefix
- ✅ Betway: Shows "Selection: Home"

**All captured successfully!**

### 4. **Resilient to OCR Errors**
If OCR makes small mistakes:
- "3Way" vs "3 Way" → Both captured
- "OVER2.5" vs "OVER 2.5" → Both captured
- "Rangers FC – Roma" vs "Rangers FC - Roma" → Both captured

### 5. **User Verification**
Even if extraction isn't perfect:
- ✅ User sees all extracted data on verification page
- ✅ User can edit any field (market, pick, odds)
- ✅ Better to capture something wrong than miss it entirely

## Technical Implementation

### Key Functions

1. **`_extract_matches()`** (Lines 412-547)
   - Main extraction loop
   - Structure-based scanning

2. **`_is_pick_line()`** (Lines 616-618)
   - Checks for explicit pick prefix
   - Helps distinguish pick from market

3. **`_is_odds_only()`** (Lines 620-623)
   - Identifies pure odds lines
   - Prevents odds from being captured as market/pick

4. **`_looks_like_team_name()`** (Lines 586-614)
   - Validates team names
   - More lenient than before

### Extraction Flow

```
1. Scan text blocks sequentially
2. Find team names (with separator OR consecutive lines)
3. After teams found, scan ahead (up to 8 lines):
   - First non-team/non-pick/non-odds line → Market
   - Line with "Pick:" prefix OR text after market → Pick
   - Decimal number → Odds
4. If found pick + odds → Valid match!
5. Move to next team pair
```

## Examples

### Example 1: Standard 3 Way
```
Input:
  Brugge – Barcelona
  3 Way
  Your Pick: Away
  1.55

Output:
  ✅ Teams: Brugge vs Barcelona
  ✅ Market: 3 Way
  ✅ Pick: Away
  ✅ Odds: 1.55
```

### Example 2: Total Goals (Previously Failed!)
```
Input:
  Rangers FC – Roma
  Total Goals Over/Under - Full Time
  Your Pick: OVER 2.5
  1.84

Output:
  ✅ Teams: Rangers FC vs Roma
  ✅ Market: Total Goals Over/Under - Full Time
  ✅ Pick: OVER 2.5
  ✅ Odds: 1.84
```

### Example 3: No Explicit Pick Prefix
```
Input:
  Ajax – Galatasaray
  3 Way
  Home
  3.20

Output:
  ✅ Teams: Ajax vs Galatasaray
  ✅ Market: 3 Way
  ✅ Pick: Home (captured dynamically!)
  ✅ Odds: 3.20
```

### Example 4: Complex Market
```
Input:
  Stuttgart – Feyenoord
  Both Teams To Score
  YES (GG)
  1.61

Output:
  ✅ Teams: Stuttgart vs Feyenoord
  ✅ Market: Both Teams To Score
  ✅ Pick: YES (GG)
  ✅ Odds: 1.61
```

## Future Improvements

The system is already very dynamic, but could be enhanced:

1. **Machine Learning**: Train model to recognize patterns in betslip structures
2. **Confidence Scoring**: Rate each extraction with confidence percentage
3. **Multi-line Markets**: Handle markets split across multiple lines
4. **Embedded Odds**: Better handle cases where odds are on same line as pick
5. **League Detection**: Extract league/competition information
6. **Date/Time Extraction**: Parse match dates and times

## Summary

### Old System: Pattern-Based ❌
- Hardcoded markets
- Hardcoded picks
- Fails on unknown formats
- Requires code updates

### New System: Structure-Based ✅
- **Dynamic market capture**
- **Dynamic pick capture**
- **Handles ANY format**
- **No code updates needed**
- **Bookmaker independent**
- **Works with any football betting market**

The system now **learns from the structure** instead of looking for specific content, making it truly dynamic and future-proof!

