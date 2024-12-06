from bedrock_client import BedrockClient
from graph import StockAnalysisGraph
from pprint import pprint
import uuid
from langchain_core.agents import AgentFinish

class ChatSession:
    def __init__(self, graph, thread_id=None):
        self.graph = graph
        self.thread_id = thread_id or str(uuid.uuid4())
    
    async def run(self):
        print(f"\n=== 새로운 채팅 세션 시작 (Thread ID: {self.thread_id}) ===")
        print("AI 챗봇입니다. 주식 관련 질문과 일반적인 질문 모두 답변 가능합니다.")
        print("'종료'를 입력하면 대화가 종료됩니다.")
        print("'로그'를 입력하면 도구 사용 기록을 확인할 수 있습니다.")
        print("'기록'을 입력하면 현재 대화 기록을 확인할 수 있습니다.")
        print("'초기화'를 입력하면 대화 기록이 초기화됩니다.")
        
        while True:
            user_input = input("\n질문: ")
            
            if user_input.lower() == '종료':
                print("대화를 종료합니다.")
                break
                
            if user_input.lower() == '로그':
                print("\n=== 도구 사용 로그 ===")
                pprint(self.graph.get_tool_usage_log())
                continue
                
            if user_input.lower() == '기록':
                print("\n=== 대화 기록 ===")
                chat_history = self.graph.get_chat_history(self.thread_id)
                if chat_history:
                    for msg in chat_history:
                        role = "사용자" if msg["role"] == "user" else "AI"
                        print(f"{role}: {msg['content']}")
                else:
                    print("아직 대화 기록이 없습니다.")
                continue
                
            if user_input.lower() == '초기화':
                self.graph.clear_chat_history(self.thread_id)
                print("대화 기록이 초기화되었습니다.")
                continue
            
            print("\n응답: ", end="")
            try:
                response_text = ""
                async for response in self.graph.run(user_input, self.thread_id):
                    if response:
                        response_text = response
                
                if response_text:
                    print(response_text)
                    self.graph.update_chat_history(self.thread_id, user_input, response_text)
                else:
                    print("응답을 생성하지 못했습니다.")
                    
            except Exception as e:
                print(f"\n오류 발생: {e}")
                continue

async def main():
    client = BedrockClient()
    graph = StockAnalysisGraph(client)
    
    while True:
        print("\n=== 메인 메뉴 ===")
        print("1. 새로운 대화 시작")
        print("2. 기존 대화 이어하기")
        print("3. 종료")
        
        choice = input("선택: ")
        
        if choice == "1":
            session = ChatSession(graph)
            await session.run()
        elif choice == "2":
            thread_id = input("Thread ID를 입력하세요: ")
            if thread_id:
                session = ChatSession(graph, thread_id)
                await session.run()
            else:
                print("유효하지 않은 Thread ID입니다.")
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
