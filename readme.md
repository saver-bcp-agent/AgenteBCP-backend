# Chatbot de Microahorro 📊🤖  

Este es un MVP básico de un chatbot desarrollado con **Langraph** y **Python**, diseñado para ayudar a personas con ingresos irregulares a configurar un **microahorro automático**.  

---

## 🚀 Instalación  

### 1️⃣ Clonar el repositorio  


### 2️⃣ Instalar requerimientos  
```bash
pip install -r requirements.txt
```

### 4️⃣ Agregar archivo `.env`  
Crea un archivo **`.env`** en la raíz del proyecto con las siguientes variables:  

```env
DATABASE_URL=postgresql://postgres:CONTRASENIA@localhost:5432/DATABASENAME
OPENAI_API_KEY=TU_CLAVE_DE_OPENAI
```

🔹 **Reemplaza `CONTRASENIA` y `DATABASENAME` con los valores de tu base de datos.**  
🔹 **Para obtener una API key de OpenAI, regístrate en [OpenAI](https://platform.openai.com/signup/).**  

---

## 🏗️ Uso  

### Ejecutar el test, chatbot por consola.
```bash
python test.py
```
### Ejecutar main.py
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```



---

## 🛠️ Tecnologías  
- **Python** 🐍  
- **Langraph** 🧠  
- **PostgreSQL** 🗄️  
- **FastAPI** 🚀  

---
