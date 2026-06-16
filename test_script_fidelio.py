"""
Script de prueba FIDELIO — simula cliente real comprando cuelga llaves 3D
Cubre todo el flujo: primer contacto → video → catálogo → diseño → ciudad → pago → datos → comprobante
"""

import requests
import time
import json

WEBHOOK_URL = "https://fidelio-python-production.up.railway.app/webhook/fidelio_whatsapp"
# Si corre local: WEBHOOK_URL = "http://localhost:8000/webhook/fidelio_whatsapp"

PHONE_PRUEBA = "573006800524"  # Tu número — llega a tu WhatsApp

def enviar_mensaje(texto: str, turno: int):
    payload = {
        "data": {
            "key": {
                "remoteJid": f"{PHONE_PRUEBA}@s.whatsapp.net",
                "fromMe": False
            },
            "message": {
                "conversation": texto
            }
        }
    }
    print(f"\n--- T{turno} CLIENTE: {texto} ---")
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        data = resp.json()
        print(f"    FIDELIO respondió: {data.get('status', 'sin status')}")
        return data
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

def esperar(segundos: int, motivo: str):
    print(f"\n    Esperando {segundos}s - {motivo}...")
    time.sleep(segundos)

# ─── SCRIPT COMPLETO ───────────────────────────────────────────────────────

print("=" * 60)
print("FIDELIO — Script de prueba completo")
print(f"Número: {PHONE_PRUEBA}")
print(f"URL: {WEBHOOK_URL}")
print("=" * 60)

# Limpiar lead en Supabase antes de empezar (opcional — comentar si no quieres)
# Agrega DELETE FROM sublime_leads WHERE phone = '573006800524' en Supabase

# T1 — Primer contacto (FIDELIO debe enviar video inmediatamente)
enviar_mensaje("Hola me aparecio su producto en TikTok", 1)
esperar(12, "FIDELIO procesa y envía video")

# T2 — Reacción al video (FIDELIO debe enviar catálogo)
enviar_mensaje("Wow que increible! Me gusto mucho", 2)
esperar(12, "FIDELIO procesa y envía catálogo")

# T3 — Elige diseño
enviar_mensaje("El de Naruto me encanta, cuál tienen exactamente?", 3)
esperar(10, "FIDELIO confirma diseño y pide ciudad")

# T4 — Da ciudad
enviar_mensaje("Estoy en Bogotá", 4)
esperar(10, "FIDELIO confirma envío y presenta opciones de pago")

# T5 — Objeción precio
enviar_mensaje("Uy eso está un poco caro no?", 5)
esperar(10, "FIDELIO maneja objeción con anchoring")

# T6 — Elige método de pago
enviar_mensaje("Bueno me convenciste, pago anticipado", 6)
esperar(10, "FIDELIO pide los 4 datos en un solo mensaje")

# T7 — Da todos los datos
enviar_mensaje(
    "Carlos Rodríguez\nCalle 45 # 12-30 Apto 201 Bogotá\n3001234567\n1020304050",
    7
)
esperar(12, "FIDELIO envía datos de pago")

# T8 — Comprobante de pago
enviar_mensaje("Ya pagué, ahí va el pantallazo", 8)
esperar(10, "FIDELIO crea orden y cierra con redes sociales")

print("\n" + "=" * 60)
print("SCRIPT COMPLETO")
print("Revisa tu WhatsApp para ver las respuestas de FIDELIO")
print("Verifica en Supabase: tabla sublime_leads y sublime_ordenes")
print("=" * 60)
