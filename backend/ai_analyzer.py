import os
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def analyze_sentiment(articles):
    """Analyzes sentiment of news articles using VADER."""
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
    """Generates a summary and insights for a single stock."""
    if not articles:
        return "No news available to generate a summary."
    news_text = " ".join([f"{article['title']}. {article['description']}" for article in articles if article and article.get('title') and article.get('description')])
    if not news_text:
        return "Not enough news content to generate a summary."

    # Check for secrets first, then fall back to environment variables
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found. Please configure your secrets."

    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", api_key=api_key)

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
    """Generates a comparative analysis of two stocks."""
    ticker1, news1 = data1['ticker'], data1['news']
    ticker2, news2 = data2['ticker'], data2['news']
    news_text1 = " ".join([f"{a['title']}" for a in news1[:5] if a and a.get('title')])
    news_text2 = " ".join([f"{a['title']}" for a in news2[:5] if a and a.get('title')])

    if not news_text1 and not news_text2:
        return "Not enough news content for either stock to generate a comparison."
    
    # Check for secrets first, then fall back to environment variables
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found. Please configure your secrets."

    llm = ChatGroq(temperature=0.1, model_name="llama3-70b-8192", api_key=api_key)

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
