⚡ PropsEdge — NBA Player Props Edge Finder

Live Demo: propsedge.onrender.com  |  Built by: Ramneek Singh Chohan

A full-stack data science web application that predicts NBA player prop outcomes using machine learning, analyzes defensive matchups, and compares real-time sportsbook lines to find edges.

⚠️ For educational and portfolio purposes only. Not financial or betting advice.

🖼️ Preview
(<Screenshot 2026-03-10 at 3.57.27 PM.png>)
A dark-mode dashboard inspired by PrizePicks, featuring:
ML-powered OVER/UNDER prediction vs. your submitted prop line
Last-10 game hit rate with animated progress bar
Color-coded interactive bar chart (green = hit, red = miss)
Opponent defensive rankings (PPG / RPG / APG allowed) for the next game
Real-time sportsbook line comparison with EV% across FanDuel, DraftKings, BetMGM & Caesars


🏗️ Tech Stack
LayerTechnologyBackendPython 3, FlaskML Modelscikit-learn — Ridge RegressionData SourceESPN Stats API (no key required)VisualizationPlotly — interactive, dark-themed chartsFrontendJinja2, Bootstrap 5, Vanilla JSDeploymentRender (live web app)

🚀 Features
🤖 Machine Learning

Ridge regression model trained on rolling 5-game averages and minutes trends
Predicts next-game output for PTS, REB, AST, PRA, 3PM and combo stats
Displays model R² score so you can gauge confidence

📊 Performance Analysis

Last-10 game hit rate calculated against your submitted line
Interactive Plotly bar chart — color-coded green/red with game-by-game hover details
Subtle prop line overlay for visual reference

🛡️ Defensive Matchup Intelligence

Automatically detects each player's next opponent from the live ESPN schedule
Ranks all 30 NBA teams by PPG, RPG, and APG allowed this season
Color-coded: 🔴 Tough (Top 10) · 🟡 Average (11–20) · 🟢 Weak (21–30)
Defensive stats rebuild dynamically every season — no manual updates needed

💰 Sportsbook Line Comparison

Live odds from FanDuel, DraftKings, BetMGM, and Caesars via The Odds API
EV% calculated per book based on ML prediction vs. real lines
Falls back to mock lines gracefully when player isn't in upcoming games

⚡ UX Polish

Player autocomplete — search any of 500+ active NBA players instantly
Loading overlay with spinner while model runs
Fully responsive dark-mode design


⚙️ Local Setup
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/nba-props-edge.git
cd nba-props-edge

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add environment variables
echo "ODDS_API_KEY=your_key_here" > .env

# 5. Run the app
python3 main.py

# 6. Open in browser
# http://127.0.0.1:5000

> 💻 Prefer to run locally? Follow the steps above. The app works fully offline with mock sportsbook lines.
> 🌐 Or just visit the live site at [propsedge.onrender.com](https://propsedge.onrender.com) — no setup needed.


📁 Project Structure
nba-props-edge/
├── main.py            # Flask app, routes, request orchestration
├── data.py            # ESPN API — player gamelogs, roster cache, schedule
├── feature_eng.py     # Rolling averages & feature engineering
├── model.py           # Ridge regression model training & inference
├── defense.py         # Real defensive rankings from ESPN scoreboard data
├── visualization.py   # Plotly chart generation
├── odds.py            # EV calculation & live sportsbook line comparison
├── templates/
│   └── index.html     # Full frontend dashboard
├── requirements.txt
├── .env               # API keys (not committed)
└── .gitignore

🔭 How It Works
1. Data Pipeline
Player gamelogs are fetched from the ESPN Stats API — no API key required, no rate limiting. A player cache of 500+ active NBA players is built on startup from all 30 team rosters.
2. Feature Engineering
For each player and stat, the pipeline computes:

5-game rolling average for the target stat
5-game rolling average for minutes played
Combo stats (PRA, PTS+AST, PTS+REB, REB+AST)

3. ML Prediction
Ridge regression is trained on the rolling features and predicts the player's next-game output. The model R² score is displayed so users can see prediction confidence.
4. Defensive Context
The app fetches the player's next game from the ESPN schedule, then looks up the opponent's defensive rankings — calculated from real game-by-game scoreboard data across the full current season.
5. EV Calculation
The distance between the ML prediction and the sportsbook line is used to estimate edge, adjusted for the vig (implied probability from American odds).

🌐 Deployment
Deployed on Render as a live web service.
Start command: gunicorn main:app
Environment variable: ODDS_API_KEY=your_key

🛣️ Roadmap

 Home/away splits in the ML model
 Injury status and rest days as features
 Position-based defensive ratings (guards vs. centers)
 Multi-player comparison view
 Parlay builder with combined hit probability
 Historical backtesting against past lines


👤 About
Ramneek Singh Chohan
Built as a data science and software engineering portfolio project demonstrating:

REST API integration and data pipeline engineering
Machine learning model training and deployment
Full-stack web development (Python/Flask + JS/HTML/CSS)
Interactive data visualization
Sports analytics and statistical reasoning

GitHub: Ramneek05 · LinkedIn: https://www.linkedin.com/in/ramneekchohan/