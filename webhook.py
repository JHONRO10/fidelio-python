# webhook.py — FastAPI entry point para FIDELIO

import threading
import unicodedata
from fastapi import FastAPI, Request
from graph import process_message
from db import cargar_lead

app = FastAPI(title="FIDELIO — Sublime Store Agent", version="1.0")

# Deduplicación: evita procesar el mismo mensaje dos veces en paralelo
_locks: dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()

# PAUTA GATE — solo leads nuevos necesitan la frase del anuncio Meta Ads
# Cada sublist = conjunto AND (todas las palabras deben estar presentes)
# Entre sublists = OR (basta con que una pase)
_PAUTA_SETS = [
    ["instagram", "interesa"],   # "Los vi en Instagram y me interesa su producto"
    ["cuelga llaves"],            # "me interesa su producto de cuelga llaves"
]


def _normalizar(texto: str) -> str:
    """Minúsculas sin tildes."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


def _pasa_pauta_gate(phone: str, texto: str) -> bool:
    """
    Retorna True si el mensaje puede ser procesado por FIDELIO.
    Leads existentes (con historial en Supabase) pasan siempre.
    Leads nuevos solo pasan si el texto contiene las palabras clave del anuncio.
    """
    try:
        lead = cargar_lead(phone)
        if lead:
            return True  # lead con historial → siempre pasa
    except Exception as e:
        print(f"[pauta_gate] error consultando lead {phone}: {e}")
        return True  # fail-open: si hay error en DB, no bloqueamos

    texto_norm = _normalizar(texto)
    for keyword_set in _PAUTA_SETS:
        if all(kw in texto_norm for kw in keyword_set):
            return True  # encontró un conjunto válido

    print(f"[pauta_gate] BLOQUEADO {phone} — mensaje: {texto[:80]}")
    return False


def _get_lock(phone: str) -> threading.Lock:
    with _locks_mutex:
        if phone not in _locks:
            _locks[phone] = threading.Lock()
        return _locks[phone]


@app.get("/")
def health():
    return {"status": "FIDELIO activo", "version": "1.0"}


@app.post("/webhook/fidelio_whatsapp")
async def webhook(request: Request):
    try:
        body = await request.json()
        data = body.get("data", {})
        key = data.get("key", {})

        from_me = key.get("fromMe", False)
        remote_jid = key.get("remoteJid", "")
        message_obj = data.get("message", {})
        msg_keys = list(message_obj.keys()) if message_obj else []
        print(f"[webhook] jid={remote_jid} fromMe={from_me} msg_keys={msg_keys}")

        if from_me:
            return {"status": "ignored"}

        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

        if not phone:
            return {"status": "no_phone"}

        text = (
            message_obj.get("conversation")
            or message_obj.get("extendedTextMessage", {}).get("text")
            or ""
        ).strip()

        if not text:
            print(f"[webhook] no_text para {phone} — msg_keys={msg_keys}")
            return {"status": "no_text"}

        # PAUTA GATE — filtro antes de procesar
        if not _pasa_pauta_gate(phone, text):
            return {"status": "blocked_pauta_gate"}

        lock = _get_lock(phone)
        if not lock.acquire(blocking=False):
            return {"status": "processing"}

        try:
            process_message(phone, text)
        finally:
            lock.release()

        return {"status": "ok"}

    except Exception as e:
        print(f"[webhook] error: {e}")
        return {"status": "error", "detail": str(e)}
