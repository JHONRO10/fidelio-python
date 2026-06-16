# notifier.py — Evolution API para FIDELIO / Sublime Store

import os
import requests
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_URL = os.environ.get("EVOLUTION_API_URL", "")
EVOLUTION_KEY = os.environ.get("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "").strip()
print(f"[notifier] EVOLUTION_INSTANCE={EVOLUTION_INSTANCE!r} EVOLUTION_URL={EVOLUTION_URL!r}")

CATALOGO_PDF_URL = os.environ.get("CATALOGO_PDF_URL", "")
VIDEO_PRODUCTO_URL = os.environ.get("VIDEO_PRODUCTO_URL", "")
CAMILO_PHONE = os.environ.get("CAMILO_PHONE", "573164721093")
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")          # número del supervisor (Jhon)
NOTIFY_INSTANCE = os.environ.get("NOTIFY_INSTANCE", "Aria")  # instancia que notifica al supervisor

DATOS_PAGO = (
    "💳 *Datos para tu pago de $57.000:*\n\n"
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
        print(f"[send_text] phone={phone} status={res.status_code} resp={res.text[:120]}")
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


def send_video(phone: str) -> bool:
    """Envía el video del producto."""
    try:
        res = requests.post(
            f"{_base_url()}/sendMedia/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={
                "number": phone,
                "mediatype": "video",
                "mimetype": "video/mp4",
                "media": VIDEO_PRODUCTO_URL,
                "caption": "🎮 Mira cómo quedan los cuelga llaves Sublime Store 🔥",
            },
            timeout=20,
        )
        print(f"[send_video] status={res.status_code} url={VIDEO_PRODUCTO_URL[:60]} resp={res.text[:200]}")
        return res.status_code == 201
    except Exception as e:
        print(f"[notifier] send_video error: {e}")
        return False


def send_catalogo(phone: str) -> bool:
    return send_document(
        phone,
        CATALOGO_PDF_URL,
        "📚 Catálogo completo Sublime Store — elige tu diseño favorito",
    )


def send_datos_pago(phone: str) -> bool:
    return send_text(phone, DATOS_PAGO)


def _send_via(instance: str, phone: str, text: str) -> bool:
    """Envía texto usando una instancia Evolution específica."""
    try:
        res = requests.post(
            f"{EVOLUTION_URL}/message/sendText/{instance}",
            headers={"apikey": EVOLUTION_KEY, "Content-Type": "application/json"},
            json={"number": phone, "text": text},
            timeout=10,
        )
        return res.status_code == 201
    except Exception as e:
        print(f"[notifier] _send_via({instance}) error: {e}")
        return False


def notify_camilo(
    phone_lead: str, name: str, diseno: str, metodo: str,
    direccion: str = "", celular: str = "", cedula: str = "",
) -> bool:
    """Notifica a Camilo (via SublimeStore) y al supervisor Jhon (via NOTIFY_INSTANCE)."""
    msg = (
        f"🛒 *NUEVO PEDIDO CONFIRMADO*\n\n"
        f"📱 WhatsApp: {phone_lead}\n"
        f"👤 Cliente: {name or 'Sin nombre'}\n"
        f"🎨 Diseño: {diseno or 'No especificado'}\n"
        f"💳 Pago: {metodo or 'No especificado'}\n"
        f"📍 Dirección: {direccion or 'No indicada'}\n"
        f"📞 Celular: {celular or 'No indicado'}\n"
        f"🪪 Cédula: {cedula or 'No indicada'}\n\n"
        f"Pedido listo para procesar envío."
    )
    # Notifica a Camilo (desde la instancia del bot)
    ok1 = send_text(CAMILO_PHONE, msg)
    # Notifica al supervisor/dueño (desde instancia Aria, para que le llegue al número de Jhon)
    ok2 = True
    if OWNER_PHONE and OWNER_PHONE != EVOLUTION_INSTANCE:
        ok2 = _send_via(NOTIFY_INSTANCE, OWNER_PHONE, msg)
    return ok1 and ok2


def notify_escalar(phone_lead: str, ultimo_mensaje: str) -> bool:
    """Escala conversación — notifica a Camilo y al supervisor."""
    msg = (
        f"⚠️ *ATENCIÓN REQUERIDA*\n\n"
        f"📱 Cliente: {phone_lead}\n"
        f"💬 Último mensaje: {ultimo_mensaje[:200]}\n\n"
        f"El cliente necesita atención humana."
    )
    ok1 = send_text(CAMILO_PHONE, msg)
    ok2 = True
    if OWNER_PHONE and OWNER_PHONE != EVOLUTION_INSTANCE:
        ok2 = _send_via(NOTIFY_INSTANCE, OWNER_PHONE, msg)
    return ok1 and ok2
