import plotly.graph_objects as go


def make_chart(df, stat, line, prediction):
    df = df.copy().sort_values("GAME_DATE")
    df["GAME_DATE"] = df["GAME_DATE"].dt.strftime("%b %d")

    game_labels = [
        f"{row['GAME_DATE']} — {row['MATCHUP']}" for _, row in df.iterrows()
    ]
    x_idx = list(range(len(df)))

    colors = ["#00d68f" if v >= line else "#ff4d6d" for v in df[stat]]

    hover_text = [
        f"<b>{row['MATCHUP']}</b><br>"
        f"📅 {row['GAME_DATE']}<br>"
        f"📊 {stat}: <b>{row[stat]}</b><br>"
        f"📏 Line: {line}<br>"
        f"⏱ Minutes: {row['MIN']}<br>"
        f"{'✅ HIT' if row[stat] >= line else '❌ MISS'}"
        for _, row in df.iterrows()
    ]

    total_games = len(df)
    visible_start = max(0, total_games - 10)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_idx,
        y=df[stat].tolist(),
        marker_color=colors,
        marker_opacity=0.88,
        marker_line_width=0,
        text=[f"<b>{v}</b>" for v in df[stat]],
        textposition="outside",
        textfont=dict(color="white", size=11, family="Inter"),
        hovertext=hover_text,
        hoverinfo="text",
        name=stat,
        showlegend=False,
    ))

    fig.add_hline(
        y=line,
        line_dash="dot",
        line_color="rgba(255,255,255,0.4)",
        line_width=1.5,
        annotation_text=f"Line {line}",
        annotation_position="top left",
        annotation_font_color="rgba(255,255,255,0.35)",
        annotation_font_size=11,
    )


    fig.update_layout(
        template="plotly_dark",
        height=420,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=44, b=70),
        xaxis=dict(
            tickmode="array",
            tickvals=x_idx,
            ticktext=game_labels,
            tickangle=-38,
            tickfont=dict(size=9.5, color="#94a3b8"),
            showgrid=False,
            range=[visible_start - 0.5, total_games - 0.5],
            rangeslider=dict(
                visible=True,
                thickness=0.06,
                bgcolor="#1e2a3a",
                bordercolor="#334155",
                borderwidth=1,
            ),
            fixedrange=False,
        ),
        yaxis=dict(
            title=stat,
            tickfont=dict(size=11, color="#94a3b8"),
            gridcolor="rgba(255,255,255,0.06)",
            fixedrange=True,
        ),
        hoverlabel=dict(
            bgcolor="#1e2a3a",
            bordercolor="rgba(255,255,255,0.12)",
            font=dict(color="white", size=13, family="Inter"),
        ),
        bargap=0.22,
        dragmode="pan",
    )

    return fig.to_html(
        full_html=False,
        config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "zoom2d", "select2d", "lasso2d", "zoomIn2d",
                "zoomOut2d", "autoScale2d", "toImage"
            ],
            "displaylogo": False,
            "scrollZoom": False,
        }
    )