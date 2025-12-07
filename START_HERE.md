# AGT Auto-Bidding Competition - Student Package

Welcome to the AGT 2025-2026 Auto-Bidding Challenge!

## 📦 Package Contents

This package contains everything you need to participate in the competition.

### 📖 Documentation (Start Here!)

1. **[STUDENT_GUIDE.md](STUDENT_GUIDE.md)** - Complete implementation guide (READ THIS FIRST!)
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for common tasks
3. **[STUDENT_RESOURCES.md](STUDENT_RESOURCES.md)** - Overview of all resources
4. **[agt_competition_rules.md](agt_competition_rules.md)** - Official competition rules
5. **[README.md](README.md)** - System documentation

### 🛠️ Tools

- **[simulator.py](simulator.py)** - Test your agent locally before submission
- **[main.py](main.py)** - Competition system (for course staff)
- **[setup_test.py](setup_test.py)** - Quick setup helper for testing

### 📝 Templates

- **[AGENT_TEMPLATE.py](AGENT_TEMPLATE.py)** - Annotated template to start your implementation
- **[src/base_agent.py](src/base_agent.py)** - Minimal agent interface

### 💡 Examples

The `examples/` folder contains 4 reference strategies:
- `truthful_bidder.py` - Bids true valuation
- `budget_aware_bidder.py` - Budget-conscious strategy
- `strategic_bidder.py` - Opponent modeling strategy
- `random_bidder.py` - Random baseline

### 📁 Your Workspace

- **teams/** - Create your team folder here (e.g., `teams/my_team/`)
- **results/** - Auto-generated results (created when you run tests)
- **logs/** - Auto-generated logs (created when you run tests)

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Your Team
```bash
# Option A: Manual
mkdir teams/my_team
cp AGENT_TEMPLATE.py teams/my_team/bidding_agent.py

# Option B: Use setup script to create test teams
python setup_test.py
```

### 3. Edit Your Agent
Open `teams/my_team/bidding_agent.py` and implement your strategy in the `bidding_function` method.

### 4. Test Your Agent
```bash
# Validate interface
python main.py --mode validate --validate teams/my_team/bidding_agent.py

# Test with simulator (10 games)
python simulator.py --your-agent teams/my_team/bidding_agent.py --num-games 10
```

---

## 📚 Recommended Reading Order

1. **Day 1:** Read STUDENT_GUIDE.md sections 1-3
2. **Day 2:** Study examples and implement basic strategy
3. **Day 3-4:** Test and iterate using simulator
4. **Day 5:** Optimize and prepare submission

---

## 🧪 Testing Your Agent

### Quick Test
```bash
python simulator.py --your-agent teams/my_team/bidding_agent.py --num-games 10
```

### Thorough Test (Recommended before submission)
```bash
python simulator.py --your-agent teams/my_team/bidding_agent.py --num-games 50 --seed 42
```

### Debug Single Game
```bash
python simulator.py --your-agent teams/my_team/bidding_agent.py --num-games 1 --verbose
```

---

## 📋 Competition Rules Summary

- **Budget:** 60 units per game
- **Rounds:** 15 auction rounds per game
- **Games:** 5 games per stage
- **Auction:** Second-price sealed-bid (Vickrey)
- **Timeout:** 2 seconds per bid
- **Scoring:** Utility = Σ(Values Won) - Σ(Prices Paid)

**See [agt_competition_rules.md](agt_competition_rules.md) for complete rules.**

---

## ✅ Pre-Submission Checklist

- [ ] Agent file named `bidding_agent.py`
- [ ] Class named `BiddingAgent`
- [ ] Validation passes
- [ ] Tested with 50+ games
- [ ] No timeout errors
- [ ] Team names in code header
- [ ] Only allowed dependencies (stdlib, numpy, scipy)

---

## 🆘 Getting Help

1. Check **QUICK_REFERENCE.md** for common issues
2. Read **STUDENT_GUIDE.md** debugging section
3. Test with `--verbose` flag
4. Ask on course forum
5. Attend office hours

---

## 📤 Submission

Submit your `bidding_agent.py` file to Moodle by the deadline.

**Submission Deadline:** [TBD - Check course website]

---

## 🏆 Good Luck!

May the best strategy win!

---

## 📞 Support

- **Course Forum:** [Link TBD]
- **Office Hours:** [Times TBD]
- **TA Contact:** [Email TBD]

---

## 📦 Package Structure

```
AGT_Competition_Package/
├── STUDENT_GUIDE.md          # Main guide (start here!)
├── QUICK_REFERENCE.md        # Quick lookup
├── STUDENT_RESOURCES.md      # Resources overview
├── AGENT_TEMPLATE.py         # Annotated template
├── README.md                 # System documentation
├── agt_competition_rules.md # Official rules
├── design.md                 # System design (optional)
│
├── simulator.py              # Testing tool
├── main.py                   # Competition system
├── setup_test.py            # Test setup helper
├── requirements.txt         # Dependencies
│
├── src/                     # System source code
│   ├── base_agent.py       # Agent interface
│   ├── config.py           # Configuration
│   └── ... (other modules)
│
├── examples/                # Example strategies
│   ├── truthful_bidder.py
│   ├── budget_aware_bidder.py
│   ├── strategic_bidder.py
│   └── random_bidder.py
│
├── teams/                   # Your work area
│   └── [create your team folder here]
│
├── results/                 # Auto-generated
└── logs/                    # Auto-generated
```

---

**Version:** 1.0.0  
**Date:** December 2025  
**Course:** AGT 2025-2026
