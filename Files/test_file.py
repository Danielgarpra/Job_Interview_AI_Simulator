import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_root():
    """Verifica que el endpoint raíz responde correctamente."""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200, f"Error: {response.status_code} - {response.text}"


def test_generar_preguntas():
    """Verifica que se generan preguntas y se obtiene un session_id."""
    global session_id  # Variable global para compartir session_id
    data = {"tema": "Inteligencia Artificial"}

    response = requests.post(f"{BASE_URL}/generar_preguntas/", data=data)
    assert response.status_code == 200, f"Error: {response.status_code} - {response.text}"

    json_data = response.json()
    session_id = json_data.get("session_id")
    assert session_id, "session_id no fue retornado por la API"

def test_evaluar_respuestas():
    """Verifica que se evalúan respuestas correctamente."""
    global session_id
    assert session_id, "session_id no está definido"

    data = {
        "session_id": session_id,
        "respuestas": "No sé ninguna respuesta"
    }

    response = requests.post(f"{BASE_URL}/evaluar_respuestas/", data=data)
    assert response.status_code == 200, f"Error: {response.status_code} - {response.text}"

    json_data = response.json()
    assert "evaluaciones" in json_data, "El campo 'evaluaciones' no fue retornado"

