"""
Run a single arena from JSON configuration.
This allows running multiple arenas in parallel across different terminals.

Usage:
    python run_arena.py arena_config.json

arena_config.json format:
{
    "arena_id": "1",
    "stage": 1,
    "num_games": 25,
    "timeout": 3.0,
    "seed": 115470,
    "teams": ["team1", "team2", "team3", "team4", "team5"],
    "output_dir": "results",
    "teams_dir": "teams"
}
"""

import json
import sys
import logging
import os
import random
import numpy as np
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

from src.config import RESULTS_DIR, LOGS_DIR
from src.tournament_manager import TournamentManager
from src.valuation_generator import ValuationGenerator
from src.results_manager import ResultsManager
from src.utils import Team


def setup_logging(arena_id: str, log_dir: str):
    """Setup logging for this arena."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"arena_{arena_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_arena_config(config_file: str) -> dict:
    """Load arena configuration from JSON file."""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_teams(team_ids: list, teams_dir: str) -> list:
    """Load Team objects for the specified team IDs."""
    teams_path = Path(teams_dir)
    
    # Load team registration
    registration_file = teams_path / "team_registration.json"
    team_members_map = {}
    if registration_file.exists():
        with open(registration_file, 'r', encoding='utf-8') as f:
            registration_data = json.load(f)
            for team_data in registration_data.get('teams', []):
                team_members_map[team_data['team_name']] = team_data.get('members', [])
    
    # Load agent filename mapping
    agent_filenames_file = teams_path.parent / "agent_filenames.json"
    agent_filenames = {}
    if agent_filenames_file.exists():
        with open(agent_filenames_file, 'r', encoding='utf-8') as f:
            agent_filenames = json.load(f)
    
    teams = []
    for team_id in team_ids:
        team_dir = teams_path / team_id
        if not team_dir.exists():
            logging.error(f"Team directory not found: {team_dir}")
            continue
        
        # Get agent filename
        agent_filename = agent_filenames.get(team_id, "bidding_agent.py")
        agent_file = team_dir / agent_filename
        
        if not agent_file.exists():
            logging.error(f"Agent file not found: {agent_file}")
            continue
        
        # Get member IDs
        members = team_members_map.get(team_id, [])
        
        team = Team(
            team_id=team_id,
            team_name=team_id,
            agent_file_path=str(agent_file.absolute()),
            registration_timestamp=datetime.fromtimestamp(team_dir.stat().st_ctime),
            members=members
        )
        teams.append(team)
        logging.info(f"Loaded team: {team_id} (members: {len(members)})")
    
    return teams


def run_arena(config: dict):
    """Run a single arena with the given configuration."""
    logger = setup_logging(config['arena_id'], config.get('log_dir', LOGS_DIR))
    
    logger.info("=" * 80)
    logger.info(f"RUNNING ARENA {config['arena_id']} (Stage {config['stage']})")
    logger.info("=" * 80)
    logger.info(f"Teams: {config['teams']}")
    logger.info(f"Games: {config['num_games']}")
    logger.info(f"Timeout: {config['timeout']} seconds")
    logger.info(f"Seed: {config['seed']}")
    
    # Set random seed
    random.seed(config['seed'])
    np.random.seed(config['seed'])
    
    # Generate different seeds for each game's valuations
    num_games = config['num_games']
    game_seeds = [random.randint(1, 1000000) for _ in range(num_games)]
    logger.info(f"Generated {num_games} unique seeds for game valuations")
    
    # Load teams
    teams = load_teams(config['teams'], config.get('teams_dir', 'teams'))
    if len(teams) != len(config['teams']):
        logger.error(f"Could not load all teams. Expected {len(config['teams'])}, got {len(teams)}")
        return False
    
    # Initialize managers
    valuation_generator = ValuationGenerator(random_seed=config['seed'])
    results_manager = ResultsManager(output_dir=config.get('output_dir', RESULTS_DIR))
    tournament_manager = TournamentManager(
        valuation_generator=valuation_generator,
        results_manager=results_manager,
        timeout_seconds=config['timeout']
    )
    
    # Run arena games with different valuations per game
    try:
        game_results = tournament_manager.run_arena_games(
            arena_id=config['arena_id'],
            arena_teams=teams,
            stage=config['stage'],
            num_games=config['num_games'],
            game_valuation_seeds=game_seeds  # Pass the seeds instead of fixed valuations
        )
        
        logger.info(f"Completed {len(game_results)} games for Arena {config['arena_id']}")
        
        # Determine winner
        winner_team = tournament_manager.determine_arena_winner(teams, game_results)
        logger.info("=" * 80)
        logger.info(f"ARENA {config['arena_id']} WINNER: {winner_team.team_id}")
        logger.info("=" * 80)
        
        # Save arena summary
        arena_summary = {
            "arena_id": config['arena_id'],
            "stage": config['stage'],
            "winner": winner_team.team_id,
            "teams": team_ids,
            "num_games": len(game_results),
            "timestamp": datetime.now().isoformat()
        }
        
        summary_file = os.path.join(
            config.get('output_dir', RESULTS_DIR),
            f"stage{config['stage']}",
            f"arena_{config['arena_id']}",
            "arena_summary.json"
        )
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(arena_summary, f, indent=2)
        
        logger.info(f"Arena summary saved to {summary_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running arena {config['arena_id']}: {e}", exc_info=True)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_arena.py <arena_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}")
        sys.exit(1)
    
    config = load_arena_config(config_file)
    success = run_arena(config)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
