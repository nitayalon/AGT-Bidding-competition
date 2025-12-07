# AGT Competition System - Design Document

## Overview
This document outlines the architecture for the AGT Auto-Bidding Competition platform. The system orchestrates multi-stage auction tournaments where teams submit bidding agents that compete in sequential second-price sealed-bid auctions.

---

## System Architecture

### Core Components

#### 1. **Valuation Generator** (`valuation_generator.py`)
**Purpose:** Generate item valuations for teams according to competition rules

**Key Functions:**
- `generate_valuation_vector(team_id: str) -> dict`: Generate 20-item valuation vector
  - 6 items: High-value for all teams (U[10,20])
  - 4 items: Low-value for all teams (U[1,10])
  - 10 items: Mixed values (U[1,20])
- `generate_arena_valuations(team_ids: list) -> dict`: Generate valuations for all teams in an arena
- Ensures consistent item categorization across teams within a game

**Data Structure:**
```python
{
    "team_id_1": {"item_0": 15.3, "item_1": 8.2, ..., "item_19": 12.7},
    "team_id_2": {"item_0": 14.8, "item_1": 7.9, ..., "item_19": 13.1},
    ...
}
```

---

#### 2. **Auction Engine** (`auction_engine.py`)
**Purpose:** Execute individual auction rounds using second-price sealed-bid mechanism

**Key Classes:**
- `AuctionRound`: Represents a single auction round

**Key Methods:**
- `collect_bids(agents: dict, item_id: str) -> dict`: Collect bids from all agents (2-second timeout)
- `determine_winner(bids: dict) -> tuple`: Determine winner and price (second-highest bid)
- `handle_ties(top_bidders: list) -> str`: Random tie-breaking
- `validate_bid(bid: float, budget: float) -> float`: Cap bids to available budget

**Return Format:**
```python
{
    "winner": "team_id",
    "price": 12.5,
    "item_id": "item_7",
    "all_bids": {"team_1": 15.0, "team_2": 12.5, ...}  # For logging only
}
```

---

#### 3. **Game Manager** (`game_manager.py`)
**Purpose:** Orchestrate a single game (15 auction rounds)

**Key Classes:**
- `Game`: Manages one complete game

**Responsibilities:**
- Initialize game with K=20 items, select random 15 for auction
- Randomly shuffle auction order
- Initialize all team agents with their valuations and budget (B=60)
- Execute 15 sequential auction rounds
- Update all agents after each round with public information
- Track team budgets, utilities, and items won
- Generate game summary and logs

**Game State Tracking:**
```python
{
    "team_id": {
        "budget": 45.3,
        "utility": 23.7,
        "items_won": ["item_3", "item_12"],
        "total_spent": 14.7,
        "valuation_sum": 38.4
    }
}
```

---

#### 4. **Tournament Manager** (`tournament_manager.py`)
**Purpose:** Manage tournament stages (Stage 1: Qualification, Stage 2: Championship)

**Key Classes:**
- `TournamentStage`: Manages one stage (5 games)
- `Arena`: Groups teams for parallel competition

**Stage 1 Workflow:**
1. Divide all teams into 5-team arenas
2. Run 5 games for each arena in parallel (or sequentially)
3. Track cumulative scores across 5 games
4. Identify top scorer from each arena
5. Advance winners to Stage 2

**Stage 2 Workflow:**
1. All qualified teams compete in single arena
2. Run 5 games
3. Track cumulative scores
4. Determine final rankings with tiebreakers

**Scoring Logic:**
- Primary: Total utility across all games in stage
- Tiebreaker 1: Highest single item utility captured
- Tiebreaker 2: Most items won
- Tiebreaker 3: Team registration timestamp

---

#### 5. **Agent Manager** (`agent_manager.py`)
**Purpose:** Load, validate, and execute team-submitted bidding agents

**Key Functions:**
- `load_agent(file_path: str, team_id: str) -> BiddingAgent`: Dynamically import team's code
- `validate_agent(agent: BiddingAgent) -> bool`: Check interface compliance
- `execute_bid_with_timeout(agent, item_id, timeout=2.0) -> float`: Execute with timeout
- `sandbox_agent(agent) -> None`: Apply security restrictions (no file I/O, network, etc.)

**Security Considerations:**
- Timeout enforcement (2 seconds)
- Memory limits (256MB)
- No external I/O allowed
- Exception handling (returns 0 bid on error)
- Resource monitoring

