#src/function/company_data.py
#설명 : 회사의 주식 데이터와 기본 정보를 가져오는 클래스
import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class CompanyDataInput(BaseModel):
    symbol: str = Field(description="회사의 주식 심볼 (예: 'AAPL')")
    company_name: Optional[str] = Field(
        default="",  # 기본값 설정
        description="회사명 (예: 'Apple')"
    )

class CompanyDataTool(BaseTool):
    name: str = "company_data"
    description: str = "회사의 주가(시가, 종가, 고가, 저가, 거래량), 기본 정보, 재무 지표 등을 조회합니다."
    args_schema: Type[BaseModel] = CompanyDataInput
    return_direct: bool = False

    def _run(
        self,
        symbol: str,
        company_name: Optional[str] = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """동기 실행을 위한 메서드"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if hist.empty:
                return {"error": "주가 데이터를 가져올 수 없습니다."}
            
            current_price = float(hist['Close'].iloc[-1])
            open_price = float(hist['Open'].iloc[-1])
            
            return {
                "basic_info": {
                    "symbol": symbol,
                    "company_name": company_name,
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "market_cap": info.get('marketCap', 'N/A'),
                },
                "stock_data": {
                    "current_price": current_price,
                    "open": open_price,
                    "high": float(hist['High'].iloc[-1]),
                    "low": float(hist['Low'].iloc[-1]),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "day_change": float(((current_price - open_price) / open_price) * 100),
                    "timestamp": datetime.now().isoformat()
                },
                "financial_metrics": {
                    "pe_ratio": info.get('trailingPE', 'N/A'),
                    "dividend_yield": info.get('dividendYield', 'N/A'),
                    "beta": info.get('beta', 'N/A'),
                    "eps": info.get('trailingEps', 'N/A'),
                }
            }
        except Exception as e:
            return {"error": f"데이터 조회 중 오류 발생: {str(e)}"}

    async def _arun(
        self,
        symbol: str,
        company_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """비동기 실행을 위한 메서드"""
        # 비동기 컨텍스트에서 동기 메서드 실행
        return await asyncio.get_event_loop().run_in_executor(
            None, self._run, symbol, company_name, run_manager
        )

