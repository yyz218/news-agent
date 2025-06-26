from typing import List, Dict, Any
from pydantic import BaseModel, Field
import datetime, os, requests
from newsapi import NewsApiClient
import re

class SearchQueryList(BaseModel):
    query: List[str] = Field(
        description="A list of search queries to be used for web research."
    )
    rationale: str = Field(
        description="A brief explanation of why these queries are relevant to the research topic."
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the provided summaries are sufficient to answer the user's question."
    )
    knowledge_gap: str = Field(
        description="A description of what information is missing or needs clarification."
    )
    follow_up_queries: List[str] = Field(
        description="A list of follow-up queries to address the knowledge gap."
    )

class NewsSearchInput(BaseModel):
    query: str = Field(..., description="News search keywords")
    from_date: str | None = Field(
        default=None, description="start date YYYY-MM-DD"
    )
    to_date: str | None = Field(
        default=None, description="end date YYYY-MM-DD"
    )
    language: str = Field(default="en", description="ISO 639-1")

def extract_video(article: dict) -> str | None:
    yt_match = re.search(r"(https?://www\.youtube\.com/watch\?v=[\w-]+)", article.get("content",""))
    return yt_match.group(1) if yt_match else None

def news_search(params: NewsSearchInput) -> List[Dict[str, Any]]:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY is not set in environment variables")

    client = NewsApiClient(api_key=api_key)

    today = datetime.date.today()
    frm = params.from_date or str(today - datetime.timedelta(days=7))
    to_  = params.to_date or str(today)

    resp = client.get_everything(
        q=params.query,
        from_param=frm,
        to=to_,
        language=params.language,
        sort_by="relevancy",
        page_size=10,
    )

    articles = resp.get("articles", []) or []
    results: List[Dict[str, Any]] = []
    for art in articles:
        results.append(
            {
                "title":        art.get("title", ""),
                "snippet":      art.get("description") or (art.get("content") or "")[:160],
                "url":          art.get("url", ""),
                "published_at": (art.get("publishedAt") or "")[:10],
                "image_url": art.get("urlToImage", ""), 
                "video_url": extract_video(art), 
            }
        )
    return results
