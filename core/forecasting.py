import numpy as np
from sklearn.linear_model import LinearRegression

def forecast(series, periods=3):
    y = series.values
    X = np.arange(len(y)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(len(y), len(y) + periods).reshape(-1, 1)
    return model.predict(future_X)