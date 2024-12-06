#src/function/news_service.py
#설명 : 뉴스를 가져오는 함수

from GoogleNews import GoogleNews
import asyncio

async def get_market_news():
    try:
        # GoogleNews 작업을 별도 스레드에서 실행
        def fetch_news():
            googlenews = GoogleNews(lang='en', period='1d')
            market_keywords = "US stock market"
            googlenews.search(market_keywords)
            news = googlenews.results()[:10]
            googlenews.clear()
            return news
            
        # 동기 작업을 비동기적으로 실행
        market_news = await asyncio.to_thread(fetch_news)
        return market_news
    except Exception as e:
        print(f"주식 뉴스 조회 실패: {str(e)}")
        return []
    