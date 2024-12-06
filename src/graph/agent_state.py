from typing import TypedDict, Annotated, Union, List
from langchain_core.agents import AgentAction, AgentFinish
import operator

class AgentState(TypedDict):
    input: str
    chat_history: List[str]
    agent_outcome: Union[AgentAction, List, AgentFinish, None]
    intermediate_steps: Annotated[List[tuple[AgentAction, str]], operator.add]
    is_stock_related: bool