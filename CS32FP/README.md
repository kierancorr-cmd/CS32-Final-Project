# Stock Explainer (CS32 Final Project)

This project is a web-based tool that monitors stock price movements and explains *why* they happen.

The system tracks stocks (both user-selected and broader market names), identifies unusually large price movements, and uses AI + news data to generate a concise explanation of what likely caused the move. The goal is to give investors a fast, intuitive way to understand market activity without digging through multiple sources.


## Overview

**PriceStory** is an interactive stock movement tracker:
* Search any public US ticker
* View historical price charts
* Identify major inflection points (spikes/drops)
* Click a point to get an AI-generated explanation of the move

## How It Works
1. The home page shows major stocks and recently viewed tickers
2. Users can search or select a stock
3. The app plots historical price data using Plotly
4. Significant moves are flagged based on volatility thresholds
5. Clicking a flagged point:

   * pulls news from the relevant date range
   * analyzes common themes across sources
   * generates a short explanation using an LLM

---

## Data Sources & Tools
* **Charts:** Plotly
* **Stock Data:** yfinance
* **News APIs (planned/optional):** NewsAPI, Finnhub, Polygon, Alpha Vantage
* **LLM:** OpenAI API (ChatGPT with web search)
* **Storage:** SQLite

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Set OpenAI API Key

The explanation system uses OpenAI’s API with web search.

```bash
export OPENAI_API_KEY="your_api_key_here"
```

**Windows:**

```bash
set OPENAI_API_KEY=your_api_key_here
```

---

### 3. Run the App

```bash
streamlit run app.py
```

Then open:
[http://localhost:8501](http://localhost:8501)

---

## File Structure

```
stock_explainer/
├── app.py              # Main Streamlit app (UI + routing)
├── stock_data.py       # Fetches stock price data (yfinance)
├── move_detector.py    # Identifies significant price movements
├── llm_explainer.py    # Calls OpenAI API to explain moves
├── database.py         # SQLite for storing recent tickers
├── requirements.txt
└── README.md
```

---

## Key Logic

* A "major move" is flagged when:

  * Daily % change > 2× (subject to change) recent rolling volatility
  * AND absolute move > 3%

This adapts to different stocks:

* High-volatility stocks (e.g., TSLA) require bigger moves
* Low-volatility stocks (e.g., JNJ) trigger on smaller moves

---

## Features

* Interactive price charts with clickable inflection points
* AI-generated explanations of stock movements
* Recently viewed ticker tracking (SQLite)
* Cached explanations to reduce API calls

---

## Notes

* Stock data is free via Yahoo Finance (no API key required)
* Explanations depend on available news — some moves may have weak or unclear causes
* Future improvements:

  * Better news aggregation
  * Multi-source verification scoring
  * Real-time alerts
  * Full market scanning

## External Resources and AI Assistance

I used several external resources while building this project.


### Generative AI Use

I used Claude as a coding assistant throughout the project, mostly for syntax help, debugging, and learning how to use unfamiliar libraries. In particular, I used Claude to help me:

- write and revise Python syntax for functions in `app.py`, `stock_mover.py`, `llm_explainer.py`, and `database.py`
- understand how to structure Streamlit components such as buttons, text inputs, charts, and page layout
- debug errors related to API calls, data formatting, SQLite queries, and function arguments
- generate starter versions of some functions, which I then edited, tested, and connected to the rest of the project
- explain unfamiliar tools such as `sqlite3`, Streamlit, API keys, and stock price data retrieval

Claude helped write portions of the code, especially boilerplate syntax and first drafts of functions. However, I made the main project design decisions myself, including the idea for the app, the overall file structure, the logic for identifying meaningful stock movements, the user interface goals, and how the different components should connect. I also reviewed, edited, and tested the code to make sure it worked for my specific project.

### YouTube Tutorials

I also used YouTube tutorials to learn the basics of Streamlit, Yahoo Finance stock data, and SQLite databases. These videos helped me understand the tools, but my final code was adapted to fit my own project.

- Streamlit tutorial: https://www.youtube.com/watch?v=D0D4Pa22iG0
- Yahoo Finance API tutorial: https://www.youtube.com/watch?v=uLM9MMT-ZKc
- SQLite Python tutorial: https://www.youtube.com/watch?v=girsuXz0yA8
