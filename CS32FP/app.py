import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from stock_data import get_stock_history, get_stock_info
from move_detector import find_major_moves
from llm_explainer import explain_move
from database import save_recently_viewed, get_recently_viewed, init_db
-
# webpage configuration
from PIL import Image
icon = Image.open("assets/pricestory_icon_128_transparent.png")
st.set_page_config(
    page_title="PriceStory",
    layout="wide",
    page_icon="icon",
    initial_sidebar_state="collapsed"
)

# some basic CSS to clean up the UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');
    * { font-family: 'IBM Plex Sans', sans-serif !important; }

    .block-container { padding-top: 2rem; }
    div[data-testid="stButton"] button {
        border-radius: 8px;
    }
    .stock-tile {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        margin: 4px;
    }
    .big-metric {
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# init db once on startup
init_db()


# session state defaults
if "page" not in st.session_state:
    st.session_state.page = "home"
if "ticker" not in st.session_state:
    st.session_state.ticker = None
if "selected_move" not in st.session_state:
    st.session_state.selected_move = None
if "time_range" not in st.session_state:
    st.session_state.time_range = "2y"

# Major stocks to show on the main page
MAIN_STOCKS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL", "SPY", "AMD", "NFLX", "JPM", "DIS"]


# helper that navigates to a stock page
def go_to_stock(ticker):
    t = ticker.upper().strip()
    st.session_state.ticker = t
    st.session_state.page = "stock"
    st.session_state.selected_move = None
    save_recently_viewed(t)
    st.rerun()


# TIME RANGE helper - maps label to days back
TIME_RANGES = {
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "2Y": 730,
    "5Y": 1825,
}


# Home Page
def render_home():
    from PIL import Image
    icon = Image.open("assets/pricestory_icon_128_transparent.png")
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image(icon, width=60)
    with col_title:
        st.title("PriceStory")
    st.caption("Search any ticker, click major moves on the chart, get AI-powered explanations")

    st.markdown("---")

    # search bar, semi centered using columns
    _, col_search, _ = st.columns([1, 2, 1])
    with col_search:
        search = st.text_input(
            "search",
            placeholder="🔍  Search a ticker (e.g. NVDA, AAPL, BTC-USD)",
            label_visibility="collapsed",
            key="search_input"
        )
        if search:
            ticker = search.upper().strip()
            if st.button(f"Open {ticker} →", use_container_width=True, type="primary"):
                go_to_stock(ticker)

    st.markdown("---")

    # recently viewed: show above main stocks if there's anything
    recent = get_recently_viewed()
    if recent:
        st.subheader("Recently Viewed")
        cols = st.columns(min(len(recent), 8))
        for i, t in enumerate(recent):
            with cols[i % 8]:
                if st.button(t, key=f"recent_{t}", use_container_width=True):
                    go_to_stock(t)
        st.markdown("---")

    # main stocks grid
    st.subheader("Major Stocks")
    st.caption("Click any card to view the full chart")

    # load all stock info - do it in one shot so the page doesn't flicker
    cols = st.columns(4)
    for i, ticker in enumerate(MAIN_STOCKS):
        with cols[i % 4]:
            with st.spinner(""):
                info = get_stock_info(ticker)

            price = info.get("price", 0)
            change = info.get("change", 0)
            name = info.get("name", ticker)
            color = "🟩" if change >= 0 else "🟥"
            sign = "+" if change >= 0 else ""

            # use a button styled to look like a card
            btn_label = f"**{ticker}**  {color}\n\n${price:,.2f}    {sign}{change:.2f}%\n\n{name[:25]}"
            if st.button(btn_label, key=f"main_{ticker}", use_container_width=True):
                go_to_stock(ticker)



# Individual Stock Info Page
def render_stock_page():
    ticker = st.session_state.ticker

    # back button + title on same row
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back"):
            st.session_state.page = "home"
            st.session_state.selected_move = None
            st.rerun()

    # grab stock info for the header
    info = get_stock_info(ticker)
    price = info.get("price", 0)
    change = info.get("change", 0)
    name = info.get("name", ticker)
    color = "green" if change >= 0 else "red"
    sign = "+" if change >= 0 else ""

    with col_title:
        st.title(f"{ticker}  —  {name}")
        st.markdown(f"**${price:,.2f}**  &nbsp;&nbsp; :{color}[{sign}{change:.2f}% today]")

    st.markdown("---")

    # time range selector
    range_cols = st.columns(len(TIME_RANGES) + 3)
    with range_cols[0]:
        st.caption("Time range:")
    for i, (label, _) in enumerate(TIME_RANGES.items()):
        with range_cols[i + 1]:
            if st.button(label, key=f"range_{label}", type="primary" if st.session_state.time_range == label else "secondary"):
                st.session_state.time_range = label
                st.session_state.selected_move = None  # clear explanation when range changes
                st.rerun()

    # load data for selected range
    days_back = TIME_RANGES[st.session_state.time_range]
    end = datetime.today()
    start = end - timedelta(days=days_back)

    with st.spinner(f"Loading {ticker} price history..."):
        data = get_stock_history(ticker, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    if data is None or data.empty:
        st.error(f"⚠️  Couldn't load data for **{ticker}**. Double-check the ticker symbol.")
        return

    # find the inflection points
    moves = find_major_moves(data)


    # Build the chart
    fig = go.Figure()

    # main candlestick or line - using line for cleaner look
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        name=ticker,
        line=dict(color="#1E88E5", width=2),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Close: $%{y:,.2f}<extra></extra>"
    ))

    # shade under the line lightly
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["Close"],
        fill="tozeroy",
        mode="none",
        fillcolor="rgba(30,136,229,0.08)",
        showlegend=False,
        hoverinfo="skip"
    ))

    # inflection point markers
    if not moves.empty:
        ups = moves[moves["return"] > 0]
        downs = moves[moves["return"] < 0]

        if not ups.empty:
            fig.add_trace(go.Scatter(
                x=ups.index,
                y=ups["Close"],
                mode="markers",
                name="Big Up Day",
                marker=dict(
                    color="#00C853",
                    size=12,
                    symbol="triangle-up",
                    line=dict(color="white", width=1)
                ),
                customdata=ups["return"].round(2),
                hovertemplate=(
                    "<b>%{x|%b %d, %Y}</b><br>"
                    "Price: $%{y:,.2f}<br>"
                    "<b style='color:#00C853'>▲ +%{customdata}%</b><br>"
                    "<i>Click to see what caused this</i>"
                    "<extra></extra>"
                )
            ))

        if not downs.empty:
            fig.add_trace(go.Scatter(
                x=downs.index,
                y=downs["Close"],
                mode="markers",
                name="Big Down Day",
                marker=dict(
                    color="#F44336",
                    size=12,
                    symbol="triangle-down",
                    line=dict(color="white", width=1)
                ),
                customdata=downs["return"].round(2),
                hovertemplate=(
                    "<b>%{x|%b %d, %Y}</b><br>"
                    "Price: $%{y:,.2f}<br>"
                    "<b style='color:#F44336'>▼ %{customdata}%</b><br>"
                    "<i>Click to see what caused this</i>"
                    "<extra></extra>"
                )
            ))

    fig.update_layout(
        height=480,
        showlegend=True,
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            showgrid=False,
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f0f0f0",
            tickprefix="$",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=30, b=10, l=10, r=10)
    )

    # render chart - the on_select="rerun" makes it so clicking a point triggers a rerun
    st.caption("⬆️ **Hover** to inspect prices. **Click a triangle** to get an AI explanation of the move.")
    selected = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode=["points"],
        use_container_width=True,
        key="stock_chart"
    )

    # handle click on inflection points
    # curve 0 is the main line, curve 1 is fill, curve 2 = ups, curve 3 = downs
    # (only 2 and 3 matter)
    if selected and selected.selection and selected.selection.points:
        point = selected.selection.points[0]
        curve_idx = point.get("curve_number", 0)

        if curve_idx in [2, 3]:  # 0 = line, 1 = fill, 2 = ups, 3 = downs
            raw_date = point.get("x", "")
            price_clicked = point.get("y", 0)
            pct = point.get("customdata", 0)

            # x might come back as a full ISO string
            date_only = str(raw_date)[:10]

            # only update if it's a different move than what's already showing
            if (
                st.session_state.selected_move is None
                or st.session_state.selected_move.get("date") != date_only
            ):
                st.session_state.selected_move = {
                    "date": date_only,
                    "price": price_clicked,
                    "pct": pct
                }

    # Explanation panel
    if st.session_state.selected_move:
        move = st.session_state.selected_move
        date = move["date"]
        pct = move["pct"]
        price_at = move["price"]

        st.markdown("---")

        # header for the explanation panel
        col_metric, col_exp = st.columns([1, 4])
        with col_metric:
            sign = "+" if pct > 0 else ""
            emoji = "📈" if pct > 0 else "📉"
            st.metric(
                label=f"{emoji} {date}",
                value=f"${price_at:,.2f}",
                delta=f"{sign}{pct:.2f}%"
            )
            if st.button("✕ Dismiss", key="dismiss"):
                st.session_state.selected_move = None
                st.rerun()

        with col_exp:
            st.markdown("#### What caused this move?")

            # check cache first - don't re-query if we already explained this one
            cache_key = f"explanation_{ticker}_{date}"
            if cache_key not in st.session_state:
                with st.spinner("🔍 Searching news and generating explanation..."):
                    explanation = explain_move(ticker, date, pct)
                st.session_state[cache_key] = explanation
            else:
                explanation = st.session_state[cache_key]

            st.markdown(explanation)

    # show a summary of how many major moves were found
    if not moves.empty:

        st.caption(f"Found **{len(moves)} major moves** ... (5-day moves > 3x normal volatility and > 4%)")
    else:
        st.caption("No major moves found in this period. Try expanding the time range.")


# Routing: which page to render

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "stock":
    render_stock_page()
