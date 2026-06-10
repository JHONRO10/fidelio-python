# db.py — Operaciones Supabase para FIDELIO
# Tablas: sublime_leads, conversaciones, ordenes

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        key = (
            os.environ.get("SUPABASE_SERVICE_KEY")
            or os.environ.get("SUPABASE_KEY")
            or os.environ["SUPABASE_SERVICE_KEY"]  # raises clear error if both missing
        )
        _supabase = create_client(os.environ["SUPABASE_URL"], key)
    return _supabase


# ── LEADS ────────────────────────────────────────────────────────────────────

def cargar_lead(phone: str) -> dict | None:
    sb = get_supabase()
    res = sb.table("sublime_leads").select("*").eq("phone", phone).execute()
    return res.data[0] if res.data else None


def crear_lead(phone: str) -> dict:
    sb = get_supabase()
    res = sb.table("sublime_leads").insert({
        "phone": phone,
        "estado_actual": "esperando_reaccion_inicial",
    }).execute()
    return res.data[0]


def actualizar_lead(phone: str, campos: dict) -> None:
    sb = get_supabase()
    sb.table("sublime_leads").update(campos).eq("phone", phone).execute()


def actualizar_estado(phone: str, nuevo_estado: str) -> None:
    actualizar_lead(phone, {"estado_actual": nuevo_estado})


# ── CONVERSACIONES ────────────────────────────────────────────────────────────

def guardar_mensaje(lead_id: str, role: str, mensaje: str, estado: str, accion: str = None) -> None:
    sb = get_supabase()
    sb.table("sublime_conversaciones").insert({
        "lead_id": lead_id,
        "role": role,
        "mensaje": mensaje,
        "estado_en_momento": estado,
        "accion_ejecutada": accion,
    }).execute()


def cargar_historial(lead_id: str, limite: int = 20) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("sublime_conversaciones")
        .select("role, mensaje")
        .eq("lead_id", lead_id)
        .order("created_at", desc=False)
        .limit(limite)
        .execute()
    )
    return res.data or []


# ── ÓRDENES ───────────────────────────────────────────────────────────────────

def crear_orden(lead_id: str, diseno: str, precio: int, metodo_pago: str,
                direccion: str, cedula: str) -> dict:
    sb = get_supabase()
    res = sb.table("sublime_ordenes").insert({
        "lead_id": lead_id,
        "diseno": diseno,
        "precio": precio,
        "metodo_pago": metodo_pago,
        "direccion_entrega": direccion,
        "cedula": cedula,
        "estado_orden": "pendiente",
    }).execute()
    return res.data[0]


def actualizar_orden(lead_id: str, campos: dict) -> None:
    sb = get_supabase()
    sb.table("sublime_ordenes").update(campos).eq("lead_id", lead_id).execute()
