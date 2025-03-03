import pytest
from fastapi.testclient import TestClient
from app import app  # Asegúrate de que el nombre del archivo principal sea "main.py"
import json

# Crear un cliente de prueba para la aplicación FastAPI
client = TestClient(app)

# Prueba para la ruta principal (GET /)
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

# Prueba para la ruta de generación de preguntas (POST /generar_preguntas/)
def test_generar_preguntas():
    tema = "Inteligencia Artificial"
    response = client.post("/generar_preguntas/", data={"tema": tema})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "preguntas" in data
    assert isinstance(data["preguntas"], str)

# Prueba para la ruta de evaluación de respuestas (POST /evaluar_respuestas/)
def test_evaluar_respuestas():
    # Primero, generamos preguntas para obtener un session_id válido
    tema = "Inteligencia Artificial"
    response = client.post("/generar_preguntas/", data={"tema": tema})
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # Ahora, evaluamos las respuestas
    respuestas = json.dumps({"respuesta1": "Esto es una respuesta de ejemplo."})
    response = client.post("/evaluar_respuestas/", data={"session_id": session_id, "respuestas": respuestas})
    assert response.status_code == 200
    data = response.json()
    assert "evaluaciones" in data
    assert isinstance(data["evaluaciones"], str)