---

#### 6. **Results Manager** (`results_manager.py`)
**Purpose:** Track, store, and report competition results

**Key Functions:**
- `log_auction_result(round_data: dict) -> None`: Log individual auction outcomes
- `log_game_result(game_data: dict) -> None`: Log complete game results
- `generate_stage_leaderboard(stage_data: dict) -> DataFrame`: Create rankings
- `export_results(format: str) -> None`: Export to JSON/CSV/Excel
- `generate_analytics_report() -> None`: Post-competition analysis

**Data Persistence:**
```
results/
├── stage1/
│   ├── arena_1/
│   │   ├── game_1.json
│   │   ├── game_2.json
│   │   └── ...
│   └── arena_2/
│       └── ...
├── stage2/
│   └── ...
├── leaderboards/
│   ├── stage1_final.csv
│   └── stage2_final.csv
└── analytics/
    └── competition_report.html
```

---

#### 7. **Base Agent Interface** (`base_agent.py`)
**Purpose:** Define the interface that all team agents must implement

**Provided to Teams:**
```python
class BiddingAgent:
    def __init__(self, team_id: str, valuation_vector: dict, budget: int, auction_items_sequence: list):
        """Initialize agent with game parameters"""
        pass
    
    def _update_available_budget(self, item_id: str, winning_team: str, price_paid: float):
        """Internal budget tracking (provided)"""
        pass
    
    def update_after_each_round(self, item_id: str, winning_team: str, price_paid: float):
        """Called after each auction with public information"""
        pass
    
    def bidding_function(self, item_id: str) -> float:
        """Return bid for current item"""
        pass
```

---

#### 8. **Configuration Manager** (`config.py`)
**Purpose:** Centralized competition parameters

**Constants:**
```python
# Game Parameters
K_TOTAL_ITEMS = 20
T_AUCTION_ROUNDS = 15
INITIAL_BUDGET = 60

# Valuation Ranges
HIGH_VALUE_ITEMS = 6
LOW_VALUE_ITEMS = 4
MIXED_VALUE_ITEMS = 10

HIGH_VALUE_RANGE = (10, 20)
LOW_VALUE_RANGE = (1, 10)
MIXED_VALUE_RANGE = (1, 20)

# Competition Structure
STAGE1_GAMES = 5
STAGE2_GAMES = 5
ARENA_SIZE = 5

# Execution Limits
BID_TIMEOUT_SECONDS = 2.0
MEMORY_LIMIT_MB = 256

# Scoring
SCORING_WEIGHTS = {
    "utility": 1.0,
    "items_won": 0,
    "budget_remaining": 0
}
```

---

## Workflow Diagrams

### Complete Competition Flow
```
1. Load all team agents → Validate
2. Stage 1: Qualification
   ├── Divide teams into arenas (5 teams each)
   ├── For each arena:
   │   ├── Run 5 games
   │   └── Track cumulative scores
   └── Identify top scorer per arena → Stage 2
3. Stage 2: Championship
   ├── Single arena with qualified teams
   ├── Run 5 games
   └── Determine final rankings
4. Generate reports and analytics
```

### Single Game Flow
```
1. Generate valuations for all teams
2. Select 15 random items from 20
3. Shuffle auction order
4. Initialize agents with (team_id, valuations, budget, item_sequence)
5. For each of 15 rounds:
   a. Collect bids from all agents (timeout: 2s)
   b. Determine winner (highest bid)
   c. Calculate price (second-highest bid)
   d. Update winner's budget and utility
   e. Notify all agents with (item_id, winner_id, price)
6. Calculate final utilities and return results
```

### Single Auction Round Flow
```
1. Announce item_id to all agents
2. Call each agent.bidding_function(item_id) in parallel/sequential
3. Collect all bids (validate against budget, apply timeout)
4. Find highest bid → winner
5. Find second-highest bid → price
6. Handle ties with random selection
7. Update game state
8. Call all agents.update_after_each_round(item_id, winner, price)
9. Log round results
```

---

## Data Models

### Team
```python
@dataclass
class Team:
    team_id: str
    team_name: str
    agent_file_path: str
    registration_timestamp: datetime
    members: List[str]
```

### GameResult
```python
@dataclass
class GameResult:
    game_id: str
    arena_id: str
    stage: int
    timestamp: datetime
    team_results: Dict[str, TeamGameResult]
    auction_log: List[AuctionRound]
```

