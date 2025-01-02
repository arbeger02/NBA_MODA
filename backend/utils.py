import pandas as pd
import numpy as np

# Function that applies a polynomial function to return the input values to a 0-100 scale (defaults to linear 1st degree polynomial)
def polynomial_return_to_scale(values, degree=1, normal_scaling=True):
    output = []
    old_min = min(values)
    old_max = max(values)

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