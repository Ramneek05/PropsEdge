from flask import Flask, jsonify, render_template, request
from data import get_player_data, get_player_suggestions, get_next_opponent
from feature_eng import prepare_features
from model import train_model
from visualization import make_chart
from odds import calculate_ev, get_odds_ev
from defense import get_opponent_stats
import numpy as np

app = Flask(__name__)



def compute_hit_rate(df, stat, line):
    last10 = df.tail(10)
    values = last10[stat].tolist()
    hits = sum(1 for v in values if v >= line)
    hit_rate = round((hits / len(values)) * 100) if values else 0
    avg = round(np.mean(values), 1) if values else 0
    return hit_rate, hits, avg


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    chart = None
    error = None

    if request.method == "POST":
        player_name = request.form["player_name"].strip()
        stat = request.form["stat"]
        line = float(request.form["line"])

        df = get_player_data(player_name)

        if df.empty:
            error = f"Could not find data for '{player_name}'. Check the spelling or try again."
        else:
            df = prepare_features(df)

            if df.empty:
                error = "Not enough game data to run the model."
            else:
                model, score, latest = train_model(df, stat)

                if model is None:
                    error = "Not enough games to train the model (need at least 5)."
                else:
                    prediction = round(float(model.predict(latest)[0]), 1)
                    best_ev, odds_dict, overall_lean = get_odds_ev(player_name, stat, line, prediction)
                    overall_lean = "OVER" if prediction > line else "UNDER"
                    hit_rate, hits, avg_last10 = compute_hit_rate(df, stat, line)
                    chart = make_chart(df, stat, line, prediction)
                    opponent_abbr = get_next_opponent(player_name)
                    defense = get_opponent_stats(opponent_abbr, stat) if opponent_abbr else {}

                    result = {
                        "player": player_name,
                        "stat": stat,
                        "line": line,
                        "prediction": prediction,
                        "score": round(score, 2),
                        "ev": round(best_ev, 1),
                        "lean": overall_lean,
                        "odds": odds_dict,
                        "hit_rate": hit_rate,
                        "hits": hits,
                        "avg_last10": avg_last10,
                        "defense": defense,
                    }

    return render_template("index.html", result=result, chart=chart, error=error)


@app.route("/suggest", methods=["GET"])
def suggest():
    query = request.args.get("q", "").lower()
    return jsonify(get_player_suggestions(query))


if __name__ == "__main__":
    app.run(debug=True)