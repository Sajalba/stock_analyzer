📈 Stock Analyst Pro 
An AI-powered Equity Research Agent built with LangGraph, Groq (Llama 3.3 70B), and LangChain. This tool autonomously fetches real-time market data, technical indicators, and news to generate structured investment reports.

🚀 Overview
Stock Analyst Pro utilizes a ReAct (Reasoning and Acting) architecture. When a user asks about a stock, the agent:

1.  Identifies the correct ticker symbol (supporting US and Indian markets).
2.  Executes parallel tools to gather price, news, and technical data.
3.  Synthesizes the information into a professional-grade research report.

🛠️ Tech Stack
*  Orchestration: LangGraph (Stateful multi-actor applications)
*  LLM: Llama-3.3-70b via Groq
*  Data Sources: Yahoo Finance (yfinance), Google Finance (Scraping), NewsAPI, and Finnhub.
*  Memory: LangGraph MemorySaver for persistent thread-based conversations.

✨ Features
* Multi-Market Support: Handles US stocks (e.g., AAPL, TSLA) and Indian stocks (e.g., RELIANCE.NS).
* Technical Analysis: Automated calculation of RSI, SMA20, and SMA50 to determine market trends.
* News Aggregation: Fetches the latest headlines to factor sentiment into recommendations.
* Peer Benchmarking: Contextualizes performance against sector averages.
* Memory: Remembers previous context within a session for follow-up analysis.

📋 Prerequisites
Before running the project, ensure you have the following API keys:
1. Groq API Key: For the Llama 3.3 model.
2. NewsAPI Key: For Indian market news.
3. Finnhub API Key: For US market news.

⚙️ Installation
Clone the repository:
git clone https://github.com/your-username/stock-analyst-pro.git
cd stock-analyst-pro

Install dependencies:
pip install langgraph langchain_groq yfinance pandas requests beautifulsoup4 python-dotenv

Configure Environment Variables: 
Create a .env file in the root directory:
1. GROQ_API_KEY=your_groq_key
2. NEWS_API_KEY=your_newsapi_key
3. FINNHUB_API_KEY=your_finnhub_key

🕹️ Usage
Run the main script to start the interactive CLI:
python main.py

Example Commands:
"Analyze Tesla""Should I buy HDFCBANK.NS?""Compare Microsoft with its peers"

🏗️ Graph Architecture
The agent operates on a cyclic graph:
Start -> Chatbot: LLM decides if tools are needed.
Chatbot -> Tools: Fetches data (Price, Tech, News).
Tools -> Chatbot: LLM receives data and formats the report.
Chatbot -> End: Delivers final response to user.

⚠️ DisclaimerThis tool is for educational purposes only. It is not financial advice. Always consult with a certified financial advisor before making investment decisions.
