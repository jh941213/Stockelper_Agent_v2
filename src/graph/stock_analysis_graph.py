from langgraph.graph import StateGraph, END
from langchain.agents import create_tool_calling_agent
from typing import List, Dict, Any
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.agents import AgentFinish

from tools.company_data_tool import CompanyDataTool
from tools.market_data_tool import MarketDataTool 
from tools.technical_tool import TechnicalAnalysisTool
from tools.stock_advisor_tool import StockAdvisorTool
from .agent_state import AgentState
from .prompt import create_prompt_template
from .node import Node
from .query_classifier import QueryClassifier

class StockAnalysisGraph:
    def __init__(self, bedrock_client):
        self.llm = bedrock_client.llm
        self.toolkit = [CompanyDataTool(), MarketDataTool(), TechnicalAnalysisTool(), StockAdvisorTool()]
        self.query_classifier = QueryClassifier(self.llm)
        self.node_functions = None
        self.memory = MemorySaver()
        self.app = self._build_graph()

    def _build_graph(self):
        tool_calling_prompt = create_prompt_template()
        tool_runnable = create_tool_calling_agent(self.llm, self.toolkit, prompt=tool_calling_prompt)
        self.node_functions = Node(tool_runnable, self.toolkit, self.query_classifier)
        
        workflow = StateGraph(AgentState)
        
        # 쿼리 분류 노드 추가
        workflow.add_node("classifier", self.node_functions.classify_query)
        workflow.add_node("agent", self.node_functions.run_tool_agent)
        workflow.add_node("action", self.node_functions.execute_tools)
        workflow.add_node("general_response", self.node_functions.handle_general_query)
        
        # 시작점을 classifier로 변경
        workflow.set_entry_point("classifier")
        
        # 조건부 엣지 추가
        workflow.add_conditional_edges(
            "classifier",
            self.node_functions.route_query,
            {
                "STOCK": "agent",
                "GENERAL": "general_response"
            }
        )
        
        workflow.add_edge("action", "agent")
        
        workflow.add_conditional_edges(
            "agent",
            self.node_functions.should_continue,
            {
                "CONTINUE": "action",
                "END": END
            }
        )
        
        # 일반 응답 노드에서 종료
        workflow.add_edge("general_response", END)
        
        # MemorySaver를 체크포인터로 설정하여 그래프 컴파일
        return workflow.compile(checkpointer=self.memory)

    def get_tool_usage_log(self):
        """도구 사용 로그를 반환하는 메서드"""
        if self.node_functions:
            return self.node_functions.tool_usage_log
        return []

    def format_chat_history(self, chat_history):
        """채팅 기록을 문자열로 포맷팅"""
        if not isinstance(chat_history, list):
            # 문자열이 들어온 경우 그대로 반환
            return chat_history
        
        if not chat_history:
            return "이전 대화 없음"
        
        formatted = []
        for msg in chat_history:
            role = "사용자" if msg["role"] == "user" else "AI"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

    async def run(self, query: str, thread_id: str, stream: bool = False):
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            current_state = self.app.get_state(config).values
            chat_history = current_state.get("chat_history", [])
        except:
            chat_history = []

        input_state = {
            "input": query,
            "chat_history": self.format_chat_history(chat_history),
            "is_stock_related": False,
            "agent_outcome": None,
            "intermediate_steps": []
        }

        try:
            result = await self.app.ainvoke(input_state, config=config)
            
            if isinstance(result, dict):
                # agent_outcome이 최상위에 있는 경우
                if 'agent_outcome' in result:
                    agent_outcome = result['agent_outcome']
                    if isinstance(agent_outcome, AgentFinish):
                        response = agent_outcome.return_values.get('output', '')
                        if response:
                            # 직렬화 가능한 형태로 상태 업데이트
                            updated_state = {
                                "input": query,
                                "chat_history": chat_history if isinstance(chat_history, list) else [],
                                "is_stock_related": False,
                                "agent_outcome": {
                                    "return_values": {"output": response}
                                }
                            }
                            self.app.update_state(config, updated_state)
                            yield response
                            return
                
                # general_response에 있는 경우
                if 'general_response' in result:
                    agent_outcome = result['general_response'].get('agent_outcome')
                    if isinstance(agent_outcome, AgentFinish):
                        response = agent_outcome.return_values.get('output', '')
                        if response:
                            # 직렬화 가능한 형태로 상태 업데이트
                            updated_state = {
                                "input": query,
                                "chat_history": chat_history if isinstance(chat_history, list) else [],
                                "is_stock_related": False,
                                "agent_outcome": {
                                    "return_values": {"output": response}
                                }
                            }
                            self.app.update_state(config, updated_state)
                            yield response
                            return
                    
        except Exception as e:
            print(f"\nDEBUG - Error in run: {str(e)}")
            raise e

    def get_chat_history(self, thread_id: str) -> List[str]:
        """특정 쓰레드의 대화 기록 조회"""
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = self.app.get_state(config)
            return state.values.get("chat_history", [])
        except:
            return []

    def clear_chat_history(self, thread_id: str):
        """특정 쓰레드의 대화 기록 초기화"""
        config = {"configurable": {"thread_id": thread_id}}
        empty_state = {
            "input": "",
            "chat_history": [],
            "is_stock_related": False,
            "agent_outcome": None,
            "intermediate_steps": []
        }
        self.app.update_state(config, empty_state)

    def stream(self, query: str, chat_history: List[str] = None):
        if chat_history is None:
            chat_history = []
        return self.app.stream({
            "input": query,
            "chat_history": chat_history,
            "is_stock_related": False,
            "agent_outcome": None,
            "intermediate_steps": []
        })

    def update_chat_history(self, thread_id: str, query: str, response: str):
        """채팅 기록 업데이트"""
        config = {"configurable": {"thread_id": thread_id}}
        try:
            current_state = self.app.get_state(config).values
            chat_history = current_state.get("chat_history", [])
            
            # 리스트가 아닌 경우 새로운 리스트 생성
            if not isinstance(chat_history, list):
                chat_history = []
            
            # 새로운 메시지 추가
            chat_history.extend([
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ])
            
            updated_state = {
                "input": query,
                "chat_history": chat_history,  # 리스트 형태의 채팅 기록
                "is_stock_related": False,
                "agent_outcome": {"return_values": {"output": response}}
            }
            self.app.update_state(config, updated_state)
        except Exception as e:
            print(f"채팅 기록 업데이트 중 오류 발생: {e}")