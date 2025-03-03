from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import pymysql
from dotenv import load_dotenv
import cohere
import uuid
import json

app = FastAPI()

# Cargar variables de entorno
load_dotenv()
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
cohere_api_key = os.getenv('API_KEY')

# Configuración de Jinja2 para plantillas HTML
templates = Jinja2Templates(directory="templates")

# Conectar a la API de Cohere
co = cohere.ClientV2(cohere_api_key)

# Ruta principal (frontend)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


# **Ruta para generar preguntas de entrevista**
@app.post("/generar_preguntas/")
async def generar_preguntas(tema: str = Form(...)):
    session_id = str(uuid.uuid4())  # Genera un ID único para la sesión

    try:
        # Llamar a la API para generar preguntas
        response = co.chat(
            model="command-r-plus",
            messages=[{"role": "user", "content": f"Genera 3 preguntas de entrevista de trabajo sobre {tema}. Pon solo las preguntas sin nada más explicativo."}]
        )
        preguntas = response.message.content[0].text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando preguntas: {str(e)}")

    # Guardar en la base de datos
    try:
        db = pymysql.connect(host=host, user=username, password=password, cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()

        cursor.execute("USE db_history")

        insert_data = '''INSERT INTO interviews (session_id, tema, preguntas) VALUES (%s, %s, %s)'''
        cursor.execute(insert_data, (session_id, tema, preguntas))
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()

    return JSONResponse(content={"session_id": session_id, "preguntas": preguntas})


# **Ruta para evaluar respuestas**
@app.post("/evaluar_respuestas/")
async def evaluar_respuestas(session_id: str = Form(...), respuestas: str = Form(...)):
    print(f"Recibido session_id: {session_id}")
    print(f"Respuestas recibidas: {respuestas}")
    try:
        # Recuperar preguntas de la sesión desde la base de datos
        db = pymysql.connect(host=host, user=username, password=password, cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()
        
        cursor.execute("USE db_history")
        cursor.execute("SELECT preguntas FROM interviews WHERE session_id = %s ORDER BY id ASC LIMIT 1", (session_id))
        result = cursor.fetchone()
        result = result["preguntas"]


        if not result:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando datos: {str(e)}")


    # Evaluar respuestas con Cohere

    try:
        question= f"Un entrevistador ha realizado la siguiente pregunta: {result}. Ante esa pregunta yo he respondido esto:{respuestas}. Evaluame cómo lo he hecho, diciéndome los errores de manera breve. Gracias"
        print(question)
        # Llamar a la API para evaluar respuestas
        response = co.chat(
            model="command-r-plus",
            messages=[{"role": "user", "content": question}]
        )
        evaluaciones=response.message.content[0].text
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluando respuestas: {str(e)}")

    # Guardar en la base de datos
    try:
        db = pymysql.connect(host=host, user=username, password=password, cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()

        cursor.execute("USE db_history")

        insert_data = '''INSERT INTO evaluations (session_id, respuestas, evaluaciones) VALUES (%s, %s, %s)'''
        cursor.execute(insert_data, (session_id, respuestas, evaluaciones))
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")


    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()    

    return JSONResponse(content={"evaluaciones": evaluaciones})


# Ejecutar la aplicación
# uvicorn.run(app)