### TeamGameResult
```python
@dataclass
class TeamGameResult:
    team_id: str
    utility: float
    budget_spent: float
    items_won: List[str]
    valuation_vector: Dict[str, float]
    max_single_item_utility: float
```

---

## File Structure

```
agt_competition/
├── src/
│   ├── __init__.py
│   ├── config.py                  # Configuration and constants
│   ├── base_agent.py              # Agent interface (provided to students)
│   ├── valuation_generator.py    # Valuation generation logic
│   ├── auction_engine.py          # Single auction round execution
│   ├── game_manager.py            # Single game orchestration
│   ├── tournament_manager.py      # Stage and tournament management
│   ├── agent_manager.py           # Agent loading and execution
│   ├── results_manager.py         # Results tracking and export
│   └── utils.py                   # Helper functions
├── teams/                         # Team submissions
│   ├── team_1/
│   │   └── bidding_agent.py
│   ├── team_2/
│   │   └── bidding_agent.py
│   └── ...
├── results/                       # Competition results
│   ├── stage1/
│   ├── stage2/
│   └── analytics/
├── logs/                          # Detailed execution logs
├── tests/                         # Unit tests
│   ├── test_auction_engine.py
│   ├── test_game_manager.py
│   ├── test_valuation_generator.py
│   └── ...
├── examples/                      # Sample agents for students
│   ├── truthful_bidder.py
│   ├── random_bidder.py
│   └── budget_aware_bidder.py
├── main.py                        # Entry point for running competition
├── requirements.txt
└── README.md
```

---

## Testing Strategy

### Unit Tests
- **Valuation Generator**: Verify distribution correctness
- **Auction Engine**: Test winner determination, tie-breaking, pricing
- **Game Manager**: Validate game flow, state updates
- **Agent Manager**: Test timeout enforcement, security sandbox

### Integration Tests
- **Single Game**: Run complete game with sample agents
- **Tournament**: Run mini-tournament with 2 arenas

### Validation Tests
- **Agent Interface**: Validate sample student submissions
- **Scoring Logic**: Verify utility calculations and tiebreakers

---

## Security and Fair Play

### Agent Sandboxing
- Restrict file system access (no read/write)
- Block network access
- Limit CPU time (2-second timeout per bid)
- Limit memory (256MB)
- Catch and handle all exceptions

### Code Validation
- Check for required methods
- Verify return types
- Detect infinite loops (via timeout)
- Log all agent errors

---

## CLI Interface

```bash
# Run full competition
python main.py --teams-dir ./teams --output-dir ./results

# Run single stage
python main.py --stage 1 --teams-dir ./teams

# Run single game (testing)
python main.py --test-game --teams team1,team2,team3

# Validate agent
python main.py --validate ./teams/team1/bidding_agent.py

# Generate reports from existing results
python main.py --generate-report --results-dir ./results
```

---

## Implementation Priority

### Phase 1: Core Engine
1. Config and base classes
2. Valuation generator
3. Auction engine
4. Game manager

### Phase 2: Tournament Infrastructure
5. Agent manager (loading, validation, timeout)
6. Tournament manager
7. Results manager

### Phase 3: Tools and Testing
8. CLI interface
9. Example agents
10. Unit tests
11. Documentation

---

## Design Decisions

1. **Parallel vs Sequential Execution**: Arenas in Stage 1 will run sequentially for convenience, but the system will be designed to support parallel execution if needed.
2. **Logging and Reporting**: Document all decisions made throughout the competition with detailed logs. Report back only final results to participants. Course staff have access to full detailed logs.
3. **Agent State Persistence**: Agents CAN maintain evolving states between rounds and games (e.g., Bayesian belief updates). Agents are instantiated once per game and persist through all 15 rounds.
4. **Logging Verbosity**: 
   - **For Course Team**: As detailed as possible - all bids, decisions, timings, errors
   - **For Student Teams**: Only winner identity and price paid per round
5. **Replay System**: Yes - full replay capability from detailed logs for post-competition analysis
6. **Budget Validation**: Cap bids that exceed budget automatically and log a notification in the detailed log file

---

## Dependencies

```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
pytest>=7.3.0
pyyaml>=6.0
```

**Note:** Student agents restricted to standard library + numpy + scipy only.
