# AGT Auto-Bidding Competition System

## Overview

This is the competition platform for the AGT 2025-2026 Auto-Bidding Challenge. The system orchestrates multi-stage auction tournaments where teams submit bidding agents that compete in sequential second-price sealed-bid (Vickrey) auctions.

## Features

- **Two-Stage Tournament**: Qualification round (Stage 1) followed by championship round (Stage 2)
- **Second-Price Sealed-Bid Auctions**: Vickrey auction mechanism with budget constraints
- **Valuation Generation**: Automated generation of item valuations per competition rules
- **Timeout Enforcement**: 2-second execution limit per bid decision
- **Comprehensive Logging**: Detailed logs for course staff, public results for teams
- **Leaderboard with Tiebreakers**: Proper ranking with multiple tiebreaker criteria
- **Agent Validation**: Tools to validate agent submissions before competition

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. Clone or download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python main.py --mode validate --validate examples/truthful_bidder.py
```

## Project Structure

```
AGT_2026/
├── src/                          # Core system modules
│   ├── base_agent.py            # Agent interface template
│   ├── config.py                # Configuration constants
│   ├── valuation_generator.py   # Valuation generation
│   ├── auction_engine.py        # Auction execution
│   ├── game_manager.py          # Game orchestration
│   ├── agent_manager.py         # Agent loading and execution
│   ├── tournament_manager.py    # Tournament management
│   ├── results_manager.py       # Results and reporting
│   └── utils.py                 # Utility functions and data models
├── examples/                     # Example bidding agents
│   ├── truthful_bidder.py       # Truthful bidding strategy
│   ├── budget_aware_bidder.py   # Budget-conscious strategy
│   ├── strategic_bidder.py      # Opponent modeling strategy
│   └── random_bidder.py         # Random baseline
├── teams/                        # Team submissions (create this)
│   ├── team1/
│   │   └── bidding_agent.py
│   └── team2/
│       └── bidding_agent.py
├── results/                      # Competition results (generated)
├── logs/                         # Detailed logs (generated)
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── agt_competition_rules.md     # Official competition rules
├── design.md                     # System design document
└── README.md                     # This file
```

## For Students: Creating Your Agent

### 📚 Student Resources

- **[STUDENT_GUIDE.md](STUDENT_GUIDE.md)** - Comprehensive implementation guide with examples
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for common tasks
- **[simulator.py](simulator.py)** - Local testing tool to test your agent

### 1. Agent Template

Your bidding agent must implement the `BiddingAgent` class interface. See `src/base_agent.py` for the complete template.

### 2. Required Methods

```python
class BiddingAgent:
    def __init__(self, team_id, valuation_vector, budget, auction_items_sequence):
        # Initialize your agent
        pass
    
    def bidding_function(self, item_id) -> float:
        # Return your bid for the current item
        # Must return a float: 0 <= bid <= current_budget
        pass
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        # Update your beliefs/strategy after each round
        pass
```

### 3. Creating Your Submission

1. Create a directory in `teams/` with your team name:
```bash
mkdir teams/your_team_name
```

2. Copy the base agent template:
```bash
cp src/base_agent.py teams/your_team_name/bidding_agent.py
```

3. Implement your `bidding_function` method with your strategy

4. Test your agent:
```bash
python main.py --mode validate --validate teams/your_team_name/bidding_agent.py
```

### 4. Allowed Dependencies

- Standard library (all modules)
- numpy
- scipy

**No external APIs, file I/O, or network access allowed!**

### 5. Example Strategies

See the `examples/` directory for reference implementations:
- **truthful_bidder.py**: Bids exact valuation (optimal without budget constraints)
- **budget_aware_bidder.py**: Scales bids based on remaining budget
- **strategic_bidder.py**: Models opponents from observed behavior
- **random_bidder.py**: Baseline random strategy

### 6. Testing Your Agent

#### Validation
```bash
# Validate your agent interface
python main.py --mode validate --validate teams/your_team_name/bidding_agent.py
```

#### Simulator (Recommended for Development)
Test your agent locally against example strategies:

```bash
# Run 10 games against all example agents
python simulator.py --your-agent teams/your_team_name/bidding_agent.py --num-games 10

# Test against specific opponent
python simulator.py --your-agent teams/your_team_name/bidding_agent.py \
                    --opponent examples/strategic_bidder.py --num-games 20

# Reproducible testing with seed
python simulator.py --your-agent teams/your_team_name/bidding_agent.py \
                    --num-games 50 --seed 42

