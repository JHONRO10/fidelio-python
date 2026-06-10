# webhook.py — FastAPI entry point para FIDELIO

import threading
from fastapi import FastAPI, Request
from graph import process_message

app = FastAPI(title="FIDELIO — Sublime Store Agent", version="1.0")

# Deduplicación: evita procesar el mismo mensaje dos veces en paralelo
_locks: dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()


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
