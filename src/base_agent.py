"""
Base Agent Interface for AGT Competition
This file should be provided to students as a template
"""

from typing import Dict, List


class BiddingAgent:
    """
    Base class for bidding agents in the AGT Competition.
    Teams must implement this interface for their bidding strategy.
    """
    
    def __init__(self, team_id: str, valuation_vector: Dict[str, float], 
                 budget: float, auction_items_sequence: List[str]):
        """
        Initialize the bidding agent.
        
        Args:
            team_id: Unique identifier for the team
            valuation_vector: Dictionary mapping item_id to valuation
                             e.g., {"item_0": 15.3, "item_1": 8.2, ...}
            budget: Initial budget (typically 60)
            auction_items_sequence: List of item_ids that will be auctioned (15 items)
                                   Note: You know WHICH items but not the ORDER
        """
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.initial_budget = budget
        self.auction_items_sequence = auction_items_sequence
        self.utility = 0
        self.items_won = []
        
        # Students can add custom attributes here for their strategy
        # Examples:
        # self.beliefs = {}  # For Bayesian updates
        # self.opponent_models = {}
        # self.round_history = []
    
    def _update_available_budget(self, item_id: str, winning_team: str, price_paid: float):
        """
        Internal method to update budget after auction.
        DO NOT MODIFY - this is called automatically by the system.
        
        Args:
            item_id: ID of the auctioned item
            winning_team: ID of the winning team
            price_paid: Price paid by the winner (second-highest bid)
        """
        if winning_team == self.team_id:
            self.budget -= price_paid
            self.items_won.append(item_id)
    
    def update_after_each_round(self, item_id: str, winning_team: str, price_paid: float):
        """
        Called after each auction round with public information.
        Students can use this to update their beliefs, opponent models, etc.
        
        Args:
            item_id: ID of the item that was auctioned
            winning_team: ID of the team that won
            price_paid: Price paid (second-highest bid)
        
        Returns:
            True if update successful
        """
        # Update budget and utility (handled by system)
        self._update_available_budget(item_id, winning_team, price_paid)
        
        if winning_team == self.team_id:
            self.utility += (self.valuation_vector[item_id] - price_paid)
        
        # Students can add their own logic here
        # Examples:
        # - Update beliefs about opponent valuations
        # - Track bidding patterns
        # - Adjust strategy for future rounds
        
        return True
    
    def bidding_function(self, item_id: str) -> float:
        """
        Decide how much to bid for the current item.
        This is the main method students need to implement.
        
        Args:
            item_id: ID of the current item being auctioned
        
        Returns:
            float: Your bid amount (must be 0 <= bid <= current_budget)
        
        Note:
            - You have 2 seconds to return a bid
            - Bids exceeding budget will be automatically capped
            - Invalid returns or timeouts result in a 0 bid
            - This is a second-price sealed-bid auction (Vickrey auction)
        """
        # STUDENTS: IMPLEMENT YOUR BIDDING STRATEGY HERE
        
        # Simple example strategy: bid your true valuation (truthful bidding)
        # This is optimal in standard second-price auctions without budget constraints
        bid = self.valuation_vector.get(item_id, 0)
        
        # Ensure bid doesn't exceed budget
        bid = min(bid, self.budget)
        
        return bid
