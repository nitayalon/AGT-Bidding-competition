"""
AGT Auto-Bidding Competition - Team Agent

Team Name: [YOUR TEAM NAME]
Members:
  - [Student 1 Name and ID]
  - [Student 2 Name and ID]
  - [Student 3 Name and ID]

Strategy (high-level):
- Budget-aware, value-weighted bidding with adaptive market learning.
- Uses observed clearing prices (second-highest bids) to estimate market competitiveness.
- Allocates budget proportionally to the value of likely-best remaining items (knapsack-style pacing).
- Becomes more aggressive near end-game and selectively competes for top-tier items.

Key Features:
- Online market model (EWMA + lightweight ridge linear fit) from (my_value, observed_price) pairs
- Value-tiering by my valuation percentiles (top / mid / low)
- Proportional budget allocation using remaining unseen values (risk-aware pacing)
- End-game budget burn-down with guardrails
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

import numpy as np


class BiddingAgent:
    """
    Bidding agent for the AGT Auto-Bidding Competition (sequential second-price auctions).

    Required methods:
      - __init__(team_id, valuation_vector, budget, opponent_teams)
      - bidding_function(item_id) -> float
      - update_after_each_round(item_id, winning_team, price_paid) -> bool
    """

    # -------------------------------
    # Initialization
    # -------------------------------
    def __init__(self, team_id: str, valuation_vector: Dict[str, float],
                 budget: float, opponent_teams: List[str]):
        # Required attributes (DO NOT REMOVE)
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = float(budget)
        self.initial_budget = float(budget)
        self.opponent_teams = opponent_teams
        self.utility = 0.0
        self.items_won: List[str] = []

        # Game state
        self.rounds_completed = 0
        self.total_rounds = 15  # fixed
        self.seen_items: Set[str] = set()

        # Opponent tracking (lightweight)
        self.opponent_wins = {opp: 0 for opp in opponent_teams}
        self.opponent_paid_prices = {opp: [] for opp in opponent_teams}  # prices paid when they win

        # Price / market learning
        self.price_history: List[float] = []
        self.myval_history: List[float] = []  # my valuations for observed items (for fitting)
        self.ewma_price = 8.0  # conservative initial guess
        self.ewma_ratio = 0.55  # expected (price / my_value) baseline
        self._ewma_alpha = 0.25  # responsiveness

        # Online linear fit accumulators for y ~ a + b*x (x=my_value, y=price_paid)
        self._n_fit = 0
        self._sum_x = 0.0
        self._sum_y = 0.0
        self._sum_xx = 0.0
        self._sum_xy = 0.0

        # Pre-compute valuation stats and tiers (fast lookups)
        values = np.array(list(valuation_vector.values()), dtype=float)
        self._val_mean = float(values.mean()) if values.size else 0.0
        self._val_std = float(values.std()) if values.size else 1.0
        self._val_max = float(values.max()) if values.size else 0.0

        # Percentile thresholds (tiers)
        # Using percentiles makes the agent robust across different valuation vectors.
        self._p70 = float(np.percentile(values, 70)) if values.size else 0.0
        self._p85 = float(np.percentile(values, 85)) if values.size else 0.0
        self._p93 = float(np.percentile(values, 93)) if values.size else 0.0

        # Sorted values per item (for remaining-value budget allocation)
        self._items_all = list(valuation_vector.keys())

        # Small epsilon to avoid division issues
        self._eps = 1e-9

    # -------------------------------
    # System-managed budget update (DO NOT MODIFY)
    # -------------------------------
    def _update_available_budget(self, item_id: str, winning_team: str, price_paid: float):
        """DO NOT MODIFY - Managed by the system."""
        if winning_team == self.team_id:
            self.budget -= float(price_paid)
            self.items_won.append(item_id)

    # -------------------------------
    # After-round update (learning)
    # -------------------------------
    def update_after_each_round(self, item_id: str, winning_team: str, price_paid: float):
        # System updates (DO NOT REMOVE)
        self._update_available_budget(item_id, winning_team, price_paid)

        if winning_team == self.team_id:
            self.utility += (self.valuation_vector[item_id] - float(price_paid))

        self.rounds_completed += 1
        self.seen_items.add(item_id)

        # Track opponents
        if winning_team:
            if winning_team in self.opponent_wins:
                self.opponent_wins[winning_team] += 1
                if price_paid > 0:
                    self.opponent_paid_prices[winning_team].append(float(price_paid))

        # Track observed market prices and fit a lightweight model
        if price_paid > 0:
            y = float(price_paid)
            x = float(self.valuation_vector.get(item_id, 0.0))

            self.price_history.append(y)
            self.myval_history.append(x)

            # EWMA updates (robust, cheap)
            self.ewma_price = (1.0 - self._ewma_alpha) * self.ewma_price + self._ewma_alpha * y

            if x > 1e-6:
                ratio = float(np.clip(y / x, 0.05, 1.25))
                self.ewma_ratio = (1.0 - self._ewma_alpha) * self.ewma_ratio + self._ewma_alpha * ratio

            # Online fit accumulators
            # (only fit when my valuation is informative)
            if x > 0.5:
                self._n_fit += 1
                self._sum_x += x
                self._sum_y += y
                self._sum_xx += x * x
                self._sum_xy += x * y

        return True

    # -------------------------------
    # Core bidding method
    # -------------------------------
    def bidding_function(self, item_id: str) -> float:
        my_value = float(self.valuation_vector.get(item_id, 0.0))

        # Early exits
        if my_value <= 0.0 or self.budget <= 0.0:
            return 0.0

        rounds_left = self.total_rounds - self.rounds_completed
        if rounds_left <= 0:
            return 0.0

        # 1) Estimate market clearing price for this kind of item
        pred_price = self._predict_price(my_value)

        # Expected surplus proxy (very noisy, but useful for filtering low ROI)
        expected_surplus = my_value - pred_price

        # 2) Determine tier (top / mid / low) relative to *my* valuation distribution
        tier = self._value_tier(my_value)

        # 3) Budget pacing: allocate budget proportionally to likely best remaining items
        max_bid_cap = self._budget_cap_for_item(item_id=item_id, my_value=my_value, tier=tier, rounds_left=rounds_left)

        # 4) Decide base bid fraction (shading) and competitive adjustment
        progress = self.rounds_completed / self.total_rounds  # 0..1

        # Conservative filter: avoid bidding on negative-ROI items unless late and top-tier
        if expected_surplus <= 0.0 and not (tier == "top" and rounds_left <= 3):
            return 0.0

        # Baseline shading by tier and game phase
        if tier == "top":
            # Stronger competition; near-truthful but with pacing constraints
            base_frac = 0.90 + 0.07 * progress  # 0.90 -> 0.97
        elif tier == "mid":
            base_frac = 0.70 + 0.18 * progress  # 0.70 -> 0.88
        else:
            base_frac = 0.45 + 0.12 * progress  # 0.45 -> 0.57

        # Competitive adjustment: if market price is close to my value, bid a bit closer to value
        comp = float(np.clip(pred_price / max(my_value, self._eps), 0.0, 1.5))
        if tier == "top" and comp > 0.75:
            base_frac = min(0.99, base_frac + 0.04)
        elif tier != "top" and comp > 0.85:
            base_frac = min(0.95, base_frac + 0.03)

        # End-game: spend remaining budget more aggressively
        if rounds_left <= 2:
            base_frac = min(1.0, base_frac + 0.08)

        # Convert to bid
        bid = my_value * base_frac

        # If we really want to compete, make sure we aren't *way* below predicted price
        # (helps avoid losing high-value items due to overly shaded bids)
        if tier == "top" and rounds_left <= 6:
            bid = max(bid, min(my_value, pred_price * 1.08))

        # Apply caps + safety
        bid = min(bid, max_bid_cap, self.budget)
        bid = max(0.0, float(bid))

        # Keep precision stable (system rounds anyway, but this avoids floating noise)
        return float(np.round(bid, 2))

    # -------------------------------
    # Helper methods
    # -------------------------------
    def _value_tier(self, my_value: float) -> str:
        """Classify item value tier based on my valuation percentiles."""
        if my_value >= self._p93:
            return "top"
        if my_value >= self._p70:
            return "mid"
        return "low"

    def _predict_price(self, my_value: float) -> float:
        """
        Predict a reasonable second price based on observed history.

        Uses a blend of:
          - EWMA ratio * my_value (fast, robust)
          - Lightweight ridge linear fit from (my_value, observed_price)
          - EWMA absolute price floor/anchor (prevents extreme underestimates early)
        """
        # EWMA ratio prediction
        ratio_pred = self.ewma_ratio * my_value

        # Linear prediction when we have enough samples
        lin_pred = ratio_pred
        if self._n_fit >= 4:
            n = float(self._n_fit)
            xbar = self._sum_x / n
            ybar = self._sum_y / n
            denom = (self._sum_xx - (self._sum_x * self._sum_x) / n)

            # Ridge regularization (stabilizes when denom is small)
            ridge = 5.0
            denom_r = denom + ridge

            if denom_r > self._eps:
                b = (self._sum_xy - (self._sum_x * self._sum_y) / n) / denom_r
                # shrink slope to plausible range
                b = float(np.clip(b, 0.05, 1.10))
                a = ybar - b * xbar
                lin_pred = a + b * my_value

        # Blend: more weight to fit as we collect evidence
        w_fit = float(np.clip(self._n_fit / 10.0, 0.0, 0.6))
        pred = (1.0 - w_fit) * ratio_pred + w_fit * lin_pred

        # Anchor: early rounds, avoid predicting too low just because ratio is small
        # Use ewma_price as soft floor scaled by a factor
        soft_floor = 0.55 * self.ewma_price
        pred = max(pred, soft_floor)

        # Keep in sane bounds
        pred = float(np.clip(pred, 0.0, my_value * 0.98))

        return pred

    def _budget_cap_for_item(self, item_id: str, my_value: float, tier: str, rounds_left: int) -> float:
        """
        Compute a per-round cap that:
          - prevents early budget exhaustion,
          - concentrates spend on high-valued items,
          - still allows aggressive end-game spending.

        Key idea: allocate remaining budget proportionally to this item's share among the
        *best likely remaining items* (top-m remaining values), then apply tier- and
        phase-based multipliers.
        """
        # Basic per-round pacing
        budget_per_round = self.budget / max(1, rounds_left)

        # Remaining unseen items (including current)
        remaining_items = [it for it in self._items_all if it not in self.seen_items]
        if item_id not in remaining_items:
            remaining_items.append(item_id)

        remaining_values = [float(self.valuation_vector.get(it, 0.0)) for it in remaining_items]
        remaining_values_sorted = sorted(remaining_values, reverse=True)

        # Consider the best "m" values among items that could still appear
        m = min(rounds_left, len(remaining_values_sorted))
        top_m_sum = sum(remaining_values_sorted[:m]) if m > 0 else max(my_value, 1.0)

        # Proportional allocation: spend share of budget aligned with value share
        share = my_value / max(top_m_sum, self._eps)
        alloc = self.budget * share

        # Tier multipliers
        if tier == "top":
            tier_mult = 2.4
            per_round_mult = 3.0
        elif tier == "mid":
            tier_mult = 1.7
            per_round_mult = 2.1
        else:
            tier_mult = 1.1
            per_round_mult = 1.4

        # Phase multipliers: become more permissive near the end
        progress = self.rounds_completed / self.total_rounds
        phase_mult = 1.1 + 0.9 * progress  # 1.1 -> 2.0

        # Candidate caps
        cap_by_alloc = alloc * tier_mult * phase_mult
        cap_by_pacing = budget_per_round * per_round_mult

        # End-game burn down: allow spending a large fraction of remaining budget
        if rounds_left <= 3:
            burn = 0.85 if tier == "top" else (0.75 if tier == "mid" else 0.60)
            cap_by_pacing = max(cap_by_pacing, self.budget * burn)

        cap = min(self.budget, my_value, cap_by_alloc, cap_by_pacing)

        # Always allow a minimal meaningful bid for top-tier items (avoid being too capped)
        if tier == "top":
            cap = max(cap, min(my_value, budget_per_round * 1.6))

        return float(np.clip(cap, 0.0, self.budget))
