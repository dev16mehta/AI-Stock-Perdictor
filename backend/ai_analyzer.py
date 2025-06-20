import os
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def analyze_sentiment(articles):
    """
    Analyze sentiment of news articles using VADER sentiment analysis.
    
    Args:
        articles (list): List of news article dictionaries containing title and description
        
    Returns:
        float: Compound sentiment score between -1 (negative) and 1 (positive)
    """
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = []
    if not articles:
        return 0.0
    for article in articles:
        if article and article.get('title') and article.get('description'):
            text = article['title'] + ". " + article['description']
            score = analyzer.polarity_scores(text)
            sentiment_scores.append(score['compound'])
    
    if not sentiment_scores:
        return 0.0
    return sum(sentiment_scores) / len(sentiment_scores)

def get_ai_summary(articles, ticker, investor_level="Beginner"):
    """
    Generate an AI-powered summary of news articles for a stock.
    
    Args:
        articles (list): List of news article dictionaries
        ticker (str): Stock ticker symbol
        investor_level (str): Experience level of the investor ("Beginner" or "Advanced")
        
    Returns:
        str: AI-generated summary of the news articles
    """
    if not articles:
        return "No news available to generate a summary."
    news_text = " ".join([f"{article['title']}. {article['description']}" for article in articles if article and article.get('title') and article.get('description')])
    if not news_text:
        return "Not enough news content to generate a summary."

    # Get API key from environment
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found. Please configure your secrets."

    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", api_key=api_key)

    # Customize prompt based on investor experience level
    if investor_level == "Beginner":
        template = """You are a friendly financial assistant. Based on the following news about {ticker}, provide a simple, easy-to-understand summary for a complete beginner. Explain if the news sounds generally positive or negative and why, avoiding complex jargon. News Articles: "{news_text}" Your simple summary:"""
    else:
        template = """You are an expert financial analyst. Analyze the following news articles for {ticker}. Provide a concise, data-driven summary highlighting key market-moving information. Present a brief "Bull Case" (reasons to be optimistic) and "Bear Case" (reasons to be cautious). News Articles: "{news_text}" Your expert analysis:"""

    prompt = PromptTemplate(template=template, input_variables=["ticker", "news_text"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    try:
        response = llm_chain.invoke({"ticker": ticker, "news_text": news_text})
        return response.get('text', "AI summary could not be generated.")
    except Exception as e:
        return f"Error generating AI summary: {e}"

def get_ai_comparison(data1, data2, investor_level="Beginner"):
    """
    Generate a comparative analysis of two stocks based on their news.
    
    Args:
        data1 (dict): First stock's data containing ticker and news
        data2 (dict): Second stock's data containing ticker and news
        investor_level (str): Experience level of the investor ("Beginner" or "Advanced")
        
    Returns:
        str: AI-generated comparison of the two stocks
    """
    ticker1, news1 = data1['ticker'], data1['news']
    ticker2, news2 = data2['ticker'], data2['news']
    news_text1 = " ".join([f"{a['title']}" for a in news1[:5] if a and a.get('title')])
    news_text2 = " ".join([f"{a['title']}" for a in news2[:5] if a and a.get('title')])

    if not news_text1 and not news_text2:
        return "Not enough news content for either stock to generate a comparison."
    
    # Get API key from environment
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found. Please configure your secrets."

    llm = ChatGroq(temperature=0.1, model_name="llama3-70b-8192", api_key=api_key)

    # Customize prompt based on investor experience level
    if investor_level == "Beginner":
        template = """You are a helpful financial guide. Compare two stocks, {ticker1} and {ticker2}, for a beginner. Based on their latest news, explain which one seems to have more positive news and why. Keep it simple. News for {ticker1}: "{news_text1}" News for {ticker2}: "{news_text2}" Your simple comparison:"""
    else:
        template = """You are a professional financial analyst. Conduct a comparative analysis of {ticker1} versus {ticker2}. Based on the news headlines, identify key themes affecting each company. Conclude with which stock appears to have stronger short-term sentiment and present a potential risk for each. Recent News for {ticker1}: "{news_text1}" Recent News for {ticker2}: "{news_text2}" Your expert comparison:"""

    prompt = PromptTemplate(template=template, input_variables=["ticker1", "ticker2", "news_text1", "news_text2"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    try:
        response = llm_chain.invoke({"ticker1": ticker1, "ticker2": ticker2, "news_text1": news_text1, "news_text2": news_text2})
        return response.get('text', "AI comparison could not be generated.")
    except Exception as e:
        return f"Error generating AI comparison: {e}"

def get_ai_portfolio_analysis(report_data_string):
    """
    Generates an AI-powered analysis of a user's playground portfolio.
    
    Args:
        report_data_string (str): String containing portfolio metrics and data
        
    Returns:
        str: Markdown-formatted analysis with recommendations
    """
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found."

    llm = ChatGroq(temperature=0.2, model_name="llama3-70b-8192", api_key=api_key)
    
    template = """
    You are an encouraging and insightful financial analyst reviewing a user's virtual stock portfolio.
    Your tone should be positive and educational.
    Based on the following data, provide a concise "Portfolio Health Report".

    The report should have three sections in markdown format:
    1.  **Overall Summary:** A brief, 2-3 sentence summary of the portfolio's current state.
    2.  **Key Observations:** 2-3 bullet points highlighting the most important findings (e.g., strong diversification, high risk in one stock, positive news sentiment).
    3.  **Actionable Recommendations:** 2 bullet points with suggestions for the user to consider. Frame these as educational tips, not direct financial advice.

    Here is the data:
    {report_data}

    Your AI-Generated Report:
    """

    prompt = PromptTemplate(template=template, input_variables=["report_data"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    try:
        response = llm_chain.invoke({"report_data": report_data_string})
        return response.get('text', "AI analysis could not be generated.")
    except Exception as e:
        return f"Error generating AI analysis: {e}"