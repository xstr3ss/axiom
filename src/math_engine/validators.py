def check_positive(value):
    if value < 0:
        raise ValueError(f"Value {value} is not positive!")
    return True
