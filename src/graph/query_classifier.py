from typing import List

class QueryClassifier:
    def __init__(self, llm):
        self.llm = llm
        
    def classify_query(self, query: str) -> bool:
        """
        쿼리가 주식 관련 질문인지 판단합니다.
        """
        system_prompt = """당신은 사용자의 질문이 주식/금융 시장 관련 질문인지 판단하는 분류기입니다.
        다음과 같은 주제들이 포함되면 주식 관련 질문으로 판단하세요:
        - 특정 회사의 주가나 정보 요청
        - 시장 동향이나 지수 관련 질문
        - 기술적 분석이나 차트 관련 질문
        - 투자나 트레이딩 관련 질문
        - 이전 대화에서 언급된 주식/금융 관련 내용에 대한 후속 질문
        
        True 또는 False로만 답변하세요.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 질문이 주식/금융 시장 관련 질문인가요?: {query}"}
        ]
        
        response = self.llm.invoke(messages)
        # AIMessage 객체에서 content 추출
        response_text = response.content if hasattr(response, 'content') else str(response)
        return 'true' in response_text.lower()

    def get_general_response(self, query: str, chat_history: List[dict] = None) -> str:
        """
        일반적인 질문에 대한 응답을 생성합니다.
        """
        messages = [
            {"role": "system", "content": "당신은 친절하고 지식이 풍부한 AI 어시스턴트입니다. 이전 대화 내용을 참고하여 일관성 있게 답변해주세요."},
        ]
        
        # 이전 대화 내역 추가
        if chat_history:
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": query})
        
        response = self.llm.invoke(messages)
        # AIMessage 객체에서 content 추출
        return response.content if hasattr(response, 'content') else str(response)