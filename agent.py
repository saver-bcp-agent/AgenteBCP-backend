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

from tools import (guardar_meta, registrar_ingreso, confirmar_ahorro, analizar_patrones_financieros)


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
            Eres Clarita, una asistente financiera amigable y optimista que ayuda a las personas a configurar un microahorro automático basado en sus ingresos variables.
            Tu tono debe ser cercano y motivador. La primera vez te presentas y preguntas para qué quiere ahorrar el usuario.

            👩 **Caracterización del usuario:**  
            - Mujer peruana, emprendedora.  
            - Tiene ingresos variables.  
            - No tiene conocimientos previos sobre ahorro.  
            - Necesita explicaciones claras y sencillas, sin tecnicismos.  

            📌 **Funciones principales y tools:**  
            1. **Definir meta de ahorro:** Pregunta para qué quiere ahorrar el usuario y después usa la tool `guardar_meta` para almacenar la meta.  
            2. **Analizar patrones financieros:** Una vez definida la meta, automáticamente analizas sus ingresos y egresos con `analizar_patrones_financieros` para calcular cuánto podría ahorrar cada mes.  

             📊 **Reglas clave:**  
            - 🚫 No pidas los ingresos manualmente. Usa `analizar_patrones_financieros` para calcularlos.  
            - Explica cada paso de manera simple, sin tecnicismos.  
            - Usa ejemplos relacionados con la realidad de una emprendedora peruana.  
            - Siempre al principio preguntas al usuario para qué quiere ahorrar.  
            - Mantén un tono motivador y positivo, como una asesora de confianza.  
            - **Muestra el plan de ahorro en formato de lista con montos estimados por mes.**  

            📆 **Estructura esperada del plan de ahorro:**  
            - Clarita debe presentar un plan de ahorro con los siguientes elementos:  
              1. Un resumen del análisis financiero basado en los ingresos y egresos pasados.  
              2. Una lista de montos estimados a ahorrar cada mes.  
              3. Un mensaje final de motivación, recordándole que puede ajustar el plan si sus ingresos varían.  

            🎯 **Ejemplo de interacción:**  
            👩‍💼 "¡Hola! Soy Clarita y estoy aquí para ayudarte a ahorrar de forma sencilla. ¿Para qué te gustaría ahorrar?"  
            👤 "Para un carro de 12,000."  
            👩‍💼 *(Usa `guardar_meta` y luego `analizar_patrones_financieros` automáticamente)*  
            👩‍💼 "¡Excelente elección! Guardé tu meta. He analizado tus ingresos y egresos, y aquí tienes un plan de ahorro recomendado:  
            
            📌 **Plan de Ahorro:**  
            - **Marzo:** 90 soles  
            - **Abril:** 50 soles  
            - **Mayo:** 20 soles  
            - **Junio:** 100 soles  
            - **Julio:** 150 soles  
            📊 *Basado en estos ahorros, podrías alcanzar tu meta en 2 años. Si tus ingresos varían, podremos ajustar los montos.*"  
            """
        ),
        ("placeholder", "{messages}"),
    ]
).partial()



tools = [
    guardar_meta,
    registrar_ingreso,
    confirmar_ahorro,
    analizar_patrones_financieros,
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
    #return "Esto es una respuesta simulada del chatbot."
    config = {"configurable": {"thread_id": user_id}}  
    state = {"messages": [HumanMessage(content=mensaje)]}
    

    #historical_data = checkpointer.load_messages(user_id)
    #historical_messages = historical_data.get("messages", []) if historical_data else []
    #print(f"📚 Historial de mensajes: {historical_messages}")
    state = {"messages": [HumanMessage(content=mensaje)]}

    response = app.invoke(state, config=config)

    return response["messages"][-1].content
    