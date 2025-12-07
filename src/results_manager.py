"""
Results Manager for AGT Competition
Handles logging, storage, and reporting of competition results
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import pandas as pd

from src.utils import GameResult, StageResult, save_json, format_utility
from src.config import RESULTS_DIR, LOGS_DIR


logger = logging.getLogger(__name__)


class ResultsManager:
    """
    Manages all competition results: logging, storage, and reporting.
    
    Responsibilities:
    - Save detailed logs for course staff
    - Generate team-visible results (winner + price only)
    - Create leaderboards with tiebreakers
    - Export results in multiple formats
    - Generate analytics reports
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize results manager.
        
        Args:
            output_dir: Base directory for results (default from config)
        """
        self.output_dir = output_dir if output_dir else RESULTS_DIR
        self.logs_dir = LOGS_DIR
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def save_game_result(self, game_result: GameResult):
        """
        Save complete game results (detailed for course staff).
        
        Args:
            game_result: Complete game results
        """
        # Create directory structure
        stage_dir = os.path.join(self.output_dir, f"stage{game_result.stage}")
        arena_dir = os.path.join(stage_dir, f"arena_{game_result.arena_id}")
        os.makedirs(arena_dir, exist_ok=True)
        
        # Save full game results
        filename = f"game_{game_result.game_number}_detailed.json"
        filepath = os.path.join(arena_dir, filename)
        
        save_json(game_result.to_dict(), filepath)
        logger.info(f"Saved detailed game results to {filepath}")
        
        # Save team-visible results (winner + price only)
        team_visible_file = f"game_{game_result.game_number}_public.json"
        team_filepath = os.path.join(arena_dir, team_visible_file)
        
        public_data = {
            "game_id": game_result.game_id,
            "stage": game_result.stage,
            "game_number": game_result.game_number,
            "rounds": [round_result.to_public_dict() for round_result in game_result.auction_log]
        }
        
        save_json(public_data, team_filepath)
        logger.info(f"Saved public game results to {team_filepath}")
    
    def save_stage_result(self, stage_result: StageResult):
        """
        Save complete stage results.
        
        Args:
            stage_result: Complete stage results including leaderboard
        """
        stage_dir = os.path.join(self.output_dir, f"stage{stage_result.stage}")
        os.makedirs(stage_dir, exist_ok=True)
        
        # Save full stage results
        filename = f"stage{stage_result.stage}_complete.json"
        filepath = os.path.join(stage_dir, filename)
        
        save_json(stage_result.to_dict(), filepath)
        logger.info(f"Saved stage results to {filepath}")
        
        # Save leaderboard as CSV
        leaderboard_file = f"stage{stage_result.stage}_leaderboard.csv"
        leaderboard_path = os.path.join(stage_dir, leaderboard_file)
        
        df = pd.DataFrame(stage_result.leaderboard)
        df.to_csv(leaderboard_path, index=False)
        logger.info(f"Saved leaderboard to {leaderboard_path}")
    
    def generate_leaderboard(self, arena_games: List[GameResult], 
                            team_registration_times: Dict[str, datetime] = None) -> List[Dict]:
        """
        Generate leaderboard from multiple games with proper tiebreakers.
        
        Ranking criteria:
        1. Total utility across all games
        2. Highest single item utility captured
        3. Most items won
        4. Team registration timestamp (earliest wins)
        
        Args:
            arena_games: List of GameResult objects from the arena
            team_registration_times: Optional dict of team_id -> registration time
        
        Returns:
            List of dicts with team rankings
        """
        # Aggregate results across all games
        team_aggregates = {}
        
        for game in arena_games:
            for team_id, team_result in game.team_results.items():
                if team_id not in team_aggregates:
                    team_aggregates[team_id] = {
                        'team_id': team_id,
                        'total_utility': 0.0,
                        'max_single_item_utility': 0.0,
                        'total_items_won': 0,
                        'games_played': 0,
                        'total_spent': 0.0,
                        'total_valuation_won': 0.0
                    }
                
                agg = team_aggregates[team_id]
                agg['total_utility'] += team_result.utility
                agg['max_single_item_utility'] = max(
                    agg['max_single_item_utility'], 
                    team_result.max_single_item_utility
                )
                agg['total_items_won'] += len(team_result.items_won)
                agg['games_played'] += 1
                agg['total_spent'] += team_result.budget_spent
                agg['total_valuation_won'] += team_result.total_valuation_won
        
        # Add registration times if provided
        if team_registration_times:
            for team_id, agg in team_aggregates.items():
                agg['registration_time'] = team_registration_times.get(
                    team_id, datetime.max
                ).timestamp()
        else:
            for agg in team_aggregates.values():
                agg['registration_time'] = 0
        
        # Sort with tiebreakers
        leaderboard = sorted(
            team_aggregates.values(),
            key=lambda x: (
                -x['total_utility'],                    # Primary: highest utility
                -x['max_single_item_utility'],          # Tiebreaker 1
                -x['total_items_won'],                  # Tiebreaker 2
                x['registration_time']                  # Tiebreaker 3: earliest
            )
        )
        
        # Add ranks
        for rank, entry in enumerate(leaderboard, 1):
            entry['rank'] = rank
        
        return leaderboard
    
    def generate_final_report(self, stage1_result: StageResult, 
                             stage2_result: StageResult = None) -> str:
        """
        Generate final competition report.
        
        Args:
            stage1_result: Results from Stage 1
            stage2_result: Optional results from Stage 2
        
        Returns:
            Path to generated report file
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AGT AUTO-BIDDING COMPETITION - FINAL REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Stage 1 Summary
        report_lines.append("STAGE 1: QUALIFICATION ROUND")
        report_lines.append("-" * 80)
        report_lines.append(f"Arenas: {len(stage1_result.arena_results)}")
        report_lines.append(f"Total Teams: {len(stage1_result.leaderboard)}")
        report_lines.append("")
        
        report_lines.append("Top Team from Each Arena (Advanced to Stage 2):")
        for arena_id, games in stage1_result.arena_results.items():
            leaderboard = self.generate_leaderboard(games)
            if leaderboard:
                winner = leaderboard[0]
                report_lines.append(
                    f"  Arena {arena_id}: {winner['team_id']} "
                    f"(Utility: {format_utility(winner['total_utility'])}, "
                    f"Items: {winner['total_items_won']})"
                )
        
        report_lines.append("")
        
        # Stage 2 Summary (if available)
        if stage2_result:
            report_lines.append("STAGE 2: CHAMPIONSHIP ROUND")
            report_lines.append("-" * 80)
            
            leaderboard = stage2_result.leaderboard
            
            report_lines.append("Final Rankings:")
            for i, entry in enumerate(leaderboard[:10], 1):  # Top 10
                report_lines.append(
                    f"  {i}. {entry['team_id']}: "
                    f"Utility={format_utility(entry['total_utility'])}, "
                    f"Items={entry['total_items_won']}, "
                    f"Max Item Utility={format_utility(entry['max_single_item_utility'])}"
                )
            
            report_lines.append("")
            report_lines.append("🏆 CHAMPION: " + leaderboard[0]['team_id'])
            if len(leaderboard) > 1:
                report_lines.append("🥈 RUNNER-UP: " + leaderboard[1]['team_id'])
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # Save report
        report_text = "\n".join(report_lines)
        report_path = os.path.join(self.output_dir, "final_report.txt")
        
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Generated final report: {report_path}")
        print(report_text)  # Also print to console
        
        return report_path
    
    def export_all_results_csv(self):
        """Export all results to CSV files for analysis"""
        logger.info("Exporting all results to CSV...")
        
        # Implementation for CSV export of all games
        # Can be extended as needed
        pass
