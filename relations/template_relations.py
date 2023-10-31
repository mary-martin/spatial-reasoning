from sklearn.linear_model import LinearRegression
import numpy as np

# Example data set
points = np.array([(1, 2), (2, 3), (3, 4), (5, 6), (6, 8), (7, 9)])

# Separate x and y coordinates
x = points[:, 0].reshape(-1, 1)
y = points[:, 1]

# Perform linear regression
reg = LinearRegression().fit(x, y)

# Calculate R-squared for linearity
r_squared = reg.score(x, y)

# Set the threshold for linearity
linearity_threshold = 0.9  # Adjust as needed

# Check if the set of points is approximately linear
if r_squared > linearity_threshold:
    print("The set of points is approximately linear.")
else:
    print("The set of points is not approximately linear.")

# Calculate the slope of the line
slope = reg.coef_[0]

# Set the threshold for diagonal or parallel alignment
alignment_threshold = 0.5  # Adjust as needed

# Check for diagonal or parallel alignment
if abs(slope) < alignment_threshold:
    print("The line is approximately parallel to the x-axis.")
elif abs(slope) > 1 / alignment_threshold:
    print("The line is approximately parallel to the y-axis.")
else:
    print("The line is diagonal.")
