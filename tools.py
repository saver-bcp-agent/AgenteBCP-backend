import asyncpg
import psycopg
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  
INSTANCE_NAME = os.getenv("INSTANCE_NAME")

########################### Functions ###########################

async def verify_user(phone: str):
    #funcion para verificar si el usuario está activo en la base de datos
    """conn = await asyncpg.connect(DATABASE_URL)
    query = "SELECT estado FROM paciente WHERE celular = $1"
    result = await conn.fetchval(query, phone)
    await conn.close()
    if result is None:
        return False
    """
    return True 


########################### Tools ###########################

@tool
def guardar_meta(config: RunnableConfig, meta: str):
    """Guarda la meta de ahorro del usuario."""
    user_id = config["configurable"].get("thread_id")
    print(user_id)
    print(meta)
    if not user_id:
        raise ValueError("ID de usuario no encontrado en la configuración.")

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        query = """INSERT INTO ahorros (usuario_id, meta, ingreso_mensual, ahorro_sugerido, ahorro_confirmado)
                   VALUES (%s, %s, 0, 0, 0)"""
        cursor.execute(query, (user_id, meta))
        inserted_id = cursor.fetchone()[0]
    print('insertar:',inserted_id)
    print('cursor:',cursor)
    conn.commit()
    conn.close()
    if inserted_id:
        return "¡Meta guardada! Ahora registra tu ingreso mensual. 💰"
    return "No se pudo guardar tu meta. Problemas técnicos."



@tool
def registrar_ingreso(config: RunnableConfig, ingreso: float):
    """Registra el ingreso mensual del usuario y calcula un ahorro sugerido."""
    user_id = config["configurable"].get("thread_id")
    if not user_id:
        raise ValueError("ID de usuario no encontrado en la configuración.")

    print(user_id)
    # Regla simple: ahorrar el 5% del ingreso como sugerencia
    ahorro_sugerido = round(ingreso * 0.05, 2)

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        query = """UPDATE ahorros 
                   SET ingreso_mensual = %s, ahorro_sugerido = %s, fecha = %s 
                   WHERE usuario_id = %s 
                   ORDER BY fecha DESC LIMIT 1"""
        cursor.execute(query, (ingreso, ahorro_sugerido, datetime.now(), user_id))

    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return "Se registró tu ingreso y se calculó un ahorro sugerido. ¿Quieres confirmar tu ahorro?"
    return "No se pudo registrar tu ingreso. Problemas técnicos"

@tool
def confirmar_ahorro(config: RunnableConfig):
    """Confirma el ahorro del usuario para el mes actual."""
    user_id = config["configurable"].get("thread_id")
    if not user_id:
        raise ValueError("ID de usuario no encontrado en la configuración.")

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        # Obtener el último ahorro sugerido
        query_select = """SELECT ahorro_sugerido FROM ahorros 
                          WHERE usuario_id = %s 
                          ORDER BY fecha DESC 
                          LIMIT 1"""
        cursor.execute(query_select, (user_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return "No encontré un ahorro sugerido para confirmar. Registra tu ingreso primero. 📊"

        ahorro_confirmado = result[0]

        # Confirmar el ahorro
        query_update = """UPDATE ahorros 
                          SET ahorro_confirmado = ahorro_sugerido 
                          WHERE usuario_id = %s 
                          ORDER BY fecha DESC LIMIT 1"""
        cursor.execute(query_update, (user_id,))

    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return f"¡Ahorro confirmado! Este mes apartaste S/.{ahorro_confirmado} para tu meta. ¡Sigue así! 🚀"
    return "No se pudo registrar tu ahorro. Problemas técnicos"

