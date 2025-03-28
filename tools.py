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
    Analiza patrones financieros con estrategias de aceleración de ahorro.
    """
    # Simulación de ingresos base
    ingresos_base = random.randint(2000, 3500)
    egresos_base = random.randint(1500, 2500)

    def calcular_ahorro_mes(mes, porcentaje_ahorro):
        """
        Calcula el ahorro con variaciones realistas y porcentaje personalizado.
        """
        variacion_ingreso = random.uniform(0.9, 1.1)
        variacion_egreso = random.uniform(0.9, 1.1)
        
        ingreso_mes = ingresos_base * variacion_ingreso
        egreso_mes = egresos_base * variacion_egreso
        
        saldo_disponible = max(ingreso_mes - egreso_mes, 0)
        
        ahorro_mes = round(saldo_disponible * porcentaje_ahorro, 2)
        
        return {
            'ingreso': round(ingreso_mes, 2),
            'egreso': round(egreso_mes, 2),
            'ahorro': max(ahorro_mes, 0),
            'saldo_disponible': round(saldo_disponible, 2)
        }

    # Calcular planes de ahorro con diferentes porcentajes
    planes = {
        'plan_base': {
            'porcentaje': 0.05,
            'ahorros': [],
            'ingresos': [],
            'egresos': []
        },
        'plan_intermedio': {
            'porcentaje': 0.10,
            'ahorros': [],
            'ingresos': [],
            'egresos': []
        },
        'plan_agresivo': {
            'porcentaje': 0.15,
            'ahorros': [],
            'ingresos': [],
            'egresos': []
        }
    }

    # Generar planes de ahorro
    for nombre_plan, plan in planes.items():
        for i in range(6):
            detalle_mes = calcular_ahorro_mes(i+1, plan['porcentaje'])
            plan['ahorros'].append(detalle_mes['ahorro'])
            plan['ingresos'].append(detalle_mes['ingreso'])
            plan['egresos'].append(detalle_mes['egreso'])

    # Calcular detalles para cada plan
    resultados = {}
    for nombre_plan, plan in planes.items():
        ahorro_promedio = max(sum(plan['ahorros']) / len(plan['ahorros']), 0)
        meses_necesarios = round(meta / ahorro_promedio) if ahorro_promedio > 0 else "Indefinido"
        
        resultados[nombre_plan] = {
            'ahorro_promedio_mensual': round(ahorro_promedio, 2),
            'meses_necesarios': meses_necesarios,
            'plan_ahorro': [f"Mes {i+1}: {ahorro} soles" for i, ahorro in enumerate(plan['ahorros'])]
        }

    # Generar mensaje motivacional con sugerencias
    def generar_mensaje_motivacional(planes):
        base = resultados['plan_base']
        intermedio = resultados['plan_intermedio']
        agresivo = resultados['plan_agresivo']

        mensaje = f"Con tu plan actual, tardarías aproximadamente {base['meses_necesarios']} meses en alcanzar tu meta de {meta} soles.\n\n"
        
        mensaje += "🚀 Alternativas para acelerar tu ahorro:\n"
        
        if intermedio['meses_necesarios'] != "Indefinido":
            reduccion_intermedio = base['meses_necesarios'] - intermedio['meses_necesarios']
            mensaje += f"- Si ahorras un 10% de tu ingreso disponible, podrías reducir {reduccion_intermedio} meses, alcanzando tu meta en {intermedio['meses_necesarios']} meses.\n"
        
        if agresivo['meses_necesarios'] != "Indefinido":
            reduccion_agresivo = base['meses_necesarios'] - agresivo['meses_necesarios']
            mensaje += f"- Si incrementas tu ahorro al 15%, podrías reducir {reduccion_agresivo} meses, alcanzando tu meta en {agresivo['meses_necesarios']} meses.\n"
        
        mensaje += "\n💡 Recuerda: Cada sol que ahorres te acerca más a tu sueño. ¡Tú decides el ritmo!"
        
        return mensaje

    return {
        "planes": resultados,
        "mensaje_motivacional": generar_mensaje_motivacional(resultados)
    }