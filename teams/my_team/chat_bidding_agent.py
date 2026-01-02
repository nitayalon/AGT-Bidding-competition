from enum import Enum


class BiddingAgent:
    TOTAL_ROUNDS = 15
    class ItemCategory(Enum):
        HIGH = "High"
        LOW = "Low"
        MIXED = "Mixed"

    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.remaining_counts = {
            self.ItemCategory.HIGH: 6,
            self.ItemCategory.LOW: 4,
            self.ItemCategory.MIXED: 10
        }
        self.total_items_remaining = sum(self.remaining_counts.values())
        self.rounds_completed = 0

    def get_likelihood(self, valuation: float, category: ItemCategory) -> float:
        """Returns P(valuation | category) based on Uniform distributions"""
        if category == self.ItemCategory.HIGH:
            return 0.1 if 10 <= valuation <= 20 else 0.0
        elif category == self.ItemCategory.LOW:
            return 0.1 if 1 <= valuation <= 10 else 0.0
        return 0.05 if 1 <= valuation <= 20 else 0.0
        

    def calculate_probabilities(self, my_valuation: float) -> dict[ItemCategory, float]:
        """Calculates P(Category | MyValuation)"""
        if self.total_items_remaining == 0:
            return {self.ItemCategory.HIGH: 0, self.ItemCategory.MIXED: 0, self.ItemCategory.LOW: 0}

        p_cats = {
            self.ItemCategory.HIGH: self.remaining_counts[self.ItemCategory.HIGH] / self.total_items_remaining,
            self.ItemCategory.MIXED: self.remaining_counts[self.ItemCategory.MIXED] / self.total_items_remaining,
            self.ItemCategory.LOW: self.remaining_counts[self.ItemCategory.LOW] / self.total_items_remaining,
        }
        
        p_high = (6/20) * (1/10) if my_valuation >=10 else 0
        p_mixed = (10/20) * (1/20) if my_valuation >=1 else 0
        p_low = (4/20) * (1/10) if my_valuation <= 10 else 0
        p_val = p_high + p_mixed + p_low
        
        p_cats_given_val = {}
        
        for cat in self.ItemCategory:
            p_val_given_cat = self.get_likelihood(my_valuation, cat)
            p_cats_given_val[cat] = p_val_given_cat * p_cats[cat] / p_val
                        
        return p_cats_given_val

    def _update_available_budget(self, item_id: str, winning_team: str, 
                                 price_paid: float):
        """
        Internal method to update budget after auction.
        DO NOT MODIFY - This is called automatically by the system.
        
        Args:
            item_id: ID of the auctioned item
            winning_team: ID of the winning team
            price_paid: Price paid by winner
        """
        if winning_team == self.team_id:
            self.budget -= price_paid
            # self.items_won.append(item_id)

    def update_after_each_round(self, item_id, winning_team, price_paid):
        self._update_available_budget(item_id, winning_team, price_paid)
        self.rounds_completed += 1
        # --- UPDATE PRIORS BASED ON OBSERVATION ---
        # We must guess what category the PREVIOUS item was to update counts.
        # This is where we use the price_paid as a signal.
        
        guessed_category = self.ItemCategory.MIXED # Default guess
        if price_paid > 10:
            if self.valuation_vector[item_id] < 10:
                if self.remaining_counts[self.ItemCategory.MIXED] <= 0:
                    self.remaining_counts[self.ItemCategory.LOW] -= 1
                    self.remaining_counts[self.ItemCategory.MIXED] = 0
                else:
                    self.remaining_counts[self.ItemCategory.MIXED] -= 1
                self.total_items_remaining -= 1
                return True
        if price_paid > 11.0:
            # Very likely a High category item where competition drove price up
            if self.remaining_counts[self.ItemCategory.HIGH] > 0:
                guessed_category = self.ItemCategory.HIGH
        elif price_paid < 8.0:
             # Likely a Low category
             if self.remaining_counts[self.ItemCategory.LOW] > 0:
                guessed_category = self.ItemCategory.LOW
        
        # Decrement the count for the guessed category
        if self.remaining_counts[guessed_category] > 0:
            self.remaining_counts[guessed_category] -= 1
            
        self.total_items_remaining -= 1
        return True

    def _calculate_ongoing_round_risk_adjustment(self):
        progress = self.rounds_completed / self.TOTAL_ROUNDS
        if progress < 0.33:
            risk_adjustment = 0.05
        elif progress < 0.67:
            risk_adjustment = 0.1
        else:
            risk_adjustment = 0.15
        return 0.85 + risk_adjustment

    def bidding_function(self, item_id):
        my_valuation = self.valuation_vector.get(item_id, 0)
        rounds_remaining = self.TOTAL_ROUNDS - self.rounds_completed
        
        if my_valuation <= 0 or self.budget <= 0.05 or rounds_remaining == 0:
            return 0.0
        
        probabilities_for_each_category = self.calculate_probabilities(my_valuation)
        
        ongoing_round_risk_adjustment = self._calculate_ongoing_round_risk_adjustment()
        # --- STRATEGY: ADAPT SHADING ---
        # If I am 90% sure this is a "High" item (Common Value), 
        # I must bid truthfully because opponents also value it highly.
        # If I think it's "Mixed", I can shade (bid 70%) to save money.
        
        base_shading = 0.7  # Default aggressive shading
        
        # As probability of High Competition goes up, shading approaches 1.0 (Truthful)
        # Formula: 0.7 + (0.3 * P(High))
        
        # we belive its a mixed item so we want to win it at all costs
        if probabilities_for_each_category[self.ItemCategory.MIXED] > probabilities_for_each_category[self.ItemCategory.HIGH]:
            adaptive_shading = 1

        # we belive its a high item so we want to make other players pay more for it without winning necessarily winning it ourselves
        else:
            adaptive_shading = base_shading + (0.3 * probabilities_for_each_category[self.ItemCategory.HIGH])
        
        bid = my_valuation * adaptive_shading * ongoing_round_risk_adjustment
        bid = min(bid, self.budget)
        return float(max(0.0, min(bid, self.budget)))