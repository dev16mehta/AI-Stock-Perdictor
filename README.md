# QuantViewAI

- This is an interactive web application that combines real-time market data, financial news sentiment, and generative AI to deliver comprehensive stock insights. 
- This tool is designed for both beginner and advanced investors, offering side-by-side stock comparisons and customisable analysis.


## Core Features
- Real-Time Data: Pulls live market data, historical prices, and company financials using the yFinance library.

- Side-by-Side Comparison: Analyse two stocks simultaneously to compare performance, sentiment, and key metrics.

- Sentiment Analysis: Fetches the latest financial news from NewsAPI and analyses its sentiment using VADER to generate a positive/negative score.

- AI-Generated Insights: Leverages the Groq API with Llama 3 via LangChain to generate:

  - Plain-English summaries for beginners.

  - Expert "Bull vs. Bear" cases for advanced settings.

  - Direct comparative analysis when viewing two stocks.

  - Interactive UI: A clean, user-friendly interface built with Streamlit that allows for dynamic ticker input and date range selection.

## Tech Stack used:
- Frontend: Streamlit
- Data Retrieval: yFinance, NewsAPI
- Data Processing: Pandas, NumPy
- AI & NLP: LangChain, LangChain-Groq (Llama 3), VADER Sentiment
- Plotting: Plotly

## Getting Started
Follow these instructions to set up and run the project on your local machine!

Prerequisites:
1. Python 3.8 or higher (Used 3.10 for this project)
2. Git

Steps:
1. Clone the Repository.

First, clone the repository to your local machine.

```bash
git clone https://github.com/dev16mehta/AI-Stock-Perdictor.git
cd AI-Stock-Perdictor
```

2. Set Up a Virtual Environment:
It's highly recommended to use a virtual environment to manage project dependencies.

On macOS/Linux:
```bash
python3 -m venv .venv 
source .venv/bin/activate
```

On Windows:
```bash
python -m v'env .venv
.\.venv\Scripts\activate
```

3. Install Dependencies:
Install all the required Python libraries using the 'requirements.txt' file.
```bash
pip install -r requirements.txt
```

4. Set Up API Keys:
This project requires API keys from NewsAPI and Groq.

Create a file named '.env' in the root of your project directory.

Sign up for your free keys:

[NewsAPI](https://newsapi.org/)
[Groq](https://console.groq.com/keys)

Add your keys to the .env file like this:
```bash
NEWS_API_KEY="YOUR_NEWSAPI_KEY_HERE"
GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"
```

Note: The .gitignore file is already configured to prevent this file from being committed to GitHub.

## How to Run the Application:
With your environment activated and API keys in place, start the Streamlit server with a single command:
```bash
streamlit run QuantViewAI.py
```

A new tab should automatically open in your web browser at http://localhost:8501.

## How to Use:
- Enter Tickers: In the sidebar, enter one or two stock tickers, separated by a comma (e.g., NVDA, AMD).
- Select Dates: Choose the start and end dates for the historical data analysis.
- Choose Profile: Select your investor profile ("Beginner" or "Advanced") to tailor the AI-generated summaries to your needs.
- Analyse: Click the "Analyse Stocks" button.
- Explore: View the normalised performance chart, read the AI insights, and explore the side-by-side comparison of metrics, news, and financials.

Pro Tip for International Stocks: For stocks outside the US, you may need to add a market suffix. For example:
Barclays (London): BARC.L
Volkswagen (Germany): VOW3.DE
Reliance (India): RELIANCE.NS

App Pages:
- Analyser: The main analysis page. View advanced charts, AI insights, detailed financials, and price predictions. Add stocks to your watchlist or portfolio from here.

- My Watchlist: A personalised dashboard to monitor stocks you are interested in.

- AI Screener: Use natural language to discover new investment opportunities.

- My Portfolio: Track your personal stock holdings, including cost basis and real-time profit/loss.

## License
This project is licensed under the MIT License. [MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgements
A big thank you to the providers of the free APIs that make this project possible: Yahoo Finance, NewsAPI, and Groq.

The Streamlit team for making web app development in Python so accessible.
