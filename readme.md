# 📈 Stockelper Agent v2
> **AI 기반 주식 투자 도우미 에이전트 - AWS Bedrock & LangChain 활용**

## 🌟 소개
**Stockelper Agent v2**는 AWS Bedrock의 강력한 AI 기능을 활용하여 실시간 주식 시장 분석과 투자 조언을 제공하는 지능형 에이전트입니다. 개인 투자자들의 더 나은 투자 결정을 돕기 위해 설계되었습니다.

---

## ✨ 주요 기능

### 📊 종합 주식 분석
- **기업 정보 분석**  
- 실시간 주가 데이터 모니터링  
- 기업 재무제표 분석  
- PE ratio, 시가총액 등 핵심 지표 분석  

### 🌐 시장 동향 분석
- S&P 500, NASDAQ, DOW 지수 실시간 추적  
- 주요 시장 지표 모니터링  
- 글로벌 시장 트렌드 분석  

### 📈 기술적 분석
- RSI (Relative Strength Index)  
- MACD (Moving Average Convergence Divergence)  
- 볼린저 밴드  
- 이동평균선 분석  

### 🤖 AI 투자 자문
- 데이터 기반 투자 추천  
- 매수/매도 시그널 알림  
- 리스크 평가 리포트  
- 상세 투자 근거 제공  

### 📰 뉴스 & 정보
- Google News API 통합  
- 실시간 시장 뉴스 업데이트  
- 관련 기업 뉴스 모니터링  

### 💬 대화형 인터페이스
- 자연어 기반 질의응답  
- 대화 기록 관리  
- 맥락 기반 응답 생성  
- 일반 질문 지원  

---

## 🛠 기술 스택
- **AI/ML:** AWS Bedrock  
- **프레임워크:** LangChain  
- **데이터 소스:**  
  - yfinance (주식 데이터)  
  - GoogleNews API (뉴스)  
  - pandas-ta (기술적 분석)  
- **통신:** aiohttp (비동기)

---

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/Stockelper_Agent_v2.git
