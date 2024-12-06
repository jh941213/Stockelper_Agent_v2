from langchain_core.tools import BaseTool
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from .company_data_tool import CompanyDataTool
from .market_data_tool import MarketDataTool
from .technical_tool import TechnicalAnalysisTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class StockAdvisorInput(BaseModel):
    symbol: str = Field(..., description="분석할 주식 심볼 (예: AAPL)")
    company_name: str = Field(default="", description="회사명 (선택사항)")

class StockAdvisorTool(BaseTool):
    name: str = "stock_advisor"
    description: str = """종합적인 투자 분석 및 추천을 제공하는 도구입니다. 투자 문의 매수/매도 의견 투자결정에 질문에 대해 사용합니다."""
    
    # 모든 도구들을 Field로 정의
    company_tool: CompanyDataTool = Field(default_factory=CompanyDataTool)
    market_tool: MarketDataTool = Field(default_factory=MarketDataTool)
    technical_tool: TechnicalAnalysisTool = Field(default_factory=TechnicalAnalysisTool)
    args_schema: Type[BaseModel] = StockAdvisorInput

    def __init__(self, **data):
        super().__init__(**data)
        # __init__에서 도구들을 직접 초기화하지 않음

    def _analyze_market_condition(self, market_data: Dict) -> Dict[str, Any]:
        """시장 전반적인 상황 분석"""
        market_sentiment = "neutral"
        market_strength = 0
        
        for index, data in market_data.items():
            if isinstance(data, dict) and "day_change" in data:
                change = data["day_change"]
                if change > 0:
                    market_strength += 1
                elif change < 0:
                    market_strength -= 1
        
        if market_strength >= 2:
            market_sentiment = "bullish"
        elif market_strength <= -2:
            market_sentiment = "bearish"
            
        return {
            "sentiment": market_sentiment,
            "strength": market_strength,
            "details": market_data
        }

    def _analyze_company_fundamentals(self, company_data: Dict) -> Dict[str, Any]:
        """기업 기본 정보 분석"""
        stock_data = company_data.get("stock_data", {})
        financial = company_data.get("financial_metrics", {})
        
        return {
            "price_trend": "상승" if stock_data.get("day_change", 0) > 0 else "하락",
            "volume_status": "활발" if stock_data.get("volume", 0) > 0 else "부진",
            "pe_status": "적정" if 10 <= financial.get("pe_ratio", 15) <= 30 else "주의",
            "details": company_data
        }

    def _generate_recommendation(self, 
                               market_analysis: Dict,
                               company_analysis: Dict,
                               technical_analysis: Dict) -> Dict[str, Any]:
        """투자 추천 생성"""
        buy_signals = 0
        sell_signals = 0
        reasons = []
        
        # 시장 상황 분석
        if market_analysis["sentiment"] == "bullish":
            buy_signals += 1
            reasons.append("시장 전반적으로 상승세")
        elif market_analysis["sentiment"] == "bearish":
            sell_signals += 1
            reasons.append("시장 전반적으로 하락세")
            
        # 기업 기본 정보 분석
        if company_analysis["price_trend"] == "상승":
            buy_signals += 1
            reasons.append("주가 상승 추세")
        if company_analysis["volume_status"] == "활발":
            buy_signals += 1
            reasons.append("거래량 활발")
            
        # 기술적 지표 분석
        tech_summary = technical_analysis.get("analysis_summary", {})
        
        if tech_summary.get("rsi_analysis") == "과매도":
            buy_signals += 1
            reasons.append("RSI 과매도 구간 (매수 기회)")
        elif tech_summary.get("rsi_analysis") == "과매수":
            sell_signals += 1
            reasons.append("RSI 과매수 구간")
            
        if tech_summary.get("macd_analysis") == "상승신호":
            buy_signals += 1
            reasons.append("MACD 상승 신호")
        else:
            sell_signals += 1
            reasons.append("MACD 하락 신호")
            
        # 최종 추천
        confidence = (buy_signals / (buy_signals + sell_signals)) * 100 if (buy_signals + sell_signals) > 0 else 50
        
        if buy_signals > sell_signals:
            recommendation = "매수"
        elif sell_signals > buy_signals:
            recommendation = "매도"
        else:
            recommendation = "관망"
            
        return {
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "timestamp": datetime.now().isoformat()
        }

    async def _arun(
        self,
        symbol: str,
        company_name: str = "",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """비동기 실행을 위한 메서드"""
        try:
            # 세 도구를 동시에 비동기로 실행
            tasks = [
                self.company_tool._arun(symbol=symbol, company_name=company_name),
                self.market_tool._arun(),
                self.technical_tool._arun(symbol=symbol)
            ]
            
            # 모든 태스크를 동시에 실행하고 결과를 기다림
            company_data, market_data, technical_data = await asyncio.gather(*tasks)
            
            # 2. 각 측면 분석
            market_analysis = self._analyze_market_condition(market_data)
            company_analysis = self._analyze_company_fundamentals(company_data)
            
            # 3. 종합 분석 및 추천 생성
            recommendation = self._generate_recommendation(
                market_analysis,
                company_analysis,
                technical_data
            )
            
            return {
                "recommendation": recommendation,
                "market_analysis": market_analysis,
                "company_analysis": company_analysis,
                "technical_analysis": technical_data,
            }
                
        except Exception as e:
            return {"error": f"투자 분석 중 오류 발생: {str(e)}"}

    def _run(
        self,
        symbol: str,
        company_name: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """동기 실행을 위한 메서드"""
        return asyncio.run(self._arun(symbol, company_name, run_manager))