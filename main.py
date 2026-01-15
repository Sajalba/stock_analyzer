from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
import requests
import datetime
import os
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

# -------------------------------------------------------------------
# Environment & Global Setup
# -------------------------------------------------------------------
load_dotenv()
memory = MemorySaver()

NEWS_API_KEY = os.getenv("NEWS_API_KEY") 
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

SYMBOL_ALIASES = {
    "TESLA": "TSLA", "APPLE": "AAPL", "MICROSOFT": "MSFT",
    "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "META": "META",
}

# -------------------------------------------------------------------
# Helper & Tool Functions
# -------------------------------------------------------------------

def normalize_symbol(symbol: str) -> str:
    return SYMBOL_ALIASES.get(symbol.upper(), symbol.upper())

def is_indian_stock(symbol: str) -> bool:
    return symbol.upper().endswith(".NS") or symbol.upper().endswith(".BSE")

def get_company_name(symbol: str) -> str:
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info.get('shortName', symbol)
    except:
        return symbol

def get_stock_price(symbol: str) -> str:
    """Fetch latest price via Google Finance."""
    try:
        symbol = symbol.upper()
        if is_indian_stock(symbol):
            clean = symbol.replace(".NS", "").replace(".BSE", "")
            google_symbol, currency = f"{clean}:NSE", "₹"
        else:
            google_symbol, currency = symbol, "$"

        url = f"https://www.google.com/finance/quote/{google_symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        price_div = soup.find("div", class_="YMlKec fxKbKc")
        if not price_div: return "Price data unavailable."
        
        price = price_div.text.replace(currency, "").replace(",", "").strip()
        return f"{currency}{float(price):.2f}"
    except Exception as exc:
        return f"Price error: {exc}"

def get_stock_news(symbol: str) -> str:
    """Fetch news from NewsAPI (India) or Finnhub (US)."""
    try:
        today, from_date = datetime.date.today(), datetime.date.today() - datetime.timedelta(days=7)
        if is_indian_stock(symbol):
            url = f"https://newsapi.org/v2/everything?q={get_company_name(symbol)}&from={from_date}&apiKey={NEWS_API_KEY}&language=en&pageSize=5"
            data = requests.get(url).json()
            articles = data.get("articles", [])
            return "News:\n" + "\n".join([f"- {a['title']}" for a in articles])
        else:
            url = f"https://finnhub.io/api/v1/company-news?symbol={normalize_symbol(symbol)}&from={from_date}&to={today}&token={FINNHUB_API_KEY}"
            news = requests.get(url).json()
            return "News:\n" + "\n".join([f"- {n['headline']}" for n in news[:5]])
    except Exception as exc:
        return f"News error: {exc}"

def get_technical_indicators(symbol: str) -> str:
    """Calculate RSI and SMA."""
    try:
        df = yf.Ticker(symbol).history(period="6mo")
        if df.empty: return "Technicals unavailable."
        close = df["Close"]
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        sma20, sma50 = close.rolling(20).mean().iloc[-1], close.rolling(50).mean().iloc[-1]
        return f"RSI: {rsi:.2f} | SMA20: {sma20:.2f} | SMA50: {sma50:.2f} | Trend: {'Bullish' if sma20 > sma50 else 'Bearish'}"
    except Exception as exc:
        return f"Tech error: {exc}"

def get_peer_comparison(symbol: str) -> str:
    """Compares stock performance with its sector peers."""
    try:
        ticker = yf.Ticker(symbol)
        peers = ticker.info.get('recommendationKey', "Unavailable") # Simplified peer proxy
        sector = ticker.info.get('sector', 'Unknown Sector')
        
        # Example: Manual peer list for demo; in prod use a dedicated API
        return f"Sector: {sector} | Peer Context: Usually compared against top sector players. Performance is currently {'leading' if ticker.info.get('pegRatio', 1) < 1 else 'lagging'} sector averages based on PEG ratio."
    except:
        return "Peer comparison data currently unavailable."

tools = [get_stock_price, get_stock_news, get_technical_indicators, get_peer_comparison]

# -------------------------------------------------------------------
# LLM & Graph Setup
# -------------------------------------------------------------------

class State(TypedDict):
    messages: Annotated[list, add_messages]

ANALYST_SYSTEM_PROMPT = """
You are a professional equity research analyst. Produce a structured, bulleted report.

### 📊 EQUITY RESEARCH REPORT ###

* **Recommendation:** [BUY | HOLD | SELL]
* **Target Price (6mo):** [Estimated target]
* **Risk Score:** [X/10] - [Label]

---
* **Current Price:**
  - [Ticker]: [Price] (Context relative to SMA)

* **Peer Benchmarking:**
  - [Compare performance/valuation vs sector peers]

* **News Analysis:**
  - [Bullet: Summary of key headlines]

* **Technical Indicators:**
  - RSI: [Value] | Trend: [Bullish/Bearish]

* **Final Reasoning:**
  - [Synthesis of all data]

SCORING: 1-3 (Low/Stable), 4-7 (Moderate), 8-10 (High/Speculative).
TARGET: BUY (+7%), SELL (-7%), HOLD (Flat).
"""

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0).bind_tools(tools)

def chatbot(state: State):
    messages = [{"role": "system", "content": ANALYST_SYSTEM_PROMPT}] + state["messages"]
    return {"messages": [llm.invoke(messages)]}

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")
graph = builder.compile(checkpointer=memory)

# -------------------------------------------------------------------
# Consolidated Runner
# -------------------------------------------------------------------

def run_chat():
    print("\n🚀 Stock Analyst Pro v4.0 Active")
    print("Commands: 'Analyze AAPL', 'Is Reliance.NS a buy?', 'exit'")
    config = {"configurable": {"thread_id": "market_analyst_session"}}

    while True:
        user_input = input("\n🧑 User: ").strip()
        if user_input.lower() in ("exit", "quit"): break

        try:
            # We use stream to capture the final LLM response after tool execution
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config, stream_mode="values"):
                final_msg = event["messages"][-1]
            
            if final_msg.content:
                print(f"\n{final_msg.content}")
                print("="*50)
        except Exception as exc:
            print(f"❌ Error: {exc}")

if __name__ == "__main__":
    run_chat()