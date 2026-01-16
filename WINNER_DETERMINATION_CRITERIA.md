# Winner Determination Criteria Analysis

## Official Competition Rules (from agt_competition_rules.md)

### Ranking Criteria
1. **Primary:** Total utility earned in respective stage
2. **Tiebreaker 1:** Highest individual item utility captured  
3. **Tiebreaker 2:** Most items won
4. **Final Tiebreaker:** Team registration timestamp

### Utility Calculation
**Game Utility = Σ(Value of Won Items) - Total Amount Paid**

Note: Unspent budget does NOT contribute to utility score.

---

## Implementation in Code (from tournament_manager.py)

### Arena Winner Determination Logic
```python
def determine_arena_winner(self, arena_teams, game_results):
    """
    Winner determination logic:
    1. Number of games won (most wins)
    2. If tied: Highest cumulative utility across all games (total value of items won, not net utility)
    3. If tied: Team with maximal single item utility won
    4. If tied: Highest cumulative utility gap (sum of utility differences from 2nd place in each game)
    """
```

### Sorting Key (lines 211-218)
```python
sorted_teams = sorted(
    team_stats.values(),
    key=lambda x: (
        x['games_won'],                    # 1. Most games won
        x['cumulative_valuation'],         # 2. Highest cumulative valuation
        x['max_item_utility'],             # 3. Highest single item utility
        x['cumulative_utility_gap']        # 4. Highest utility gap
    ),
    reverse=True
)
```

---

## CRITICAL DISCREPANCY IDENTIFIED

### The Problem
The **official rules** say to rank by **total utility** (value - payments), but the **code implementation** ranks by:
1. **Number of games won** (not mentioned in rules!)
2. **Cumulative valuation** (total value of items won, NOT net utility)

### What This Means

**According to Official Rules:**
- Winner = Team with highest **total utility** (value - cost)
- Example: Team A wins 3 games with utility [10, 12, 8] = **30 total**

**According to Code Implementation:**  
- Winner = Team with **most game wins**, then highest total valuation (ignoring costs)
- Example: Team B wins 4 games with utility [5, 6, 7, 4] = **22 total** but **4 wins beats Team A**

### Current State Analysis

Looking at our Arena 2 data:
- **We_Run_Venezuela**: avg utility=35.45, wins=10
- **skibidi_toilet**: avg utility=30.76, wins=13

**By Official Rules (total utility across 25 games):**
- We_Run_Venezuela: 35.45 × 25 = **886.25 total utility** ✓ WINNER
- skibidi_toilet: 30.76 × 25 = **769.00 total utility**

**By Code Implementation (most games won):**
- skibidi_toilet: **13 wins** ✓ "WINNER"
- We_Run_Venezuela: 10 wins

---

## Recommendation

### Question for Decision
**Which criterion should we use?**

#### Option 1: Follow Official Rules (Total Utility)
- **Pros:** Matches published rules that students were told
- **Cons:** Code has been running with different logic
- **Winner Ranking:** By cumulative/average utility across all games

#### Option 2: Follow Code Implementation (Most Wins + Valuation)
- **Pros:** Matches what was actually executed
- **Cons:** Contradicts published rules
- **Winner Ranking:** By number of game wins, then total valuation

### My Analysis
Since the **official rules document** is what students were given and what they optimized their strategies for, we should use **Option 1: Total Utility**. The code implementation appears to have a bug that doesn't match the specification.

### Impact on Results
Using **average utility** (which equals total utility ÷ number of games, preserving rankings):

**Current Verified Winners by Average Utility:**
1. Arena 1: DSIC_Gal_Liam (20.64)
2. Arena 2: We_Run_Venezuela (35.45)  
3. Arena 3: TAR (11.03)
4. Arena 4: inglorious_bidders (20.16)
5. Arena 5: team_amboli (26.51)

These are different from what the code produced!
