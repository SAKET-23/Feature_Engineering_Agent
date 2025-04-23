from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.State.state import AgentState, Reviewer, Chat_or_Feature_bot
import json
from typing import Literal
from src.Tools.tools import complete_python_task
# from langgraph.prebuilt import ToolInvocation, ToolExecutor
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode

# from langgraph.prebuilt import tools_condition
import os


llm = ChatOpenAI(model="gpt-4o", temperature=0)

tools = [complete_python_task]


def create_data_summary(state: AgentState) -> str:
    summary = ""
    variables = []
    for d in state["input_data"]:
        variables.append(d.variable_name)
        summary += f"\n\nVariable: {d.variable_name}\n"
        summary += f"Description: {d.data_description}"
    
    if "current_variables" in state:
        remaining_variables = [v for v in state["current_variables"] if v not in variables]
        for v in remaining_variables:
            summary += f"\n\nVariable: {v}"
    return summary

def route_to_tools(
    state: AgentState,
) -> Literal["tools", "__end__"]:
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route back to the agent.
    """

    if messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"


def Feat_or_chat(state : AgentState):
    """
    Based on the user query decides whether which Agent to route to .
    """
    
    msg = """"
            You are an intent classifier. Given a user query, decide if the user wants to perform feature engineering on a dataset.

            Output format:
            {{
            "perform_feature_engineering": true/false,
            "target_column": "<name of the target column if mentioned, else empty string>"
            }}

            Examples:
            Input: "Perform feature engineering on this dataset with target column 'price'"
            Output: {{ "perform_feature_engineering": true, "target_column": "price" }}

            Input: "Perform feature engineering on this dataset"
            Output: {{ "perform_feature_engineering": false, "target_column": "" }}

            Input: "Can you visualize the null value distribution?"
            Output: {{ "perform_feature_engineering": false, "target_column": "" }}

            Input: "Apply transformations for model training. Target is 'churn'."
            Output: {{ "perform_feature_engineering": true, "target_column": "churn" }}

            Now classify the following user query: {user_query}
            
          """

    chat_template2 = ChatPromptTemplate.from_messages([
        ("system", msg ),
    ])
     
    reviewer = chat_template2 | llm.with_structured_output(Chat_or_Feature_bot)
    result = reviewer.invoke({"user_query": state["user_query"]})
    print(result)
    
    return {'agent_caller' : result.output , 'target_column' : result.target_column}

def router(state: AgentState) -> Literal["feature", "chat"]:
    if state["agent_caller"]:
        return "feature"
    else: 
        return "chat" 

def Feature_Engg(state: AgentState):

    current_data_template  = """The following data is available:\n{data_summary}"""
    current_data_message = HumanMessage(content=current_data_template.format(data_summary=create_data_summary(state)))

    # Avoid duplicate data message
    if not state["messages"] or (state["messages"] and state["messages"][-1].content != current_data_message.content):
        state["messages"] = [current_data_message] + state["messages"]

    
    model = llm.bind_tools(tools)


    with open(os.path.join(os.path.dirname(__file__), "../prompts/feature_Engg.md"), "r") as file:
        prompt = file.read()

    chat_template = ChatPromptTemplate.from_messages([
        ("system", prompt),
    ])
    model = chat_template | model
    
    
    llm_outputs = model.invoke({"state" : state  })
    # print(llm_outputs )
    # print(current_data_message.content)
    return {"messages": [llm_outputs], "intermediate_outputs": [current_data_message.content]}


def call_model(state: AgentState):

    current_data_template  = """The following data is available:\n{data_summary}"""
    current_data_message = HumanMessage(content=current_data_template.format(data_summary=create_data_summary(state)))

    # Avoid duplicate data message
    if not state["messages"] or (state["messages"] and state["messages"][-1].content != current_data_message.content):
        state["messages"] = [current_data_message] + state["messages"]

    
    model = llm.bind_tools(tools)


    with open(os.path.join(os.path.dirname(__file__), "../prompts/main_prompt.md"), "r") as file:
        prompt = file.read()

    chat_template = ChatPromptTemplate.from_messages([
        ("system", prompt),
        ("placeholder", "{messages}"),
    ])
    model = chat_template | model
    
    
    llm_outputs = model.invoke(state)
    print(state)
    return {"messages": [llm_outputs], "intermediate_outputs": [current_data_message.content]}


def call_tools(state: AgentState):
    last_message = state["messages"][-1]

    tool_calls = getattr(last_message, "tool_calls", [])
    if not tool_calls:
        return {"messages": []}

    tool_messages = []
    state_updates = {}

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_input = {**tool_call["args"], "graph_state": state}
        tool_call_id = tool_call["id"]

        # Find the corresponding tool
        tool = next((t for t in tools if getattr(t, 'name', None) == tool_name), None)

        if tool is None:
            tool_messages.append(ToolMessage(
                content=f"Tool '{tool_name}' not found.",
                name=tool_name,
                tool_call_id=tool_call_id
            ))
            continue

        try:
            # If using LangChain tool interface
            if hasattr(tool, "invoke"):
                result = tool.invoke(tool_input)
            else:
                result = tool(**tool_input)

            # Handle (message, updates) or just message
            if isinstance(result, tuple) and len(result) == 2:
                tool_output, updates = result
            else:
                tool_output, updates = result, {}

            tool_messages.append(ToolMessage(
                content=str(tool_output),
                name=tool_name,
                tool_call_id=tool_call_id
            ))

            # Merge updates into state_updates
            for k, v in updates.items():
                if k in state_updates and isinstance(state_updates[k], list):
                    state_updates[k].extend(v)
                else:
                    state_updates[k] = v

        except Exception as e:
            tool_messages.append(ToolMessage(
                content=f"Error executing tool '{tool_name}': {str(e)}",
                name=tool_name,
                tool_call_id=tool_call_id
            ))

    # Attach tool messages to state
    if "messages" not in state_updates:
        state_updates["messages"] = []

    state_updates["messages"].extend(tool_messages)
    print(state_updates)
    return state_updates


def call_reviewer(state : AgentState):
    """
    Review's the code and suggest's any potential improvements or optimizations that could enhance its performance, readability, or functionality.
    """
    
    with open(os.path.join(os.path.dirname(__file__), "../prompts/reviewer.md"), "r") as file:
        msg = file.read()

    chat_template2 = ChatPromptTemplate.from_messages([
        ("system", msg ),
    ])
     
    reviewer = chat_template2 | llm.with_structured_output(Reviewer)
    code_to_review = state["intermediate_outputs"][-1]["code"]
    result = reviewer.invoke({"code": code_to_review,
                              "user_query" : state["user_query"],
                              "output":state["intermediate_outputs"][-1]["output"] })
    print(result)
    
    return {'grade' : result.output , 'Feedback' : result.Feedback}


def call_model_2(state: AgentState):

    print("Enterd the Call2 loop")
    chat_template = ChatPromptTemplate.from_messages([
        ("system", "You are an AI code fixer. Use the following feedback to improve the code."),
        ("user", "Feedback:\n{feedback}\n\nCode:\n{code}")
    ])

    llm_chain = chat_template | llm.bind_tools(tools)
    llm_outputs = llm_chain.invoke({
        "feedback": state["Feedback"],
        "code": state["intermediate_outputs"][-1]["code"]
        
    })

    # Reset messages with only the fixed result
    return {"messages": [llm_outputs]}

def route_decision(state: AgentState):
    # print("\n\n")
    # print(state["grade"] , state["agent_caller"] , state["Feedback"])
    # print("\n\n")
    # if state["grade"] == False:
        if state["agent_caller"]:
            return "feature"
        else:
            return "agent"
    # else:
    #     print(state)
    #     return "passed"
        