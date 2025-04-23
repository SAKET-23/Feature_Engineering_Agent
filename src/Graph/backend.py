from langchain_core.messages import HumanMessage
from typing import List
from dataclasses import dataclass
from langgraph.graph import StateGraph , START , END
from src.State.state import AgentState
from src.Nodes.nodes import call_model, call_tools, route_to_tools, call_reviewer, call_model_2, route_decision , router, Feat_or_chat, Feature_Engg
from src.State.data_models import InputData

class PythonChatbot:
    def __init__(self):
        super().__init__()
        self.reset_chat()
        self.graph = self.create_graph()
        
    def create_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node('agent', call_model)
        workflow.add_node('tools', call_tools)
        workflow.add_node('reviewer', call_reviewer)
        workflow.add_node("rectifier" , call_model_2)
        workflow.add_node("Query_assesser" , Feat_or_chat)
        workflow.add_node("Feat_Engg" , Feature_Engg)
        
        
        # workflow.add_edge(START, 'agent')
        workflow.add_edge(START, 'Query_assesser')
        workflow.add_conditional_edges('Query_assesser', router, {"feature" : "Feat_Engg" , "chat" : "agent"})
        workflow.add_conditional_edges('agent', route_to_tools, {"tools" : "tools" , "__end__" : END})
        workflow.add_conditional_edges('Feat_Engg', route_to_tools, {"tools" : "tools" , "__end__" : END})
        workflow.add_edge('tools', 'reviewer')
        workflow.add_conditional_edges('reviewer', route_decision, {"agent" : "agent" , "feature":"Feat_Engg" ,"passed" : END})
        # workflow.add_conditional_edges('rectifier', route_to_tools, {"tools" : "tools" , "__end__" : END})
        # workflow.add_edge('tools', 'agent')
        
        return workflow.compile()
    
    def user_sent_message(self, user_query, input_data: List[InputData]):
        starting_image_paths_set = set(sum(self.output_image_paths.values(), []))
        input_state = {
            "user_query" : user_query,
            "messages": self.chat_history + [HumanMessage(content=user_query)],
            "output_image_paths": list(starting_image_paths_set),
            "input_data": input_data,
        }

        result = self.graph.invoke(input_state, {"recursion_limit": 25})
        self.chat_history = result["messages"]
        new_image_paths = set(result["output_image_paths"]) - starting_image_paths_set
        self.output_image_paths[len(self.chat_history) - 1] = list(new_image_paths)
        if "intermediate_outputs" in result:
            self.intermediate_outputs.extend(result["intermediate_outputs"])

    def reset_chat(self):
        self.chat_history = []
        self.intermediate_outputs = []
        self.output_image_paths = {}
