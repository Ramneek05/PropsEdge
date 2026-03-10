import pandas as pd

def prepare_features(df):
    if df.empty:
        return df  # Return empty DataFrame if input is empty
    df = df.sort_values("GAME_DATE")

    df["PRA"] = df["PTS"] + df["REB"] + df["AST"]
    df["PTS_AST"] = df["PTS"] + df["AST"]
    df["PTS_REB"] = df["PTS"] + df["REB"]
    df["REB_AST"] = df["REB"] + df["AST"]
    df["3PM"] = df["FG3M"]

    # Rolling averages; min_periods=1 handles early season when players are still getting up to speed
    df["rolling_pts"] = df["PTS"].rolling(5, min_periods=1).mean()
    df["rolling_reb"] = df["REB"].rolling(5, min_periods=1).mean()
    df["rolling_ast"] = df["AST"].rolling(5, min_periods=1).mean()
    df["rolling_pra"] = df["PRA"].rolling(5, min_periods=1).mean()
    df["rolling_pts_ast"] = df["PTS_AST"].rolling(5, min_periods=1).mean()
    df["rolling_pts_reb"] = df["PTS_REB"].rolling(5, min_periods=1).mean()
    df["rolling_reb_ast"] = df["REB_AST"].rolling(5, min_periods=1).mean()
    df["rolling_3pm"] = df["3PM"].rolling(5, min_periods=1).mean()

    # Convert minutes to numeric
    df["MIN"] = pd.to_numeric(df["MIN"], errors="coerce")

    df = df.dropna()
    return df