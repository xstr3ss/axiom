class Calculator:
    def apply_withdrawal(self, balance: int, amount: int) -> int:
        """
        Apply a withdrawal to the given balance.

        Raises:
            ValueError: If the balance is negative, the withdrawal amount is negative,
                        or the withdrawal amount exceeds the current balance.
        """
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative")
        if amount > balance:
            raise ValueError("Withdrawal amount exceeds balance")
        return balance - amount
