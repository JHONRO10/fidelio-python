# notifier.py — Evolution API para FIDELIO / Sublime Store

import os
import requests
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_URL = os.environ.get("EVOLUTION_API_URL", "")
EVOLUTION_KEY = os.environ.get("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "")

CATALOGO_PDF_URL = os.environ.get("CATALOGO_PDF_URL", "")  # URL pública del PDF en Drive o Supabase
CAMILO_PHONE = os.environ.get("CAMILO_PHONE", "573164721093")

DATOS_PAGO = (
    "💳 *Datos para tu pago de $65.000:*\n\n"
    "🔵 Nequi / Daviplata: 3164721093\n"
    "🔵 Bancolombia ahorros: 04528543397\n"
    "   (Dados Productora Gráfica y Digital SAS)\n"
    "🔵 PSE / Tarjeta: https://checkout.bold.co/payment/LNK_9A4GRYI5DQ\n\n"
    "Cuando hagas el pago, envíame el pantallazo 📸"
)


def _headers() -> dict:
    return {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}


def _base_url() -> str:
    return f"{EVOLUTION_URL}/message"


def send_text(phone: str, text: str) -> bool:
    try:
        res = requests.post(
            f"{_base_url()}/sendText/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={"number": phone, "text": text},
            timeout=10,
        )
        return res.status_code == 201
    except Exception as e:
        print(f"[notifier] send_text error: {e}")
        return False


def send_document(phone: str, url: str, caption: str = "") -> bool:
    """Envía un PDF (catálogo) vía URL pública."""
    try:
        res = requests.post(
            f"{_base_url()}/sendMedia/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={
                "number": phone,
                "mediatype": "document",
                "mimetype": "application/pdf",
                "media": url,
                "caption": caption,
                "fileName": "Catalogo_Sublime_Store.pdf",
            },
            timeout=15,
        )
        return res.status_code == 201
    except Exception as e:
        print(f"[notifier] send_document error: {e}")
        return False


def send_catalogo(phone: str) -> bool:
    return send_document(
        phone,
        CATALOGO_PDF_URL,
        "📚 Catálogo completo Sublime Store 2025",
    )


def send_datos_pago(phone: str) -> bool:
    return send_text(phone, DATOS_PAGO)


def notify_camilo(phone_lead: str, name: str, diseno: str, metodo: str) -> bool:
    """Notifica a Camilo cuando se confirma un pedido."""
    msg = (
        f"🛒 *NUEVO PEDIDO CONFIRMADO*\n\n"
        f"📱 WhatsApp: {phone_lead}\n"
        f"👤 Cliente: {name or 'Sin nombre'}\n"
        f"🎨 Diseño: {diseno or 'No especificado'}\n"
        f"💳 Pago: {metodo or 'No especificado'}\n\n"
        f"Revisar en Supabase para guía de envío."
    )
    return send_text(CAMILO_PHONE, msg)


def notify_escalar(phone_lead: str, ultimo_mensaje: str) -> bool:
    """Escala conversación a Camilo."""
    msg = (
        f"⚠️ *ATENCIÓN REQUERIDA*\n\n"
        f"📱 Cliente: {phone_lead}\n"
        f"💬 Último mensaje: {ultimo_mensaje[:200]}\n\n"
        f"El cliente necesita atención humana."
    )
    return send_text(CAMILO_PHONE, msg)
