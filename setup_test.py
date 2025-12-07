"""
Quick setup script to create test teams from example agents
"""

import os
import shutil
from pathlib import Path


def setup_test_teams():
    """Create test teams from example agents"""
    
    # Create teams directory
    teams_dir = Path("teams")
    teams_dir.mkdir(exist_ok=True)
    
    # Example agents to use
    examples = [
        ("truthful_bidder.py", "team_truthful"),
        ("budget_aware_bidder.py", "team_budget_aware"),
        ("strategic_bidder.py", "team_strategic"),
        ("random_bidder.py", "team_random"),
        ("truthful_bidder.py", "team_truthful_2"),  # Duplicate for more teams
    ]
    
    examples_dir = Path("examples")
    
    for example_file, team_name in examples:
        team_dir = teams_dir / team_name
        team_dir.mkdir(exist_ok=True)
        
        source = examples_dir / example_file
        dest = team_dir / "bidding_agent.py"
        
        if source.exists():
            shutil.copy(source, dest)
            print(f"✓ Created {team_name} from {example_file}")
        else:
            print(f"✗ Could not find {example_file}")
    
    print(f"\n✓ Setup complete! Created {len(examples)} test teams in teams/")
    print("\nRun the tournament with:")
    print("python main.py --mode tournament --teams-dir teams --verbose")


if __name__ == "__main__":
    setup_test_teams()
