# Auto bidding Challenge 

Welcome to AGT 2025-2026 challenge! 
This competition will test your understanding of auction mechanisms, strategic bidding, budget management, and algorithmic decision-making in a dynamic, multi-stage environment.

## Educational Objectives
In this challenge you'll practice the following topics: 

1. **Auction Theory:** Understanding second-price auction properties and strategic implications
2. **Algorithmic Strategy:** Designing computational approaches to sequential decision-making
3. **Budget Optimization:** Resource allocation under scarcity and uncertainty
4. **Competitive Analysis:** Reasoning about opponent behavior and market dynamics
5. **Information Economics:** Decision-making with partial information and limited market signals

The following concepts will play a key role in your success - don't forget to review them!

- **Truthful Bidding:** When is bidding your true value optimal in second-price auctions?
- **Budget Constraints:** How do financial limitations change bidding strategies?
- **Sequential Games:** Planning and adaptation in multi-round environments
- **Information Asymmetry:** Using private valuations strategically
- **Information revelation:** Making inferences about others' behavior
- **Algorithmic Game Theory:** Algorithm design for strategic environments

---

# Game Mechanics
Please read these instructions carefully.

## Competition Overview

- **Competition Structure:**  Two-stage elimination tournament  
- **Team Size:**  3 students per team (exceptions only in case the number of students satisfies $\mathbf{N} \ mod \ 3 \neq 0$)
- **Duration:** 5 weeks total (4 weeks preparations, 1 week challenge)  
- **Objective:** Maximize total utility across all auction rounds through strategic algorithmic bidding as defined below

## Schedule (exact dates TBA)

### Stage 1: Qualification Round (Sunday-Wednesday)
- **Participants:** All registered teams
- **Tournament:** Teams are allocated into a 5-team arena
- **Total Rounds:** 5 *games*, each has 15 rounds
- **Advancement:** The top scoring team from each arena continues to the next stage  

### Stage 2: Championship Round (Wednesday to Sunday)
- **Participants:** Qualified teams from Stage 1 
- **Tournament:** All teams are allocated into one arena
- **Total Rounds:** 5 *games*, each has 15 rounds
- **Advancement:** The top scoring team wins the challenge

---

## Game structure and Information

### General Setup

- **Items Available:** There are $K = 20$ different items available  
- **Auction Rounds:** At each game there are T = 15 rounds (subset of items auctioned)
- **Sequential Auction:** At each round one item is sold. Once the item is allocated, a new round begins
- **Allocation Mechanism:** The item is allocated via 2nd price, sealed bid auction

1. **Pre Game Stage:** 
At the start of each game, teams learn:
   - Their complete 20-item valuation vector for this game $V_i = \langle v^1_i, \dots, v_i^{20}\rangle $
      - The valuation vectors are additive
   - Which 15 items will be auctioned (note that at each game $15$ items are sampled uniformly from the available $20$)
      - Note - you don't know the order of the auctions a-priori
   - Each team gets a budget of 60 units (B=60)

2. **In game stage:**
After each round, teams will learn:
   - The winning team identity 
   - The winning bid $b^t$   

### Item Valuation Structure

**Valuation Vector Generation:** 
   - Each team receives a 20-dimensional valuation vector at stage start
   - Items divided into three categories: **High-Value for All**, **Low-Value for All** and **Mixed Values** items:
   - **High-Value For All Items:** Highly valued items for all teams - 6 items
         - Formally: $v_i \sim U[10,20]$
   - **Low-Value For All Items:** Low valued items for all teams - 4 items
         - Formally: $v_i \sim U[1,10]$
   - **Mixed Values:** High valued for some teams, low valued for other teams - 10 items
         - Formally: $v_i \sim U[1,20]$
   - **Distribution Design:** Ensures teams typically get a mix of high and low-value items, preventing extreme all-high or all-low allocations
   - Teams only know their complete valuation vector throughout each challenge

**Strategic Implication:** Teams must identify which of their high-value items are likely contested vs. which low-value items they might win cheaply
   - Note that this implies that some high value items in your valuation vector are valued by all, and some are only valued by a few - but you don't know which!

## Game overview

1. **Agent design:**
   - Teams submit Python code implementing their bidding strategy
   - Each agent takes as constructor inputs: `(preference_vector, initial_budget, auction_items_sequence)`
   - Each auction round, the system calls each team's bidding function
      - Function receives: `(item_id)`
      - Function must return: `bid_amount` (float, non-negative, ≤ current_budget)
   - Bids exceeding remaining budget are automatically capped
   - Failure to bid within time registers as $0$ bid
   - Each team is also assigned a unique `group_id` (UUID) for identification, which is provided to the bidding function as an additional argument.
   - **Time Limit:** 2 seconds maximum execution time per bid decision

2. **Winner Determination:**
   - Highest bidder wins the item
   - Winner pays the second-highest bid (Vickrey pricing)
   - Ties broken by random selection with equal probability

3. **Information Revelation:**
   - **Public Information:** Winner identity, final price paid
   - **Private Information:** All other bid amounts remain confidential

---

## Scoring and Rankings

### Utility Calculation (Per Game)
**Game Utility = Σ(Value of Won Items) - Total Amount Paid**

**Note:** Unspent budget does NOT contribute to utility score. Teams are incentivized to spend strategically rather than hoard money.

### Challenge and Overall Scoring

