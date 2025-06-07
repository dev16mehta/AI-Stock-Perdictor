from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

def analyze_sentiment(articles):
    """Analyzes sentiment of news articles using VADER."""
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = []
    for article in articles:
        if article['title'] and article['description']:
            text = article['title'] + ". " + article['description']
            score = analyzer.polarity_scores(text)
            sentiment_scores.append(score['compound'])
    
    if not sentiment_scores:
        return 0.0

    return sum(sentiment_scores) / len(sentiment_scores)

def get_ai_summary(articles, ticker, investor_level="Beginner"):
    """Generates a summary and insights using Groq and LangChain."""
    if not articles:
        return "No news available to generate a summary."

    # Combine headlines and descriptions for the AI
    news_text = " ".join([f"{article['title']}. {article['description']}" for article in articles])

    # Initialize the Groq LLM
    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

    # Creative Prompt Engineering
    if investor_level == "Beginner":
        template = """
        You are a friendly financial assistant. Based on the following news about {ticker}, 
        provide a simple, easy-to-understand summary for a complete beginner. 
        Explain if the news sounds generally positive or negative and why, avoiding complex jargon.
        
        News Articles: "{news_text}"
        
        Your simple summary:
        """
    else: # Advanced
        template = """
        You are an expert financial analyst. Analyze the following news articles for {ticker}.
        Provide a concise, data-driven summary highlighting key market-moving information.
        Present a brief "Bull Case" (reasons to be optimistic) and "Bear Case" (reasons to be cautious) based on the news sentiment and content.
        
        News Articles: "{news_text}"

        Your expert analysis:
        """

    prompt = PromptTemplate(template=template, input_variables=["ticker", "news_text"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    try:
        response = llm_chain.invoke({"ticker": ticker, "news_text": news_text})
        return response['text']
    except Exception as e:
        return f"Error generating AI summary: {e}"
