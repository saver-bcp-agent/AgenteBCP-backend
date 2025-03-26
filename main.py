from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import process_message
#from tools import verify_user

app = FastAPI()

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

# Correr el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)