# graph.py — Grafo LangGraph FIDELIO
# Principios: nodos de propósito único, routing explícito, fail-open

import os
import json as json_module
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from state import FIDELIOState, ESTADOS_VALIDOS, SIGNALS_VALIDAS
from agents import construir_prompt_fidelio, parse_response
from db import (
    cargar_lead, crear_lead, actualizar_lead, actualizar_estado,
    guardar_mensaje, cargar_historial, crear_orden,
)
from notifier import (
    send_text, send_video, send_catalogo, send_datos_pago,
    notify_camilo, notify_escalar,
)

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(
    model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
    temperature=0.3,
    timeout=30,
    model_kwargs={"response_format": {"type": "json_object"}},
)


# ── NODOS ─────────────────────────────────────────────────────────────────────

def nodo_cargar_lead(state: FIDELIOState) -> dict:
    """Carga o crea el lead en Supabase. Inyecta datos al estado."""
    phone = state["phone"]
    lead = cargar_lead(phone)

    if not lead:
        lead = crear_lead(phone)

    historial_raw = cargar_historial(lead["id"])
    messages = []
    for row in historial_raw:
        if row["role"] == "user":
            messages.append(HumanMessage(content=row["mensaje"]))
        else:
            # Wrap in JSON so the LLM sees consistent format with the system prompt
            wrapped = json_module.dumps({
                "mensaje": row["mensaje"],
                "nuevo_estado": "normal",
                "signal": "NORMAL",
                "datos_capturados": {}
            }, ensure_ascii=False)
            messages.append(AIMessage(content=wrapped))

    return {
        "lead_id": lead["id"],
        "estado_actual": lead.get("estado_actual", "esperando_reaccion_inicial"),
        "name": lead.get("name"),
        "city": lead.get("city"),
        "diseno_elegido": lead.get("diseno_elegido"),
        "metodo_pago": lead.get("metodo_pago"),
        "direccion": lead.get("direccion"),
        "celular_cliente": lead.get("celular"),
        "cedula": lead.get("cedula"),
        "messages": messages,
    }


def nodo_generar_respuesta(state: FIDELIOState) -> dict:
    """Llama al LLM con el prompt de FIDELIO y parsea el JSON de respuesta."""
    system_prompt = construir_prompt_fidelio(state)

    messages = [SystemMessage(content=system_prompt)] + state["messages"] + [
        HumanMessage(content=state["message"])
    ]

    raw = llm.invoke(messages).content
    parsed = parse_response(raw)

    signal = parsed.get("signal", "NORMAL")
    nuevo_estado = parsed.get("nuevo_estado", state["estado_actual"])

    if signal not in SIGNALS_VALIDAS:
        signal = "NORMAL"
    if nuevo_estado not in ESTADOS_VALIDOS:
        nuevo_estado = state["estado_actual"]

    return {
        "mensaje_respuesta": parsed.get("mensaje", ""),
        "signal": signal,
        "nuevo_estado": nuevo_estado,
        "datos_capturados": parsed.get("datos_capturados", {}),
        "messages": [HumanMessage(content=state["message"])],
    }


def nodo_actualizar_datos(state: FIDELIOState) -> dict:
    """Persiste datos capturados del lead en Supabase."""
    datos = state.get("datos_capturados", {})
    campos = {}

    mapping = {
        "name": "name",
        "city": "city",
        "diseno_elegido": "diseno_elegido",
        "metodo_pago": "metodo_pago",
        "direccion": "direccion",
        "celular": "celular",
        "cedula": "cedula",
    }

    for key, col in mapping.items():
        val = datos.get(key)
        if val:
            campos[col] = val

    campos["estado_actual"] = state["nuevo_estado"]
    campos["ultimo_mensaje_at"] = "now()"

    actualizar_lead(state["phone"], campos)

    # Actualizar state local también
    updates = {}
    for key, col in mapping.items():
        if datos.get(key):
            if key == "celular":
                updates["celular_cliente"] = datos[key]
            else:
                updates[key] = datos[key]

    return updates


