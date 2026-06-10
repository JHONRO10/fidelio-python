# state.py — FIDELIOState
# Principio LangGraph: estado raw (datos puros, no prompts formateados)

from typing import Annotated, Optional
from typing_extensions import TypedDict
import operator


class FIDELIOState(TypedDict):
    # Identificación
    phone: str
    lead_id: Optional[str]

    # Mensaje entrante
    message: str

    # Historial de conversación para el LLM (append-mode)
    messages: Annotated[list, operator.add]

    # Estado comercial del lead
    estado_actual: str

    # Datos del cliente (se llenan progresivamente)
    name: Optional[str]
    city: Optional[str]
    diseno_elegido: Optional[str]
    metodo_pago: Optional[str]
    direccion: Optional[str]
    celular_cliente: Optional[str]
    cedula: Optional[str]

    # Output del LLM parseado
    mensaje_respuesta: str
    nuevo_estado: str
    signal: str           # NORMAL | ENVIAR_CATALOGO | ENVIAR_DATOS_PAGO | REGISTRAR_PAGO | CREAR_ORDEN | ESCALAR_HUMANO
    datos_capturados: dict


ESTADO_INICIAL = "esperando_reaccion_inicial"

ESTADOS_VALIDOS = {
    "esperando_reaccion_inicial",
    "video_enviado",
    "catalogo_enviado",
    "esperando_eleccion_diseno",
    "diseno_elegido",
    "metodo_pago_presentado",
    "recolectando_datos",
    "esperando_comprobante",
    "pedido_confirmado",
    "escalado_humano",
}

SIGNALS_VALIDAS = {
    "NORMAL",
    "ENVIAR_VIDEO",
    "ENVIAR_CATALOGO",
    "ENVIAR_DATOS_PAGO",
    "REGISTRAR_PAGO",
    "CREAR_ORDEN",
    "ESCALAR_HUMANO",
}
