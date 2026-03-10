import requests
import pandas as pd
from defense import TEAM_ID_MAP

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
}

# Stats array indexes from ESPN labels:
# [MIN, FG, FG%, 3PT, 3P%, FT, FT%, REB, AST, BLK, STL, PF, TO, PTS]
#   0    1    2    3    4   5    6    7    8    9   10   11  12   13
IDX_MIN = 0
IDX_3PM = 3
IDX_REB = 7
IDX_AST = 8
IDX_PTS = 13



# Cache so we only build the player list once per session
_PLAYER_CACHE = {}


def build_player_cache():
    global _PLAYER_CACHE
    if _PLAYER_CACHE:
        return

    print("[INFO] Building player cache from ESPN rosters...")
    for team_id, abbr in TEAM_ID_MAP.items():
        try:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster",
                headers=HEADERS,
                timeout=10,
            )
            athletes = r.json().get("athletes", [])
            for player in athletes:
                name    = player.get("fullName", "").lower()
                pid     = player.get("id")
                display = player.get("displayName", player.get("fullName", ""))
                if name and pid:
                    _PLAYER_CACHE[name] = {
                        "id":          pid,
                        "displayName": display,
                        "team_id":     team_id,   # ← store team ID here
                        "team_abbr":   abbr,       # ← store team abbr here
                    }
        except Exception as e:
            print(f"[WARN] Could not fetch team {abbr}: {e}")

    print(f"[INFO] Player cache built: {len(_PLAYER_CACHE)} players")


def find_espn_player_id(player_name):
    build_player_cache()
    match = _PLAYER_CACHE.get(player_name.lower())
    if match:
        return match["id"], match["displayName"]
    # fuzzy fallback — check if query is contained in any name
    for name, data in _PLAYER_CACHE.items():
        if player_name.lower() in name:
            return data["id"], data["displayName"]
    return None, None


def get_player_data(player_name, season="2026"):
    player_id, found_name = find_espn_player_id(player_name)
    if not player_id:
        print(f"[WARN] Could not find ESPN ID for '{player_name}'")
        return pd.DataFrame()

    try:
        url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{player_id}/gamelog"
        r = requests.get(
            url,
            headers=HEADERS,
            params={"season": season},
            timeout=15,
        )
        data = r.json()
        events_dict = data.get("events", {})

        rows = []
        for season_type in data.get("seasonTypes", []):
            for category in season_type.get("categories", []):
                for event in category.get("events", []):
                    event_id = event.get("eventId")
                    stats = event.get("stats", [])
                    if not stats or len(stats) < 14:
                        continue

                    mins = stats[IDX_MIN]
                    if not mins or mins in ("0", "0:00", "--"):
                        continue

                    game_info = events_dict.get(event_id, {})
                    game_date = game_info.get("gameDate", "")
                    opponent  = game_info.get("opponent", {}).get("abbreviation", "?")
                    at_vs     = game_info.get("atVs", "vs")
                    team      = game_info.get("team", {}).get("abbreviation", "?")
                    result    = game_info.get("gameResult", "")
                    score     = game_info.get("score", "")
                    matchup   = f"{team} {at_vs} {opponent} ({result} {score})"

                    raw_3pt = stats[IDX_3PM]
                    fg3m = int(str(raw_3pt).split("-")[0]) if "-" in str(raw_3pt) else 0

                    rows.append({
                        "GAME_DATE": pd.to_datetime(game_date, utc=True).tz_convert("US/Eastern").tz_localize(None),
                        "MATCHUP":   matchup,
                        "PTS":  int(stats[IDX_PTS]),
                        "REB":  int(stats[IDX_REB]),
                        "AST":  int(stats[IDX_AST]),
                        "FG3M": fg3m,
                        "MIN":  mins,
                    })

        if not rows:
            print(f"[WARN] No stats found for {player_name}.")
            return pd.DataFrame()

        df = pd.DataFrame(rows).sort_values("GAME_DATE").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch gamelog for {player_name}: {e}")
        return pd.DataFrame()


def get_player_suggestions(query):
    build_player_cache()
    query = query.lower()
    matches = [
        data["displayName"]
        for name, data in _PLAYER_CACHE.items()
        if query in name
    ]
    return matches[:10]

def get_next_opponent(player_name):
    build_player_cache()
    player = _PLAYER_CACHE.get(player_name.lower())
    if not player:
        return None

    team_id   = player["team_id"]
    team_abbr = player["team_abbr"]

    try:
        r = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule",
            headers=HEADERS,
            timeout=10,
        )
        events = r.json().get("events", [])

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        for event in events:
            game_date_str = event.get("date", "")
            if not game_date_str:
                continue
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except Exception:
                continue

            if game_date < now:
                continue

            for comp in event.get("competitions", []):
                for competitor in comp.get("competitors", []):
                    abbr = competitor.get("team", {}).get("abbreviation", "")
                    if abbr and abbr != team_abbr:
                        print(f"[INFO] Next opponent for {player_name}: {abbr}")
                        return abbr

        return None

    except Exception as e:
        print(f"[ERROR] Could not get next opponent: {e}")
        return None