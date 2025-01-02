import pandas as pd
import numpy as np

def polynomial_return_to_scale(values, degree=1, normal_scaling=True):
    """
    Applies a polynomial function to return the input values to a 0-100 scale 
    (defaults to linear 1st degree polynomial).

    Args:
        values (list or array-like): Input values to be scaled.
        degree (int): Degree of the polynomial. Defaults to 1 (linear).
        normal_scaling (bool): If True, performs normal scaling; if False, 
                               performs reverse scaling. Defaults to True.

    Returns:
        list: Scaled values between 0 and 100.
    """
    output = []
    old_min = min(values)
    old_max = max(values)

    # Handle division by zero
    if old_max**degree - old_min**degree == 0:
        print("Warning: Division by zero encountered in polynomial_return_to_scale. Setting scaling factor to 0.")
        a = 0  # Set scaling factor to 0
    else:
        # Calculate polynomial coefficient
        a = 100 / (old_max**degree - old_min**degree)

    # Apply the polynomial function to the values
    for v in values:
        if normal_scaling:
            # Normal scaling
            new_v = a * (v**degree - old_min**degree)
            output.append(new_v)
        else:
            # Reverse scaling
            new_v = -a * (v**degree - old_max**degree)
            output.append(new_v)

    return output