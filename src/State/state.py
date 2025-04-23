import operator
from typing import Sequence, TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from src.State.data_models import InputData
from typing import Dict
from pydantic import BaseModel

class AgentState(TypedDict):
    user_query: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input_data: Annotated[List[InputData], operator.add]
    intermediate_outputs: Annotated[List[dict], operator.add]
    current_variables: dict
    output_image_paths: Annotated[List[str], operator.add]
    Feedback : str
    grade : bool
    agent_caller : bool
    target_column : str


class Reviewer(BaseModel):
    output : bool 
    Feedback : str
    
class Chat_or_Feature_bot(BaseModel):
    output : bool
    target_column : str