# Verbose output for debugging
python simulator.py --your-agent teams/your_team_name/bidding_agent.py \
                    --num-games 3 --verbose
```

**The simulator provides:**
- Win rate against each opponent
- Average utility and ranking
- Budget utilization statistics  
- Performance assessment and recommendations
- Detailed game-by-game results

## For Course Staff: Running the Competition

### Running Full Tournament

Run both Stage 1 and Stage 2:
```bash
python main.py --mode tournament --teams-dir teams --output-dir results --verbose
```

### Running Single Stage

Stage 1 only:
```bash
python main.py --mode stage --stage 1 --teams-dir teams --output-dir results
```

Stage 2 only (with pre-qualified teams):
```bash
python main.py --mode stage --stage 2 --teams-dir qualified_teams --output-dir results
```

### Testing with Example Agents

Create test teams from examples:
```bash
# Copy examples to teams directory for testing
cp -r examples teams/example_team1
mv teams/example_team1/truthful_bidder.py teams/example_team1/bidding_agent.py

cp -r examples teams/example_team2
mv teams/example_team2/budget_aware_bidder.py teams/example_team2/bidding_agent.py

# Add more teams as needed...

# Run tournament
python main.py --mode tournament --teams-dir teams --verbose
```

### Command Line Options

```
--mode              : tournament | stage | validate
--teams-dir         : Directory containing team submissions (default: teams)
--output-dir        : Directory for results (default: results)
--stage             : Stage number 1 or 2 (for stage mode)
--validate          : Path to agent file (for validate mode)
--timeout           : Bid execution timeout in seconds (default: 2.0)
--seed              : Random seed for reproducibility (optional)
--log-file          : Custom log file path (optional)
--verbose           : Enable verbose logging
```

### Results Structure

After running a competition:

```
results/
├── stage1/
│   ├── arena_1/
│   │   ├── game_1_detailed.json    # Full details (course staff)
│   │   ├── game_1_public.json      # Public results (students)
│   │   └── ...
│   ├── stage1_complete.json
│   └── stage1_leaderboard.csv
├── stage2/
│   ├── arena_championship/
│   │   └── ...
│   ├── stage2_complete.json
│   └── stage2_leaderboard.csv
└── final_report.txt                 # Human-readable summary
```

## Competition Rules Summary

- **Items**: 20 total, 15 randomly selected per game
- **Budget**: 60 units per game
- **Rounds**: 15 auction rounds per game
- **Games**: 5 games per stage
- **Auction Type**: Second-price sealed-bid (Vickrey)
- **Timeout**: 2 seconds per bid decision
- **Scoring**: Utility = Σ(Value of Won Items) - Total Amount Paid

### Valuation Distribution

- **6 items**: High-value for all teams (U[10, 20])
- **4 items**: Low-value for all teams (U[1, 10])
- **10 items**: Mixed values (U[1, 20])

### Ranking Criteria

1. Total utility across all games
2. Highest single item utility captured (tiebreaker 1)
3. Most items won (tiebreaker 2)
4. Team registration timestamp (tiebreaker 3)

## Troubleshooting

### Agent Not Loading

- Ensure `bidding_agent.py` exists in team directory
- Check class name is exactly `BiddingAgent`
- Verify all required methods are implemented

### Timeout Errors

- Your `bidding_function` is taking > 2 seconds
- Optimize your code or reduce complexity
- Avoid infinite loops

### Import Errors

- Only use allowed libraries: standard library, numpy, scipy
- No external dependencies or custom packages

### Budget Exceeded

- Bids exceeding budget are automatically capped
- Check logs for warnings about capped bids

## Development and Testing

### Running Tests

```bash
# Validate all example agents
for agent in examples/*.py; do
    python main.py --mode validate --validate "$agent"
done
```

### Reproducible Results

Use `--seed` for reproducible valuation generation:
```bash
python main.py --mode tournament --seed 42 --verbose
```

### Verbose Logging

Enable detailed logging to see all bids and decisions:
```bash
python main.py --mode tournament --verbose --log-file logs/debug.log
```

## Support

For technical questions or issues:
- Review the official competition rules: `agt_competition_rules.md`
- Check the design document: `design.md`
- Examine example agents in `examples/`
- Contact course staff via the course forum

## License

This competition system is for educational use in the AGT 2025-2026 course.

---

*Good luck to all teams! May the best strategy win!* 🏆