def nodo_enviar_y_actuar(state: FIDELIOState) -> dict:
    """Envía el mensaje y ejecuta la acción según la señal."""
    phone = state["phone"]
    signal = state["signal"]
    mensaje = state["mensaje_respuesta"]

    if signal == "ENVIAR_VIDEO":
        send_video(phone)

    send_text(phone, mensaje)

    if signal == "ENVIAR_CATALOGO":
        send_catalogo(phone)

    elif signal == "ENVIAR_DATOS_PAGO":
        send_datos_pago(phone)

    elif signal == "CREAR_ORDEN":
        lead_id = state.get("lead_id", "")
        crear_orden(
            lead_id=lead_id,
            diseno=state.get("diseno_elegido") or "no especificado",
            precio=57000 if state.get("metodo_pago") == "anticipado" else 62000,
            metodo_pago=state.get("metodo_pago") or "anticipado",
            direccion=state.get("direccion") or "",
            cedula=state.get("cedula") or "",
        )
        notify_camilo(
            phone_lead=phone,
            name=state.get("name") or "",
            diseno=state.get("diseno_elegido") or "",
            metodo=state.get("metodo_pago") or "",
            direccion=state.get("direccion") or "",
            celular=state.get("celular_cliente") or "",
            cedula=state.get("cedula") or "",
        )

    elif signal == "ESCALAR_HUMANO":
        notify_escalar(phone, state.get("message", ""))
        actualizar_estado(phone, "escalado_humano")

    return {}


def nodo_guardar_salida(state: FIDELIOState) -> dict:
    """Guarda mensajes en historial de conversaciones."""
    lead_id = state.get("lead_id", "")
    estado = state["nuevo_estado"]

    guardar_mensaje(lead_id, "user", state["message"], estado)
    guardar_mensaje(
        lead_id, "assistant", state["mensaje_respuesta"],
        estado, state["signal"]
    )

    return {"messages": [AIMessage(content=state["mensaje_respuesta"])]}


# ── GRAFO ─────────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(FIDELIOState)

    graph.add_node("cargar_lead", nodo_cargar_lead)
    graph.add_node("generar_respuesta", nodo_generar_respuesta)
    graph.add_node("actualizar_datos", nodo_actualizar_datos)
    graph.add_node("enviar_y_actuar", nodo_enviar_y_actuar)
    graph.add_node("guardar_salida", nodo_guardar_salida)

    graph.add_edge(START, "cargar_lead")
    graph.add_conditional_edges(
        "cargar_lead",
        lambda s: END if s.get("estado_actual") == "pedido_confirmado" else "generar_respuesta",
        {"generar_respuesta": "generar_respuesta", END: END},
    )
    graph.add_edge("generar_respuesta", "actualizar_datos")
    graph.add_edge("actualizar_datos", "enviar_y_actuar")
    graph.add_edge("enviar_y_actuar", "guardar_salida")
    graph.add_edge("guardar_salida", END)

    return graph.compile()


fidelio_graph = build_graph()


def process_message(phone: str, message: str) -> str:
    """Entry point principal. Retorna el mensaje enviado."""
    initial_state: FIDELIOState = {
        "phone": phone,
        "message": message,
        "messages": [],
        "lead_id": None,
        "estado_actual": "esperando_reaccion_inicial",
        "name": None,
        "city": None,
        "diseno_elegido": None,
        "metodo_pago": None,
        "direccion": None,
        "celular_cliente": None,
        "cedula": None,
        "mensaje_respuesta": "",
        "nuevo_estado": "esperando_reaccion_inicial",
        "signal": "NORMAL",
        "datos_capturados": {},
    }

    result = fidelio_graph.invoke(initial_state)
    return result.get("mensaje_respuesta", "")
