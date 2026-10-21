from src.math_engine.calculator import Calculator

def test_withdraw():
    calc = Calculator()
    # Pytest ONLY checks this specific happy path. 
    # It passes, so standard CI/CD would deploy this vulnerable code to production!
    assert calc.apply_withdrawal(100, 20) == 80
