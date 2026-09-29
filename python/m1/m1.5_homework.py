# python/m1/m1.5_homework.py
"""M1.5 Homework: Build Your Own Custom Tool.

THE IDEA
The lab wired up one custom tool (read_sql) for one fixed topic (the
Chinook music database). This homework asks you to do the same thing for
a topic YOU pick: something you actually know or care about (a game, a
sport, a show, your favorite band's discography, local trivia, whatever).
There's no single correct topic or persona here, that's the point. Two
students doing this homework could end up with two completely different
tools and agents.

WHAT YOU FILL IN
  TODO 1: write your own custom tool with the @tool decorator. Pick any
    topic, store a small lookup (a dict is fine, no API needed) of facts
    about it, and return one back based on the argument the model passes.
  TODO 2: write a system prompt that gives the agent a persona of your
    choosing and tells it to use your tool before answering.

RUN
  cd python
  uv run ./m1/m1.5_homework.py
"""

#%% initialize
import warnings
import os
warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.tools import tool

from deepagents import create_deep_agent
from models import model
from  dotenv import load_dotenv
import requests


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Define your own custom tool.
#
# Requirements:
#   - Keep the @tool decorator.
#   - Give it a real docstring: one sentence the model will read to decide
#     when to call this tool.
#   - Have it take at least one argument and return a string.
#   - The lookup data can just live in this file (a dict, a list, whatever
#     fits your topic). No external API or key needed.
#
# Example shape (delete this and write your own):
#   @tool
#   def lookup_something(query: str) -> str:
#       """One sentence describing what this returns and when to call it."""
#       ...
# ════════════════════════════════════════════════════════════════════════

class MktData:
    """A simple class to fetch market data from a public API."""

    def __init__(self):
        load_dotenv(override=True)
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        internval = "5min"
        self.api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={{}}&interval={internval}&apikey={api_key}"

    def get_price(self, symbol: str, currency: str = "usd") -> dict:
        """Fetch the current price of a cryptocurrency."""
        try:
            _url = self.api_url.format(symbol)
            response = requests.get(_url)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as e:
            return f"Error fetching price data: {e}"

mktdata = MktData()

@tool
def markdata_tool(query: str) -> dict:
    """Provides financial advice based on the user's query."""
    mkt_data:dict = mktdata.get_price(query)
    return f"this is your financial advice on: {mkt_data}"

#%% Execute the agent with a test prompt
# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a system prompt for your agent.
#
# Give it a persona (a name, a voice, a personality, anything you want)
# and tell it to call your_custom_tool (rename it if you like) before
# answering, the same way the lab's SYSTEM_PROMPT pointed the agent at
# read_sql.
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a financial advisor. You specialize in financial data analysis and provide insights based on market trends. You have access to a tool called markdata_tool that fetches real-time market data for various financial instruments. Before answering any user query related to financial advice, you must call markdata_tool to retrieve the latest data and base your response on that information. Always provide clear, concise, and actionable advice, and ensure that your recommendations are backed by the most recent market data available."""

# Guards against running with an unfilled placeholder; the filled
# reference doesn't need this since there's no placeholder text left.
if "TODO 1" in markdata_tool.description:
    raise NotImplementedError("TODO 1: see the comment block above")
if "TODO 2" in SYSTEM_PROMPT:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    name="Finance_agent",
    tools=[markdata_tool],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Ask your agent a question that needs your tool."}]}
)

print(result["messages"][-1].content)

# %%
result = agent.invoke(
    {"messages": [{"role": "user", "content": "tell me the trend of AAPL?"}]}
)

from pprint import pprint
pprint(result["messages"][-1].content)
# %%
