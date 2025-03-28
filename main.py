from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import process_message
import os
import asyncpg
#from tools import verify_user

app = FastAPI()

# Configuración de la conexión a PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL") 

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

class UserMessage(BaseModel):
    user_id: str  
    message: str  

@app.post("/chat")
async def chat_endpoint(user_message: UserMessage):
    """
    Endpoint para recibir mensajes de la app frontend y responder con IA.
    """
    user_id = user_message.user_id
    message = user_message.message

    # Verificar si el usuario tiene acceso
    #allowed = await verify_user(user_id)
    #if not allowed:
    #    raise HTTPException(status_code=403, detail="Usuario no autorizado")

    
    response = process_message(user_id, message)
    
    # Devolver la respuesta al front
    return {"user_id": user_id, "response": response}


@app.get("/ahorros/{user_id}")
async def get_ahorros(user_id: str):
    """
    Obtiene los ahorros de un usuario específico.
    """
    conn = await get_db_connection()
    try:
        query = "SELECT id, meta, total_meta, total_actual FROM ahorros WHERE usuario_id = $1"
        ahorros = await conn.fetch(query, user_id)
        
        if not ahorros:
            raise HTTPException(status_code=404, detail="No se encontraron ahorros para este usuario")

        return [
            {
                "id": row["id"],
                "meta": row["meta"],
                "total_meta": float(row["total_meta"]),
                "total_actual": float(row["total_actual"])
            }
            for row in ahorros
        ]
    finally:
        await conn.close()

# Correr el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)