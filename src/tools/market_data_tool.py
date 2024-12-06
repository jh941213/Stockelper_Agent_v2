

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
from aiohttp import ClientSession
from .news_service import get_market_news
from langchain_core.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class MarketData:
    # 클래스 속성으로 indices 정의
    INDICES = {
        '^GSPC': {
            'name': 'S&P 500',
            'description': '미국 대형주 500개 기업을 포함하는 대표적인 주가지수'
        },
        '^DJI': {
            'name': '다우존스',
            'description': '미국 30대 우량 기업을 대표하는 산업평균지수'
        },
        '^IXIC': {
            'name': '나스닥',
            'description': '기술주 중심의 미국 전자주식시장 지수'
        }
    }

    @staticmethod
    async def fetch_ticker_data(symbol: str, session: ClientSession) -> tuple:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Open'].iloc[0]
            day_change = ((current_price - prev_price) / prev_price) * 100
            return symbol, current_price, day_change
        return symbol, None, None

    @classmethod
    async def get_major_indices(cls) -> dict:
        try:
            result = {
                'indices': {},
                'market_news': await get_market_news()
            }
            
            async with ClientSession() as session:
                tasks = [cls.fetch_ticker_data(symbol, session) for symbol in cls.INDICES.keys()]
                ticker_results = await asyncio.gather(*tasks)
                
                for symbol, price, change in ticker_results:
                    if price is not None:
                        info = cls.INDICES[symbol]
                        result['indices'][info['name']] = {
                            'price': price,
                            'change': change,
                            'description': info['description']
                        }

            return result
        except Exception as e:
            return {'indices': {}, 'market_news': []}

class MarketDataInput(BaseModel):
    pass  # 입력 파라미터가 필요 없음

class MarketDataTool(BaseTool):
    name: str = "get_market_data"
    description: str = "주요 시장 지수(S&P 500, NASDAQ, DOW)3대지수의 현재 상태를 조회합니다."
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,  # 추가 파라미터 허용
    ) -> Dict[str, Any]:
        """동기 실행을 위한 메서드"""
        try:
            # 주요 지수 심볼
            indices = {
                "^GSPC": "S&P 500",
                "^IXIC": "NASDAQ",
                "^DJI": "DOW JONES"
            }
            
            result = {}
            for symbol, name in indices.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if hist.empty:
                    result[name] = {"error": f"{name} 데이터를 가져올 수 없습니다."}
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                open_price = float(hist['Open'].iloc[-1])
                day_change = ((current_price - open_price) / open_price) * 100
                
                result[name] = {
                    "current": current_price,
                    "open": open_price,
                    "high": float(hist['High'].iloc[-1]),
                    "low": float(hist['Low'].iloc[-1]),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "day_change": float(day_change),
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
        except Exception as e:
            return {"error": f"시장 데이터 조회 중 오류 발생: {str(e)}"}

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any,  # 추가 파라미터 허용
    ) -> Dict[str, Any]:
        """비동기 실행을 위한 메서드"""
        # run_manager를 제외하고 _run 메서드 호출
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self._run(**kwargs)  # run_manager 제외
        )


