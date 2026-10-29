"""
Sample Module: Calculator
Contains basic arithmetic operations with deliberate edge-case bugs.
Used to demonstrate AI-assisted testing and bug detection in software engineering.
"""

def calculate(operation: str, a: float, b: float) -> float:
    """
    Performs arithmetic calculation based on operation name.
    
    Supported operations:
        - 'add': returns a + b
        - 'subtract': returns a - b
        - 'multiply': returns a * b
        - 'divide': returns a / b (should raise ZeroDivisionError when b == 0)
    
    DELIBERATE BUGS:
    1. Division by zero: Returns 0.0 instead of raising ZeroDivisionError.
    2. Invalid operation string does not raise ValueError properly when empty.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments a and b must be numeric")

    op = str(operation).strip().lower()
    
    if op == "add":
        return float(a + b)
    elif op == "subtract":
        return float(a - b)
    elif op == "multiply":
        return float(a * b)
    elif op == "divide":
        # DELIBERATE BUG: Returns 0.0 instead of raising ZeroDivisionError when b == 0
        if b == 0:
            return 0.0
        return float(a / b)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
