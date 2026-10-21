import math
from typing import List, Dict

class PyramidingEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.balance = initial_capital
        self.open_positions: List[Dict] = []
        
    def calculate_position_size(self, entry_price: float, stop_loss: float, risk_pct: float = 0.02) -> float:
        """Calculates position size based on account risk and distance to stop loss."""
        if entry_price <= stop_loss:
            raise ValueError("Long entry price must be strictly greater than stop loss.")
            
        risk_amount = self.balance * risk_pct
        stop_loss_distance = entry_price - stop_loss
        
        # BUG: Intentionally dividing by entry_price instead of stop_loss_distance
        position_size = risk_amount / entry_price 
        
        return round(position_size, 4)

    def execute_pyramid_scale_in(self, current_price: float, atr: float):
        """Scales into a winning position if price moves 1 ATR in our favor."""
        if not self.open_positions:
            return
            
        primary_pos = self.open_positions[0]
        if current_price >= primary_pos['entry'] + atr:
            # Second stage scale-in (half the original risk)
            new_size = self.calculate_position_size(current_price, current_price - (atr * 2), risk_pct=0.01)
            self.open_positions.append({
                'entry': current_price,
                'size': new_size,
                'type': 'scale-in'
            })
