import os
import requests
from dotenv import load_dotenv

load_dotenv()


ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"

TARGET_BOOKS = {
    "fanduel":        "FanDuel",
    "draftkings":     "DraftKings",
    "betmgm":         "BetMGM",
    "williamhill_us": "Caesars",
}

STAT_MARKET_MAP = {
    "PTS":     "player_points",
    "REB":     "player_rebounds",
    "AST":     "player_assists",
    "3PM":     "player_threes",
    "PRA":     "player_points_rebounds_assists",
    "PTS_AST": "player_points_assists",
    "PTS_REB": "player_points_rebounds",
    "REB_AST": "player_rebounds_assists",
}


def american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def calculate_ev(prediction: float, line: float, odds: int = -115) -> tuple:
    lean = "OVER" if prediction > line else "UNDER"
    implied_prob = american_to_implied(odds)
    diff = abs(prediction - line)
    raw_edge = diff * 3.5
    ev = raw_edge * (1 - implied_prob)
    return round(float(ev), 2), lean


def get_real_odds(player_name: str, stat: str, line: float, prediction: float) -> dict:
    market = STAT_MARKET_MAP.get(stat)
    if not market or not ODDS_API_KEY:
        return {}

    try:
        # Get upcoming NBA events
        events_resp = requests.get(
            f"{BASE_URL}/sports/basketball_nba/events",
            params={"apiKey": ODDS_API_KEY},
            timeout=10,
        )
        events = events_resp.json()
        if not events or isinstance(events, dict):
            print(f"[WARN] No NBA events found: {events}")
            return {}

        results = {}

        for event in events:
            event_id = event["id"]

            odds_resp = requests.get(
                f"{BASE_URL}/sports/basketball_nba/events/{event_id}/odds",
                params={
                    "apiKey":     ODDS_API_KEY,
                    "regions":    "us",
                    "markets":    market,
                    "oddsFormat": "american",
                    "bookmakers": ",".join(TARGET_BOOKS.keys()),
                },
                timeout=10,
            )
            odds_data = odds_resp.json()

            for bookmaker in odds_data.get("bookmakers", []):
                book_key   = bookmaker["key"]
                book_title = TARGET_BOOKS.get(book_key, bookmaker["title"])

                for mkt in bookmaker.get("markets", []):
                    if mkt["key"] != market:
                        continue
                    for outcome in mkt.get("outcomes", []):
                        desc = outcome.get("description", "")
                        if player_name.lower() not in desc.lower():
                            continue
                        if outcome["name"] != "Over":
                            continue

                        real_line = float(outcome.get("point", line))
                        real_odds = int(outcome.get("price", -115))
                        ev, lean  = calculate_ev(prediction, real_line, real_odds)

                        results[book_title] = {
                            "line": real_line,
                            "odds": real_odds,
                            "ev":   ev,
                            "lean": lean,
                        }

            if results:
                return results

        print(f"[INFO] '{player_name}' not found in upcoming odds — using mock")
        return {}

    except Exception as e:
        print(f"[ERROR] Odds API failed: {e}")
        return {}


def get_odds_ev(player: str, stat: str, line: float, prediction: float) -> tuple:
    # Try real odds first
    if ODDS_API_KEY:
        real = get_real_odds(player, stat, line, prediction)
        if real:
            best_ev   = max(v["ev"] for v in real.values())
            best_lean = max(real.values(), key=lambda x: x["ev"])["lean"]
            return round(best_ev, 2), real, best_lean

    # Fall back to mock if no API key or player not in upcoming games
    print("[INFO] Falling back to mock odds")
    mock_books = {
        "FanDuel":    {"line": line,        "odds": -112},
        "DraftKings": {"line": line + 0.5,  "odds": -115},
        "BetMGM":     {"line": line,        "odds": -115},
        "Caesars":    {"line": line - 0.5,  "odds": -110},
    }
    sportsbook_data = {}
    best_ev   = 0.0
    best_lean = "UNDER"
    for book, info in mock_books.items():
        ev, lean = calculate_ev(prediction, info["line"], info["odds"])
        sportsbook_data[book] = {"line": float(info["line"]), "ev": ev, "lean": lean}
        if ev > best_ev:
            best_ev   = ev
            best_lean = lean
    return best_ev, sportsbook_data, best_lean