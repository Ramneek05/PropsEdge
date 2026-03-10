import requests
import pandas as pd
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
}

TEAM_ID_MAP = {
    1:  "ATL", 2:  "BOS", 3:  "NO",  4:  "CHI", 5:  "CLE",
    6:  "DAL", 7:  "DEN", 8:  "DET", 9:  "GS",  10: "HOU",
    11: "IND", 12: "LAC", 13: "LAL", 14: "MIA", 15: "MIL",
    16: "MIN", 17: "BKN", 18: "NY",  19: "ORL", 20: "PHI",
    21: "PHX", 22: "POR", 23: "SAC", 24: "SA",  25: "OKC",
    26: "UTAH",27: "WSH", 28: "TOR", 29: "MEM", 30: "CHA",
}

_DEFENSE_CACHE = {}


def build_defense_cache():
    global _DEFENSE_CACHE
    if _DEFENSE_CACHE:
        return

    print("[INFO] Building real defensive stats cache...")

    # Fetch full season games across two date ranges
    now = datetime.now()
    if now.month >= 10:
        season_start_year = now.year
    else:
        season_start_year = now.year - 1
    
    season_end_year = season_start_year + 1

    date_ranges = [
    f"{season_start_year}1001-{season_start_year}1031",
    f"{season_start_year}1101-{season_start_year}1130",
    f"{season_start_year}1201-{season_start_year}1231",
    f"{season_end_year}0101-{season_end_year}0131",
    f"{season_end_year}0201-{season_end_year}0228",
    f"{season_end_year}0301-{season_end_year}0331",
    f"{season_end_year}0401-{season_end_year}0430",
    f"{season_end_year}0501-{season_end_year}0531",
    f"{season_end_year}0601-{season_end_year}0630",
    ]
    all_events = []
    for d in date_ranges:
        try:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
                params={"limit": 200, "dates": d},
                headers=HEADERS,
                timeout=15,
            )
            all_events.extend(r.json().get("events", []))
        except Exception as e:
            print(f"[WARN] Could not fetch scoreboard {d}: {e}")

    # Aggregate opponent stats allowed per team
    # Structure: { team_abbr: { "pts": [], "reb": [], "ast": [] } }
    allowed = {}

    for event in all_events:
        try:
            comp = event["competitions"][0]
            competitors = comp["competitors"]
            if len(competitors) < 2:
                continue

            teams = []
            for c in competitors:
                abbr = c["team"].get("abbreviation") or c["team"].get("abbrev")
                score = float(c.get("score", 0) or 0)
                reb = 0
                ast = 0
                for s in c.get("statistics", []):
                    if s["name"] == "rebounds":
                        reb = float(s.get("displayValue", 0) or 0)
                    elif s["name"] == "assists":
                        ast = float(s.get("displayValue", 0) or 0)
                teams.append({"abbr": abbr, "pts": score, "reb": reb, "ast": ast})

            if len(teams) < 2:
                continue

            # Skip if score is 0 (game not played yet)
            if teams[0]["pts"] == 0 or teams[1]["pts"] == 0:
                continue

            # Each team "allowed" what their opponent scored
            for i, j in [(0, 1), (1, 0)]:
                abbr = teams[i]["abbr"]
                if not abbr or abbr == "NZL":  # skip invalid
                    continue
                if abbr not in allowed:
                    allowed[abbr] = {"pts": [], "reb": [], "ast": []}
                allowed[abbr]["pts"].append(teams[j]["pts"])
                allowed[abbr]["reb"].append(teams[j]["reb"])
                allowed[abbr]["ast"].append(teams[j]["ast"])

        except Exception:
            continue

    if not allowed:
        print("[WARN] No defensive data built")
        return

    # Compute averages and build cache
    rows = []
    for abbr, stats in allowed.items():
        if len(stats["pts"]) < 5:
            continue
        rows.append({
            "abbr":       abbr,
            "avg_pts":    round(sum(stats["pts"]) / len(stats["pts"]), 1),
            "avg_reb":    round(sum(stats["reb"]) / len(stats["reb"]), 1),
            "avg_ast":    round(sum(stats["ast"]) / len(stats["ast"]), 1),
            "games":      len(stats["pts"]),
        })

    df = pd.DataFrame(rows)

    # Rank — rank 1 = allows LEAST (toughest defense)
    df["pts_rank"] = df["avg_pts"].rank(ascending=True).astype(int)
    df["reb_rank"] = df["avg_reb"].rank(ascending=True).astype(int)
    df["ast_rank"] = df["avg_ast"].rank(ascending=True).astype(int)

    for _, row in df.iterrows():
        _DEFENSE_CACHE[row["abbr"]] = row.to_dict()

    print(f"[INFO] Defensive cache built for {len(_DEFENSE_CACHE)} teams")


def get_matchup_rating(rank: int) -> dict:
    if rank <= 10:
        return {"label": "Tough Defense", "emoji": "🔴"}
    elif rank <= 20:
        return {"label": "Average Defense", "emoji": "🟡"}
    else:
        return {"label": "Weak Defense", "emoji": "🟢"}


def get_opponent_stats(opponent_abbr: str, stat: str) -> dict:
    build_defense_cache()

    if not opponent_abbr:
        return {}

    abbr = opponent_abbr.strip().upper()
    team = _DEFENSE_CACHE.get(abbr)

    if not team:
        for key in _DEFENSE_CACHE:
            if abbr in key or key in abbr:
                team = _DEFENSE_CACHE[key]
                break

    if not team:
        print(f"[WARN] No defensive data for {abbr}")
        return {}

    stat_map = {
        "PTS":     ("avg_pts", "pts_rank", "PPG"),
        "REB":     ("avg_reb", "reb_rank", "RPG"),
        "AST":     ("avg_ast", "ast_rank", "APG"),
        "3PM":     ("avg_pts", "pts_rank", "PPG"),  # use pts as proxy
        "PRA":     ("avg_pts", "pts_rank", "PPG"),
        "PTS_AST": ("avg_pts", "pts_rank", "PPG"),
        "PTS_REB": ("avg_pts", "pts_rank", "PPG"),
        "REB_AST": ("avg_reb", "reb_rank", "RPG"),
    }

    stat_key, rank_key, label = stat_map.get(stat, ("avg_pts", "pts_rank", "PPG"))
    rank   = int(team[rank_key])
    rating = get_matchup_rating(rank)

    return {
        "team_name": abbr,
        "rank":      rank,
        "label":     rating["label"],
        "emoji":     rating["emoji"],
        "all_ranks": {
            "PTS": {"rank": int(team["pts_rank"]), "avg": team["avg_pts"], "label": "PPG"},
            "REB": {"rank": int(team["reb_rank"]), "avg": team["avg_reb"], "label": "RPG"},
            "AST": {"rank": int(team["ast_rank"]), "avg": team["avg_ast"], "label": "APG"},
        },
    }