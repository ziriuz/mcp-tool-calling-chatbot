import asyncio
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import BaseTool, ArgsSchema
from langgraph.graph import START, END, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, List, Optional, Any, Tuple

import prompt_templates
from logger import Logger


# Define state for application
class LLMChatState(TypedDict):
    query: str  # Human message to LLM
    execute_mode: bool  # True if command should be executed automatically
    iterations: int
    generated: BaseMessage
    artifacts: List
    output: str  # STDOUT captured from execution of command


def isinstance_of_LLMChatState(obj: dict) -> bool:
    return isinstance(obj, dict) and all(k in obj for k in LLMChatState.__annotations__)


class ToolConfig:
    def __init__(self, callable_tool, direct_response=False, auto_exec=True, is_mcp_tool=False, enabled=True):
        self.function = callable_tool
        self.direct_response = direct_response
        self.auto_exec = auto_exec
        self.is_mcp_tool = is_mcp_tool
        self.enabled = enabled


class LLMChatAgent(Logger):
    # When User approval is required to run any tool Then ask user for confirmation.
    TOOL_CALLING_SYSTEM_MESSAGE = """
    You can use available tools to retrieve additional information or respond directly with your own answer.
    
    Given tool is called, 
    When tool returns error in response, 
    Then fix input and try to call that tool one more time (You have {max_attempts} attempts to fix error).
    Avoid mentioning errors and fixes you have done in final response, just provide answer to question.
    When unable to fix errors after all attempts say `I cannot answer this question`.    
    """

    def __init__(self, agent_name: str, log_color: str, chat_model: BaseChatModel,
                 system_message: str = prompt_templates.QA_ASSISTANT_INSTRUCTION, toolkit: dict = None):

        self.name = agent_name
        self.color = log_color
        self.log("Initializing...")
        self.__llm = chat_model
        self.__system_instruction = system_message
        self.__toolkit = toolkit
        self.__graph = self.build_workflow()
        self.__history = []
        self.__max_iterations = 4
        if self.__system_instruction:
            self.__remember(SystemMessage(content=self.__system_instruction))

        if self.__toolkit is not None:
            self.__remember(
                SystemMessage(content=self.TOOL_CALLING_SYSTEM_MESSAGE.format(max_attempts=self.__max_iterations-1))
            )

    def set_model(self, chat_model: BaseChatModel):
        self.__llm = chat_model
        self.log(f"!!! Model changed to: {self.get_llm_name()}")

    def get_toolkit(self):
        return self.__toolkit

    def get_history(self):
        return self.__history

    def set_history(self, history):
        self.__history = history

    def __remember(self, message: BaseMessage, verbose: bool = True):
        if verbose:
            self.log_hist(message.pretty_repr())
        self.__history.append(message)
        return message

    def __log_action(self, action: str, iteration: int):
        self.log(">>> {action} ({iter}) >>>", action=action, iter=f"iteration: {iteration}")

    def __generate(self, state: LLMChatState):

        iterations = state.get("iterations", 0)

        if iterations == 0:
            self.log("********** {action} **********", action="START PROCESSING REQUEST")
            self.__remember(HumanMessage(content=state["query"]))

        self.__log_action("GENERATE", iterations + 1)

        tools = [tool.function for tool in self.__toolkit.values() if tool.enabled]

        llm_with_tools = self.__llm.bind_tools(tools)
        llm_response = llm_with_tools.invoke(self.__history)

        return {"generated": self.__remember(llm_response), "output": llm_response.content, "iterations": iterations}

    def __decide_next_action(self, state: LLMChatState):
        llm_response = state["generated"]
        if state["iterations"] >= self.__max_iterations:
            self.log("********** NEXT ACTION: finish due to max iterations reached **********")
            return "end"
        if not llm_response:
            self.log("********** NEXT ACTION: LLM reasoning ********** ")
            return "generate"
        if llm_response.tool_calls is not None and len(llm_response.tool_calls) > 0:
            self.log("********** NEXT ACTION: Tool calling ********** ")
            return "handle_tool_calls"
        else:
            self.log("********** {action} **********", action="FINISH PROCESSING REQUEST")
            return "end"

    def __handle_tool_calls(self, state: LLMChatState):

        self.__log_action("HANDLE TOOL CALLS", state['iterations'] + 1)

        llm_response = state["generated"]
        content = ""
        generated = None
        direct_response = False
        artifacts = state["artifacts"] if state.get("artifacts") else []
        for tool_call in llm_response.tool_calls:

            tool: ToolConfig = self.__toolkit[tool_call["name"]]
            args = ', '.join([f"{k}=`{v}`" for k, v in tool_call['args'].items()])

            if tool.auto_exec or state['execute_mode']:
                self.log("Calling {tool_name}({args})", tool_name=tool_call['name'], args=args)
                # try:
                # Handle both sync and async tools properly
                if tool.is_mcp_tool and hasattr(tool.function, 'ainvoke'):
                    # For MCP tools, create a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        tool_msg = loop.run_until_complete(tool.function.ainvoke(tool_call))
                    finally:
                        loop.close()
                else:
                    tool_msg = tool.function.invoke(tool_call)

                # except Exception as e:
                #     self.log("Tool execution failed: {error}", error=str(e))
                #     tool_msg = ToolMessage(
                #         f"Tool execution failed: {str(e)}",
                #         tool_call_id=tool_call["id"]
                #     )
            else:
                self.log("Requested {tool_name}({args})", tool_name=tool_call['name'], args=args)
                tool_msg = ToolMessage(f"User approval required to execute {tool_call['name']}({args})", tool_call_id=tool_call["id"])

            self.log("Received result of type {artifact_type}", artifact_type=type(tool_msg.artifact if tool_msg.artifact is not None else tool_msg.content))
            artifacts.append({
                "input": f"{tool_call['name']}({args})",
                "result": tool_msg.artifact if tool_msg.artifact is not None else tool_msg.content
            })

            self.__remember(tool_msg)

            if tool.direct_response:
                self.log(">>> TOOL DIRECT RESPONSE: {content}", content=tool_msg.content)
                direct_response = True
                content += tool_msg.content

        if direct_response:
            generated = self.__remember(AIMessage(content))

        return {"generated": generated, "output": content, "artifacts": artifacts, "iterations": state["iterations"] + 1}

    def build_workflow(self):
        workflow = StateGraph(LLMChatState)

        # Define the nodes
        workflow.add_node("generate", self.__generate)
        workflow.add_node("handle_tool_calls", self.__handle_tool_calls)

        # Build graph
        workflow.add_edge(START, "generate")
        workflow.add_conditional_edges(
            "generate",
            self.__decide_next_action,
            {
                "end": END,
                "handle_tool_calls": "handle_tool_calls",
            },
        )
        workflow.add_conditional_edges(
            "handle_tool_calls",
            self.__decide_next_action,
            {
                "end": END,
                "generate": "generate",
            },
        )

        return workflow.compile()

    def invoke(self, query: str, execute_mode: bool = False):
        return self.__graph.invoke({"query": query, "execute_mode": execute_mode})

    def get_graph_image(self):
        return self.__graph.get_graph().draw_mermaid_png()

    def get_llm_name(self):
        return self.__llm.model if hasattr(self.__llm, 'model') else self.__llm.model_name

    def get_system_instruction(self):
        return self.__system_instruction


class ToolInput(BaseModel):
    query: str = Field(description="Data retrieval Query in natural language")


# Note: It's important that every field has type hints. BaseTool is a
# Pydantic class and not having type hints can lead to unexpected behavior.
class CallAgentTool(BaseTool):
    name: str = "{name}"
    description: str = "{description}"
    args_schema: Optional[ArgsSchema] = ToolInput
    return_direct: bool = True
    response_format: str = "content_and_artifact"
    agent: LLMChatAgent = None

    def __init__(self, name: str, description: str, agent: LLMChatAgent, **kwargs: Any):
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.agent = agent

    def _run(
            self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Tuple[str, dict]:
        """Use the tool."""
        response = self.agent.invoke(query, True)
        output = f"Response to request `{query}` is: \n {response['output']}"
        return output, response

