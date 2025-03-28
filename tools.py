import asyncpg
import psycopg
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Dict, Any
import random

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
def guardar_meta(config: RunnableConfig, meta: str, monto: float):
    """Guarda la meta de ahorro del usuario con el monto especificado."""
    user_id = config["configurable"].get("thread_id")
    
    if not user_id:
        raise ValueError("ID de usuario no encontrado en la configuración.")

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                query = """INSERT INTO ahorros (usuario_id, meta, total_meta, total_actual)
                           VALUES (%s, %s, %s, 0) RETURNING id"""
                cursor.execute(query, (user_id, meta, monto))
                inserted_id = cursor.fetchone()[0]

            conn.commit()
        
        return f"¡Meta guardada con éxito! ID: {inserted_id}. Ahora registra tu ingreso mensual. 💰"
    
    except Exception as e:
        return f"❌ Error al guardar la meta: {str(e)}"



@tool
def registrar_ingreso(config: RunnableConfig, ingreso: float):
    """Registra el ingreso mensual del usuario y calcula un ahorro sugerido."""
    user_id = config["configurable"].get("thread_id")
    if not user_id:
        raise ValueError("ID de usuario no encontrado en la configuración.")

    #print(user_id)
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

@tool
def analizar_patrones_financieros(meta: float, meses: int) -> Dict[str, Any]:
    """
    Analiza patrones financieros con una estrategia más realista y motivadora.
    """
    # Simulación de ingresos más estables y realistas
    ingresos_base = random.randint(2000, 3500)  # Ingreso mensual base más realista
    egresos_base = random.randint(1500, 2500)   # Egresos base

    def calcular_ahorro_mes(mes):
        """
        Calcula el ahorro con variaciones más realistas.
        Introduce ligeras variaciones en ingresos y egresos.
        """
        variacion_ingreso = random.uniform(0.9, 1.1)  # ±10% de variación
        variacion_egreso = random.uniform(0.9, 1.1)   # ±10% de variación
        
        ingreso_mes = ingresos_base * variacion_ingreso
        egreso_mes = egresos_base * variacion_egreso
        
        saldo_disponible = max(ingreso_mes - egreso_mes, 0)
        
        # Estrategias de ahorro progresivas
        if saldo_disponible <= 500:
            porcentaje_ahorro = 0.03  # Ahorro mínimo conservador
        elif saldo_disponible <= 1000:
            porcentaje_ahorro = 0.06  # Ahorro moderado
        else:
            porcentaje_ahorro = 0.10  # Ahorro más agresivo
        
        ahorro_mes = round(saldo_disponible * porcentaje_ahorro, 2)
        
        return {
            'ingreso': round(ingreso_mes, 2),
            'egreso': round(egreso_mes, 2),
            'ahorro': max(ahorro_mes, 0),  # Nunca menor a cero
            'saldo_disponible': round(saldo_disponible, 2)
        }

    # Generar plan de ahorro
    plan_ahorro = []
    ahorros_mensuales = []
    ingresos_detalle = []
    egresos_detalle = []

    for i in range(6):
        detalle_mes = calcular_ahorro_mes(i+1)
        plan_ahorro.append(f"Mes {i+1}: {detalle_mes['ahorro']} soles")
        ahorros_mensuales.append(detalle_mes['ahorro'])
        ingresos_detalle.append(detalle_mes['ingreso'])
        egresos_detalle.append(detalle_mes['egreso'])

    # Cálculos finales
    ahorro_promedio = max(sum(ahorros_mensuales) / len(ahorros_mensuales), 0)
    meses_necesarios = round(meta / ahorro_promedio) if ahorro_promedio > 0 else "Indefinido"

    # Mensaje motivacional adaptativo
    if ahorro_promedio == 0:
        mensaje_motivacional = "Parece que necesitamos revisar tu presupuesto. ¡Juntas podemos encontrar formas de ahorrar!"
    elif meses_necesarios <= 24:
        mensaje_motivacional = f"¡Excelente! Con este plan, podrías alcanzar tu meta de {meta} soles en aproximadamente {meses_necesarios} meses. ¡Sigue así!"
    elif meses_necesarios <= 36:
        mensaje_motivacional = f"Tu meta está a {meses_necesarios} meses. Recuerda, cada sol ahorrado te acerca más a tu sueño del carro. ¡Tú puedes lograrlo!"
    else:
        mensaje_motivacional = f"El camino es largo, pero no imposible. En aproximadamente {meses_necesarios} meses podrías alcanzar tu meta. ¡La constancia es clave!"

    return {
        "ingresos": ingresos_detalle,
        "egresos": egresos_detalle,
        "plan_ahorro": plan_ahorro,
        "ahorro_promedio_mensual": round(ahorro_promedio, 2),
        "meses_necesarios": meses_necesarios,
        "mensaje": mensaje_motivacional
    }
