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

# Load environment variables
load_dotenv()
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
cohere_api_key = os.getenv('API_KEY')

# Configuration for Jinja2 templates (HTML)
templates = Jinja2Templates(directory="templates")

# Connect to Cohere API
co = cohere.ClientV2(cohere_api_key)

# Main route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


# Route to generate questions
@app.post("/generar_preguntas/")
async def generar_preguntas(tema: str = Form(...)):
    session_id = str(uuid.uuid4())  # Generate a unique session ID

    try:
        # Call the API to generate questions
        response = co.chat(
            model="command-r-plus",
            messages=[{"role": "user", "content": f"Genera 3 preguntas de entrevista de trabajo sobre {tema}. Pon solo las preguntas sin nada más explicativo."}]
        )
        preguntas = response.message.content[0].text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando preguntas: {str(e)}")

    # Save in the database
    try:
        db = pymysql.connect(host=host, user=username, password=password, cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()

        cursor.execute("USE db_history")

        insert_data = '''INSERT INTO interviews (session_id, tema, preguntas) VALUES (%s, %s, %s)'''
        cursor.execute(insert_data, (session_id, tema, preguntas))
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")

    # Close the database connection
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()

    return JSONResponse(content={"session_id": session_id, "preguntas": preguntas})


# Route to evaluate answers
@app.post("/evaluar_respuestas/")
async def evaluar_respuestas(session_id: str = Form(...), respuestas: str = Form(...)):

    try:
        # Restore the questions from the database from the same session
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


    # Evaluate the answers with Cohere

    try:
        question= f"Un entrevistador ha realizado las siguientes preguntas: {result}. Ante esa pregunta yo he respondido esto:{respuestas}. Evaluame cómo lo he hecho, diciéndome los errores de manera breve como si hubieras sido tú el entrevistador. Empieza directamente respondiéndome, sin comentar antes nada. Respóndeme con un texto de manera estructurada. Acaba la evaluación con una frase motivadora."
        
        # Call the API to evaluate the answers
        response = co.chat(
            model="command-r-plus",
            messages=[{"role": "user", "content": question}]
        )
        evaluaciones=response.message.content[0].text
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluando respuestas: {str(e)}")

    # Save the evaluation in the database
    try:
        db = pymysql.connect(host=host, user=username, password=password, cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()

        cursor.execute("USE db_history")

        insert_data = '''INSERT INTO evaluations (session_id, respuestas, evaluaciones) VALUES (%s, %s, %s)'''
        cursor.execute(insert_data, (session_id, respuestas, evaluaciones))
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")

    # Close the database connection
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()    

    return JSONResponse(content={"evaluaciones": evaluaciones})


# To execute the app if we run it in local
uvicorn.run(app)
# After decomment e should run the app with the following command: python app.py
