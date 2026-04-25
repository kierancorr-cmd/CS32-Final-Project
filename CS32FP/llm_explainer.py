from openai import OpenAI
import os
from datetime import datetime, timedelta

# uses OpenAI / ChatGPT API with web search
# you need OPENAI_API_KEY set in your environment

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def explain_move(ticker, date_str, pct_change):
    """
    Given a ticker, date, and % change, search the web for news from that period
    and ask ChatGPT to explain what probably caused the move.
    """

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        date = datetime.strptime(date_str[:10], "%Y-%m-%d")

    date_before = (date - timedelta(days=2)).strftime("%B %d, %Y")
    date_after = (date + timedelta(days=1)).strftime("%B %d, %Y")
    date_pretty = date.strftime("%B %d, %Y")

    direction = "rose" if pct_change > 0 else "fell"
    sign = "+" if pct_change > 0 else ""

    prompt = f"""I need you to explain why {ticker} stock {direction} {sign}{pct_change:.1f}% on {date_pretty}.

Please search the web for news about {ticker} from around {date_before} to {date_after}. Look for:
- Earnings reports or guidance
- Major product announcements
- Analyst upgrades/downgrades
- Macroeconomic news affecting the stock
- Industry news
- Any relevant company announcements

After searching, write a SHORT explanation, 3-5 sentences max, of what most likely caused this move.
Be specific about what you found. If the news evidence is weak or unclear, say so.
Don't pad the response. Just explain the move clearly and concisely.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1",
            tools=[
                {"type": "web_search_preview"}
            ],
            input=prompt,
            max_output_tokens=500
        )

        explanation = response.output_text

        if not explanation.strip():
            explanation = "Couldn't find a clear explanation for this move. Try checking financial news sites for this date."

        return explanation.strip()

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Error generating explanation: {str(e)}\n\nMake sure your OPENAI_API_KEY is set correctly."
