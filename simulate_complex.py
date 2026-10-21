import os
import shutil
import tempfile
import pytest
from engine import SelfHealingEngine

def setup_complex_workspace():
    workspace = tempfile.mkdtemp(prefix="fable_complex_")
    
    # 1. The Complex Trading Engine (with a critical math bug)
    module_code = """
import math
from typing import List, Dict

class PyramidingEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.balance = initial_capital
        self.open_positions: List[Dict] = []
        
    def calculate_position_size(self, entry_price: float, stop_loss: float, risk_pct: float = 0.02) -> float:
        \"\"\"Calculates position size based on account risk and distance to stop loss.\"\"\"
        if entry_price <= stop_loss:
            raise ValueError("Long entry price must be strictly greater than stop loss.")
            
        risk_amount = self.balance * risk_pct
        stop_loss_distance = entry_price - stop_loss
        
        # BUG: Intentionally dividing by entry_price instead of stop_loss_distance
        # This causes massive under-allocation or liquidation in leveraged scenarios.
        position_size = risk_amount / entry_price 
        
        return round(position_size, 4)

    def execute_pyramid_scale_in(self, current_price: float, atr: float):
        \"\"\"Scales into a winning position if price moves 1 ATR in our favor.\"\"\"
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
"""
    with open(os.path.join(workspace, "trading_engine.py"), "w") as f:
        f.write(module_code.strip())

    # 2. The Strict Financial Test Suite
    test_code = """
import pytest
from trading_engine import PyramidingEngine

def test_position_sizing_logic():
    engine = PyramidingEngine(initial_capital=10000.0)
    
    # 2% risk on 10k = $200 risk.
    # Entry at 50, Stop Loss at 40. Distance = $10.
    # Correct Position Size = $200 / $10 = 20 units.
    
    size = engine.calculate_position_size(entry_price=50.0, stop_loss=40.0, risk_pct=0.02)
    assert size == 20.0, f"Catastrophic Risk Failure: Expected 20 units, got {size}"

def test_pyramid_scale_in():
    engine = PyramidingEngine(initial_capital=10000.0)
    
    # Primary entry
    initial_size = engine.calculate_position_size(50.0, 40.0, 0.02)
    engine.open_positions.append({'entry': 50.0, 'size': initial_size, 'type': 'primary'})
    
    # Price moves 1 ATR ($5) in our favor to $55. ATR = 5.
    engine.execute_pyramid_scale_in(current_price=55.0, atr=5.0)
    
    assert len(engine.open_positions) == 2
    
    # 1% risk on 10k = $100 risk. 
    # Entry at $55, Stop Loss at $45 (55 - 2*5). Distance = $10.
    # Correct Scale-in Size = $100 / $10 = 10 units.
    scale_in_size = engine.open_positions[1]['size']
    assert scale_in_size == 10.0, f"Pyramiding Risk Failure: Expected 10 units, got {scale_in_size}"
"""
    with open(os.path.join(workspace, "test_trading.py"), "w") as f:
        f.write(test_code.strip())

    return workspace

if __name__ == "__main__":
    print("========================================================")
    print("🚀 STARTING FABLE ENTERPRISE BOSS LEVEL: ALGO TRADING")
    print("========================================================")
    
    workspace = setup_complex_workspace()
    original_dir = os.getcwd()
    os.chdir(workspace)
    
    print("\n❌ Initial Pytest Status (Expected Fail):")
    pytest.main(["-q", "test_trading.py"])
    
    engine = SelfHealingEngine()
    prompt = (
        "The PyramidingEngine in trading_engine.py has a critical position sizing bug. "
        "It is calculating position_size by dividing risk_amount by entry_price. "
        "It MUST divide risk_amount by stop_loss_distance instead. "
        "Fix trading_engine.py so test_trading.py passes."
    )
    
    try:
        engine.run(prompt)
    finally:
        os.chdir(original_dir)
        print(f"\n📁 Complex workspace preserved at: {workspace}")