- **Stage Score:** Sum of utilities across all 5 games in any stage
- **Challenge Score:** Sum of utilities across all two stages

### Example Scoring:
**Game 1:** Win Item 5 (utility=8) for price=3, Item 12 (utility=15) for price=7  
→ **Game 1 Utility = (8 + 15) - (3 + 7) = 13**

**Game 2:** Win Item 3 (utility=12) for price=5  
→ **Game 2 Utility = 12 - 5 = 7**

**Challenge Score = 13 + 7 + ... (across all 5 games)**

### Ranking Criteria
1. **Primary:** Total utility earned in respective stage
2. **Tiebreaker 1:** Highest individual item utility captured
3. **Tiebreaker 2:** Most items won
4. **Final Tiebreaker:** Team registration timestamp

---

## Technical Implementation

### Code Submission Requirements

1. **Programming Language:** Python 3.11+
2. **Submission Method:** Upload your code to Moodle
3. **Entry Point:** Teams must implement the detailed `bidding_agent` interface
4. **Dependencies:** Only standard library + numpy, scipy allowed (no external APIs)

### Interface Requirements

```python
class BiddingAgent:
   def __init__(self, team_id: str, valuation_vector: dict, budget: int, auction_items_sequence: list):
      self.team_id = team_id
      self.valuation_vector = valuation_vector
      self.budget = budget
      self.available_items = auction_items_sequence
      self.utility = 0
   
   def _update_available_budget(self, item_id: str, winning_team: str, price_paid: float):
      if winning_team == self.team_id:
         self.budget -= price_paid         

   def update_after_each_round(self, item_id: str, winning_team: str, price_paid: float):
      """
      Update the information as you wish
      """
      self._update_available_budget(item_id, winning_team, price_paid)
      self.utility += (self.valuation_vector[item_id] - price_paid)
      # Other updates you wish to implement goes here
      return True

   def bidding_function(self, item_id):
      """
      Args:
         current_budget (float): Remaining budget for this stage
         item_id (int): ID of current item being auctioned (0-19)
         round_number (int): Current auction round (1-15)
         valuation_vector (list): Your team's utilities for all 20 items
         auction_sequence (list): Ordered list of all 15 item_ids to be auctioned
      
      Returns:
         float: Your bid amount (0 <= bid <= current_budget)
      """
      # Your strategy implementation here
      return bid_amount
```

### Performance Requirements
- **Execution Time:** Maximum 2 seconds per bid decision
- **Memory Limit:** 256MB per function call
- **Error Handling:** Invalid returns treated as $0 bid
- **Logging:** Teams can print debug info (captured but not shared)

### Testing and Validation
- **Local Testing:** Sample tournament data provided for strategy development
- **Validation Server:** Teams can test submissions before official tournaments
- **Code Review:** Basic automated checks for compliance and security

---

## Rules and Fair Play

### Prohibited Actions
- **System Abuse:** No attempts to exploit timing, computational limits, or platform vulnerabilities
- **Code Sharing:** Each team must develop original bidding algorithms

### Code Requirements
- **No External Communication:** Code cannot access internet, files, external resources, or make any external calls
- **Computational Fairness:** No attempts to consume excessive resources or slow down other teams

### Penalties
- **Minor Violations:** Warning and resubmission opportunity
- **Major Violations:** Team disqualification and forfeit of prizes
- **Technical Violations:** Function timeout/error treated as $0 bid for that round

---

## Prizes and Recognition

### Awards
- **1st Place:** AGT Champion certificates + 5 bonus points to final grade
- **2nd Place:** AGT Runner-up certificates + 3 bonus points to final grade  
- **All Stage 2 Teams:** 2 bonus points to final grade
- **Participation Recognition:** 1 bonus point to final grade
- **Best Strategy Innovation:** Additional +1 bonus point to final grade (awarded to most creative algorithmic approach)

### Post-Competition Analysis
- **Strategy Showcase:** Top teams present their approaches
- **Data Release:** Anonymized tournament data for further analysis
- **Theory Discussion:** Connecting observed behaviors to AGT concepts

---

## Technical Support and Resources

### Development Support
**TA Support:** Available for technical questions and debugging

### Resources Provided
- **API Documentation:** Detailed function specifications and examples
- **Sample Code:** Basic bidding strategy templates
- **Test Data:** Historical valuation vectors and tournament scenarios  
- **Validation Tools:** Local testing framework matching tournament environment

### Communication Channels
- **Course Forum:** Technical questions and clarifications
- **Git Repository:** Code submission and version control
- **Tournament Dashboard:** Live results and team standings during competition

---

## Getting Started

### Quick Start Checklist
1. ✅ Form team of 3 students (use the Moodle forum if needed)
2. ✅ Register team and clone Git repository
3. ✅ Implement and test basic bidding function
4. ✅ Submit to tournament

### Strategy Development Tips
- **Start Simple:** Begin with basic strategies (e.g., bid utility value, bid fraction of budget)
- **Analyze Correlation:** Identify which items are likely to be highly contested
- **Budget Planning:** Consider saving budget for later high-value items vs. securing early wins
- **Opponent Modeling:** Think about how rational opponents might bid
- **Testing:** Use provided tools to simulate different scenarios
---

*This competition combines theoretical AGT concepts with practical algorithm development, providing hands-on experience with auction mechanisms, strategic thinking, and computational game theory. May the best strategy win!*