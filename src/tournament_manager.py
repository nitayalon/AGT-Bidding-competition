"""
Tournament Manager for AGT Competition
Manages tournament stages and arenas
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

from src.config import STAGE1_GAMES, STAGE2_GAMES, ARENA_SIZE
from src.game_manager import GameManager
from src.valuation_generator import ValuationGenerator
from src.auction_engine import AuctionEngine
from src.agent_manager import AgentManager
from src.results_manager import ResultsManager
from src.utils import GameResult, StageResult, Team


logger = logging.getLogger(__name__)


class TournamentManager:
    """
    Manages the complete tournament including both stages.
    
    Stage 1: Qualification Round
    - Divide teams into 5-team arenas
    - Run 5 games per arena
    - Top scorer from each arena advances
    
    Stage 2: Championship Round
    - All qualified teams in single arena
    - Run 5 games
    - Determine final rankings
    """
    
    def __init__(self, valuation_generator: ValuationGenerator,
                 results_manager: ResultsManager,
                 timeout_seconds: float = 2.0):
        """
        Initialize tournament manager.
        
        Args:
            valuation_generator: Valuation generator instance
            results_manager: Results manager instance
            timeout_seconds: Timeout for agent bid execution
        """
        self.valuation_generator = valuation_generator
        self.results_manager = results_manager
        self.timeout_seconds = timeout_seconds
        
        self.stage1_results = None
        self.stage2_results = None
    
    def create_arenas(self, teams: List[Team]) -> Dict[str, List[Team]]:
        """
        Divide teams into arenas of size ARENA_SIZE.
        
        Args:
            teams: List of Team objects
        
        Returns:
            Dictionary mapping arena_id to list of teams
        """
        arenas = {}
        
        for i in range(0, len(teams), ARENA_SIZE):
            arena_id = str(i // ARENA_SIZE + 1)
            arena_teams = teams[i:i + ARENA_SIZE]
            arenas[arena_id] = arena_teams
            logger.info(f"Arena {arena_id}: {[t.team_id for t in arena_teams]}")
        
        return arenas
    
    def run_arena_games(self, arena_id: str, arena_teams: List[Team], 
                       stage: int, num_games: int) -> List[GameResult]:
        """
        Run all games for a single arena.
        
        Args:
            arena_id: Arena identifier
            arena_teams: List of teams in this arena
            stage: Competition stage (1 or 2)
            num_games: Number of games to run
        
        Returns:
            List of GameResult objects
        """
        logger.info(f"=== Running Arena {arena_id} (Stage {stage}) ===")
        
        game_results = []
        
        # Prepare team_agents mapping
        team_agents = {team.team_id: team.agent_file_path for team in arena_teams}
        
        for game_num in range(1, num_games + 1):
            try:
                # Create fresh instances for each game
                auction_engine = AuctionEngine()
                agent_manager = AgentManager(timeout_seconds=self.timeout_seconds)
                
                game_manager = GameManager(
                    stage=stage,
                    arena_id=arena_id,
                    game_number=game_num,
                    valuation_generator=self.valuation_generator,
                    auction_engine=auction_engine,
                    agent_manager=agent_manager
                )
                
                # Run the game
                game_result = game_manager.run_game(team_agents)
                game_results.append(game_result)
                
                # Save game results
                self.results_manager.save_game_result(game_result)
                
            except Exception as e:
                logger.error(f"Error running game {game_num} in arena {arena_id}: {e}", exc_info=True)
        
        return game_results
    
    def run_stage1(self, teams: List[Team]) -> Tuple[StageResult, List[Team]]:
        """
        Run Stage 1: Qualification Round.
        
        Args:
            teams: List of all registered teams
        
        Returns:
            Tuple of (StageResult, qualified_teams)
        """
        logger.info("=" * 80)
        logger.info("STARTING STAGE 1: QUALIFICATION ROUND")
        logger.info("=" * 80)
        
        # Create arenas
        arenas = self.create_arenas(teams)
        
        # Run games for each arena (sequential as per design decision)
        arena_results = {}
        arena_winners = []
        
        for arena_id, arena_teams in arenas.items():
            game_results = self.run_arena_games(
                arena_id=arena_id,
                arena_teams=arena_teams,
                stage=1,
                num_games=STAGE1_GAMES
            )
            
            arena_results[arena_id] = game_results
            
            # Determine arena winner
            team_reg_times = {team.team_id: team.registration_timestamp for team in arena_teams}
            leaderboard = self.results_manager.generate_leaderboard(game_results, team_reg_times)
            
            if leaderboard:
                winner_id = leaderboard[0]['team_id']
                winner_team = next(t for t in arena_teams if t.team_id == winner_id)
                arena_winners.append(winner_team)
                logger.info(f"Arena {arena_id} Winner: {winner_id} (Utility: {leaderboard[0]['total_utility']:.2f})")
        
        # Generate overall Stage 1 leaderboard
        all_games = [game for games in arena_results.values() for game in games]
        all_team_reg_times = {team.team_id: team.registration_timestamp for team in teams}
        overall_leaderboard = self.results_manager.generate_leaderboard(all_games, all_team_reg_times)
        
        # Create stage result
        stage_result = StageResult(
            stage=1,
            arena_results=arena_results,
            leaderboard=overall_leaderboard,
            timestamp=datetime.now()
        )
        
        # Save stage results
        self.results_manager.save_stage_result(stage_result)
        self.stage1_results = stage_result
        
        logger.info("=" * 80)
        logger.info(f"STAGE 1 COMPLETE - {len(arena_winners)} teams advance to Stage 2")
        logger.info("=" * 80)
        
        return stage_result, arena_winners
    
    def run_stage2(self, qualified_teams: List[Team]) -> StageResult:
        """
        Run Stage 2: Championship Round.
        
        Args:
            qualified_teams: List of teams qualified from Stage 1
        
        Returns:
            StageResult with final rankings
        """
        logger.info("=" * 80)
        logger.info("STARTING STAGE 2: CHAMPIONSHIP ROUND")
        logger.info("=" * 80)
        
        # All qualified teams in single arena
        arena_id = "championship"
        
        game_results = self.run_arena_games(
            arena_id=arena_id,
            arena_teams=qualified_teams,
            stage=2,
            num_games=STAGE2_GAMES
        )
        
        # Generate final leaderboard
        team_reg_times = {team.team_id: team.registration_timestamp for team in qualified_teams}
        final_leaderboard = self.results_manager.generate_leaderboard(game_results, team_reg_times)
        
        # Create stage result
        stage_result = StageResult(
            stage=2,
            arena_results={arena_id: game_results},
            leaderboard=final_leaderboard,
            timestamp=datetime.now()
        )
        
        # Save stage results
        self.results_manager.save_stage_result(stage_result)
        self.stage2_results = stage_result
        
        # Display final results
        logger.info("=" * 80)
        logger.info("STAGE 2 COMPLETE - FINAL RANKINGS")
        logger.info("=" * 80)
        
        for rank, entry in enumerate(final_leaderboard, 1):
            logger.info(
                f"Rank {rank}: {entry['team_id']} | "
                f"Utility: {entry['total_utility']:.2f} | "
                f"Items: {entry['total_items_won']}"
            )
        
        return stage_result
    
    def run_full_tournament(self, teams: List[Team]) -> Tuple[StageResult, StageResult]:
        """
        Run complete tournament (both stages).
        
        Args:
            teams: List of all registered teams
        
        Returns:
            Tuple of (stage1_result, stage2_result)
        """
        logger.info("=" * 80)
        logger.info("AGT AUTO-BIDDING COMPETITION - STARTING TOURNAMENT")
        logger.info(f"Total Teams: {len(teams)}")
        logger.info("=" * 80)
        
        # Run Stage 1
        stage1_result, qualified_teams = self.run_stage1(teams)
        
        # Run Stage 2
        stage2_result = self.run_stage2(qualified_teams)
        
        # Generate final report
        self.results_manager.generate_final_report(stage1_result, stage2_result)
        
        logger.info("=" * 80)
        logger.info("🏆 TOURNAMENT COMPLETE 🏆")
        logger.info("=" * 80)
        
        return stage1_result, stage2_result
