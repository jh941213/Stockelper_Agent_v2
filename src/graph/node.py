from langchain_core.agents import AgentFinish, AgentAction
from langgraph.prebuilt.tool_executor import ToolExecutor
from typing import Dict, Any
from datetime import datetime

class Node:
    def __init__(self, tool_runnable, toolkit, query_classifier):
        self.tool_runnable = tool_runnable
        self.tool_executor = ToolExecutor(toolkit)
        self.query_classifier = query_classifier
        self.tool_usage_log = []  # 도구 사용 로그 저장

    def log_tool_usage(self, tool_name: str, input_data: str, output_data: str):
        """도구 사용 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "input": input_data,
            "output": output_data
        }
        self.tool_usage_log.append(log_entry)
        print(f"\n[도구 사용 로그]")
        print(f"도구: {tool_name}")
        print(f"입력: {input_data}")
        print(f"출력: {output_data[:200]}..." if len(str(output_data)) > 200 else f"출력: {output_data}")
        print("-" * 50)

    def classify_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """쿼리를 분류하고 상태에 저장"""
        is_stock_related = self.query_classifier.classify_query(state["input"])
        return {"is_stock_related": is_stock_related}

    def route_query(self, state: Dict[str, Any]) -> str:
        """분류 결과에 따라 다음 노드 결정"""
        return "STOCK" if state["is_stock_related"] else "GENERAL"

    def handle_general_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """일반 질문 처리"""
        chat_history = state.get("chat_history", [])
        response = self.query_classifier.get_general_response(
            state["input"], 
            chat_history
        )
        
        return {
            "agent_outcome": AgentFinish(return_values={"output": response}, log=""),
            "chat_history": chat_history
        }

    def run_tool_agent(self, state):
        """도구 사용 에이전트 실행"""
        print("\n[에이전트 실행]")
        print(f"입력: {state['input']}")
        
        chat_history = state.get("chat_history", [])
        agent_outcome = self.tool_runnable.invoke(state)
        
        return {
            "agent_outcome": agent_outcome,
            "chat_history": chat_history
        }

    def execute_tools(self, state):
        agent_action = state["agent_outcome"]
        steps = []
        
        if not isinstance(agent_action, list):
            agent_action = [agent_action]
            
        for action in agent_action:
            print(f"\n[도구 실행] {action.tool} 실행 시작")
            output = self.tool_executor.invoke(action)
            steps.append((action, str(output)))
            
            # 도구 사용 로깅
            self.log_tool_usage(
                tool_name=action.tool,
                input_data=str(action.tool_input),
                output_data=str(output)
            )
            
        return {"intermediate_steps": steps}

    @staticmethod
    def should_continue(data):
        if isinstance(data["agent_outcome"], AgentFinish):
            return "END"
        return "CONTINUE"