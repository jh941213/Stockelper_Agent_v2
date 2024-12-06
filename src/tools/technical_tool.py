# src/function/technical.py
# 기술적 지표를 계산하는 클래스

import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.trend import MACD
import aiohttp
import asyncio
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from langchain_core.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class TechnicalAnalysisInput(BaseModel):
    symbol: str = Field(..., description="분석할 주식 심볼 (예: AAPL)")
    period_days: int = Field(default=180, description="데이터 조회 기간 (일)")
    rsi_period: int = Field(default=14, description="RSI 계산 기간")
    bb_period: int = Field(default=20, description="볼린저 밴드 계산 기간")
    ma_periods: List[int] = Field(default=[50, 200], description="이동평균선 계산 기간 리스트")

class TechnicalAnalysis:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_technical_indicators(
        self,
        symbol: str, 
        period_days: int = 180,
        rsi_period: int = 14,
        bb_period: int = 20,
        ma_periods: List[int] = [50, 200]
    ) -> Dict[str, Any]:
        """
        기술적 지표를 계산하는 메인 함수
        
        Args:
            symbol (str): 주식 심볼
            period_days (int): 데이터 조회 기간 (일)
            rsi_period (int): RSI 계산 기간
            bb_period (int): 볼린저 밴드 계산 기간
            ma_periods (list): 이동평균선 계산 기간 리스트
        """
        try:
            df = await self._fetch_price_data(symbol, period_days)
            if df is None:
                return {'error': '가격 데이터를 가져오는데 실패했습니다.'}

            result = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'period_days': period_days,
                'rsi': await self._calculate_rsi(df, rsi_period),
                'bollinger_bands': await self._calculate_bollinger_bands(df, bb_period),
                'macd': await self._calculate_macd(df),
                'moving_averages': await self._calculate_moving_averages(df, ma_periods)
            }
            
            result['analysis'] = self._analyze_indicators(result)
            return result
            
        except Exception as e:
            return {'error': f'기술적 지표 계산 중 류 발생: {str(e)}'}

    async def _fetch_price_data(self, symbol: str, period_days: int) -> Optional[pd.DataFrame]:
        """가격 데이터 조회"""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
                
            range_param = f"{period_days}d"
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={range_param}"
            
            async with self.session.get(url) as response:
                data = await response.json()
                
            timestamps = data['chart']['result'][0]['timestamp']
            closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
            return pd.DataFrame({'Close': closes}, index=pd.to_datetime(timestamps, unit='s'))
            
        except Exception as e:
            print(f"데이터 조회 실패: {str(e)}")
            return None

    async def _calculate_rsi(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """RSI 계산"""
        rsi_indicator = RSIIndicator(close=df['Close'], window=period)
        current_rsi = rsi_indicator.rsi().iloc[-1]
        return {
            'value': round(current_rsi, 2),
            'period': period
        }

    async def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """볼린저 밴드 계산"""
        bb_indicator = BollingerBands(close=df['Close'], window=period, window_dev=2)
        return {
            'upper': round(bb_indicator.bollinger_hband().iloc[-1], 2),
            'middle': round(bb_indicator.bollinger_mavg().iloc[-1], 2),
            'lower': round(bb_indicator.bollinger_lband().iloc[-1], 2),
            'period': period
        }

    async def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """MACD 계산"""
        macd = MACD(close=df['Close'])
        return {
            'macd': round(macd.macd().iloc[-1], 2),
            'signal': round(macd.macd_signal().iloc[-1], 2),
            'histogram': round(macd.macd_diff().iloc[-1], 2)
        }

    async def _calculate_moving_averages(self, df: pd.DataFrame, periods: List[int]) -> Dict[str, float]:
        """이동평균선 계산"""
        moving_averages = {}
        for period in periods:
            ma = df['Close'].rolling(window=period).mean().iloc[-1]
            moving_averages[f'ma{period}'] = round(ma, 2)
        return moving_averages

    def _analyze_indicators(self, data: Dict[str, Any]) -> Dict[str, str]:
        """기술적 지표 분석"""
        analysis = {}
        
        # RSI 분석
        rsi = data['rsi']['value']
        if rsi > 70:
            analysis['rsi'] = "과매수"
        elif rsi < 30:
            analysis['rsi'] = "과매도"
        else:
            analysis['rsi'] = "중립"
        
        # MACD 분석
        if data['macd']['macd'] > data['macd']['signal']:
            analysis['macd'] = "상승신호"
        else:
            analysis['macd'] = "하락신호"
        
        # 볼린저 밴드 분석
        bb = data['bollinger_bands']
        current_price = bb['middle']
        
        if current_price > bb['upper']:
            analysis['bollinger'] = "상단밴드 상향돌파"
        elif current_price < bb['lower']:
            analysis['bollinger'] = "하단밴드 하향돌파"
        else:
            analysis['bollinger'] = "볼린저밴드 내 움직임"
        
        return analysis

class TechnicalAnalysisTool(BaseTool):
    name: str = "get_technical_analysis"
    description: str = "��� RSI, 볼린저 밴드, MACD 등 기술적 지표를 분석합니다."
    args_schema: Type[BaseModel] = TechnicalAnalysisInput
    
    def _calculate_moving_averages(self, data: pd.DataFrame) -> Dict[str, float]:
        """이동평균선 계산"""
        close_prices = data['Close']
        return {
            "MA5": float(close_prices.rolling(window=5).mean().iloc[-1]),
            "MA20": float(close_prices.rolling(window=20).mean().iloc[-1]),
            "MA60": float(close_prices.rolling(window=60).mean().iloc[-1]),
            "MA120": float(close_prices.rolling(window=120).mean().iloc[-1])
        }

    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """RSI 계산"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def _calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:
        """MACD 계산"""
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return {
            "macd": float(macd.iloc[-1]),
            "signal": float(signal.iloc[-1]),
            "histogram": float(macd.iloc[-1] - signal.iloc[-1])
        }

    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20) -> Dict[str, float]:
        """볼린저 밴드 계산"""
        ma = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=period).std()
        return {
            "upper": float(ma.iloc[-1] + (std.iloc[-1] * 2)),
            "middle": float(ma.iloc[-1]),
            "lower": float(ma.iloc[-1] - (std.iloc[-1] * 2))
        }

    def _analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """거래량 분석"""
        return {
            "current_volume": int(data['Volume'].iloc[-1]),
            "avg_volume_5d": float(data['Volume'].rolling(window=5).mean().iloc[-1]),
            "avg_volume_20d": float(data['Volume'].rolling(window=20).mean().iloc[-1]),
            "volume_trend": "상승" if data['Volume'].iloc[-1] > data['Volume'].rolling(window=5).mean().iloc[-1] else "하락"
        }

    def _analyze_trend(self, data: pd.DataFrame) -> Dict[str, str]:
        """추세 분석"""
        current_price = data['Close'].iloc[-1]
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = data['Close'].rolling(window=60).mean().iloc[-1]
        
        trend = {
            "short_term": "상승" if current_price > ma20 else "하락",
            "medium_term": "상승" if current_price > ma60 else "하락",
            "momentum": "강세" if current_price > ma20 > ma60 else "약세"
        }
        return trend

    def _run(
        self,
        symbol: str,
        period_days: int = 180,
        rsi_period: int = 14,
        bb_period: int = 20,
        ma_periods: List[int] = [50, 200],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """동기 실행을 위한 메서드"""
        try:
            # period_days를 yfinance에서 지원하는 형식으로 변환
            if period_days <= 7:
                period = '1d'
            elif period_days <= 30:
                period = '1mo'
            elif period_days <= 90:
                period = '3mo'
            elif period_days <= 180:
                period = '6mo'
            elif period_days <= 365:
                period = '1y'
            else:
                period = 'max'
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"error": "기술적 분석을 위한 데이터를 가져올 수 없습니다."}
            
            # 직렬화 가능한 형태로 데이터 변환
            technical_data = {
                "moving_averages": {
                    k: float(v) for k, v in self._calculate_moving_averages(hist).items()
                },
                "rsi": float(self._calculate_rsi(hist, period=rsi_period)),
                "macd": {
                    k: float(v) for k, v in self._calculate_macd(hist).items()
                },
                "bollinger_bands": {
                    k: float(v) for k, v in self._calculate_bollinger_bands(hist, period=bb_period).items()
                },
                "volume_analysis": {
                    k: float(v) if isinstance(v, (int, float)) else v 
                    for k, v in self._analyze_volume(hist).items()
                },
                "trend_analysis": self._analyze_trend(hist),
                "timestamp": datetime.now().isoformat()
            }
            
            # 분석 결과에 대한 요약 추가
            analysis_summary = {
                "rsi_analysis": "과매수" if technical_data["rsi"] > 70 else "과매도" if technical_data["rsi"] < 30 else "중립",
                "macd_analysis": "상승신호" if technical_data["macd"]["histogram"] > 0 else "하락신호",
                "trend_summary": technical_data["trend_analysis"]["momentum"]
            }
            technical_data["analysis_summary"] = analysis_summary
            
            return technical_data
        except Exception as e:
            return {"error": f"기술적 분석 중 오류 발생: {str(e)}"}

    async def _arun(
        self,
        symbol: str,
        period_days: int = 180,
        rsi_period: int = 14,
        bb_period: int = 20,
        ma_periods: List[int] = [50, 200],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """비동기 실행을 위한 메서드"""
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self._run(
                symbol=symbol,
                period_days=period_days,
                rsi_period=rsi_period,
                bb_period=bb_period,
                ma_periods=ma_periods
            )
        )

