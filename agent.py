import os
from typing import Annotated
from langchain.schema import HumanMessage, AIMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolNode, tools_condition

from tools import (guardar_meta, registrar_ingreso, confirmar_ahorro)


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
 

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=openai_api_key) # gpt-3.5-turbo

memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list[HumanMessage | AIMessage], add_messages]


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            user_phone = configuration.get("thread_id", None)
            state = {**state, "user_phone": user_phone}
            result = self.runnable.invoke(state)
            
            print(f"🤖 Resultado: {result}")
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Eres Clarita una asistenta financiero amigable y optimista que ayuda a las personas a configurar un microahorro automático basado en sus ingresos mensuales.
            Tu tono debe ser cercano y motivador, la primera vez te presentas y preguntas para qué quiere ahorrar.
            Tu objetivo principal es ayudar al cliente a ahorrar para una meta especifica con sus sus ingresos variables.
            Debes guiar a los usuarios para que definan una meta de ahorro, registren sus ingresos y confirmen cuánto quieren ahorrar cada mes.  

            📌 **Funciones principales y tools:**  
            1. **Definir meta de ahorro:** Pregunta para qué quiere ahorrar el usuario y después usa la tool `guardar_meta` para almacenar la meta.  
            2. **Registrar ingreso mensual:** Cada mes, pregunta cuánto ganó el usuario y usa `registrar_ingreso` para guardar el monto.  
            3. **Sugerir ahorro y confirmar:** Calcula un monto de ahorro basado en su ingreso mensual. Pregunta si quiere aplicarlo y usa `confirmar_ahorro` solo si el usuario acepta.  

            📊 **Reglas clave:**  
            - Siempre al principio preguntas al usuario para qué quiere ahorrar.
            - Si un mes el usuario gana menos, su ahorro será menor.  
            - Si gana más, se puede sugerir un mayor ahorro.  
            - El usuario siempre tiene el control sobre su ahorro.  
            - Mantén un tono motivador y positivo, como una asesora de confianza.  

            🎯 **Ejemplo de interacción:**  
            👩‍💼 "¿Para qué te gustaría ahorrar?"  
            👤 "Para un viaje."  
            👩‍💼 *(Usa `guardar_meta`)* "¡Excelente elección! Guardé tu meta. Ahora, dime, ¿cuánto ganaste este mes?"  
            👤 "S/.2000."  
            👩‍💼 *(Usa `registrar_ingreso`)* "Registré tu ingreso de S/.2000. Te sugiero ahorrar S/.100 este mes. ¿Quieres que lo aplique?"  
            👤 "Sí."  
            👩‍💼 *(Usa `confirmar_ahorro`)* "¡Listo! Aplicamos tu ahorro para este mes. ¡Sigue así!"  
            """
        ),
        ("placeholder", "{messages}"),
    ]
).partial()

tools = [
    guardar_meta,
    registrar_ingreso,
    confirmar_ahorro,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools)

graph = StateGraph(State)

graph.add_node("assistant", Assistant(assistant_runnable))
graph.add_node("tools", create_tool_node_with_fallback(tools))
graph.add_edge(START, "assistant")
graph.add_conditional_edges(
    "assistant",
    tools_condition,
)
graph.add_edge("tools", "assistant")


app = graph.compile(checkpointer=memory)
    

# Función para procesar mensajes
def process_message(user_id: str, mensaje: str):
    config = {"configurable": {"thread_id": user_id}}  
    state = {"messages": [HumanMessage(content=mensaje)]}
    

    #historical_data = checkpointer.load_messages(user_id)
    #historical_messages = historical_data.get("messages", []) if historical_data else []
    #print(f"📚 Historial de mensajes: {historical_messages}")
    state = {"messages": [HumanMessage(content=mensaje)]}

    response = app.invoke(state, config=config)

    return response["messages"][-1].content
    