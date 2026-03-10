import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

def train_model(df, stat):

    df = df.sort_values("GAME_DATE")

    # Minutes trend (HUGE factor)
    df["rolling_min"] = df["MIN"].rolling(5).mean()
    df["rolling_stat"] = df[stat].rolling(5).mean()

    df = df.dropna()

    features = ["rolling_min", "rolling_stat"]

    X = df[features]
    y = df[stat]

    if len(X) < 5:
        return None, None, None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = Ridge()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    score = r2_score(y_test, preds)

    latest = X.iloc[-1].values.reshape(1, -1)

    return model, score, latest