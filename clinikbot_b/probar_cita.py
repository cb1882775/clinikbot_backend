import requests

url = "http://127.0.0.1:8000/api/citas/agendar/"

datos = {
    "paciente": 1,
    "doctor": 1,
    "fecha_hora": "2026-05-15T10:30:00",
    "motivo": "Revisión de signos vitales del paciente"
}

respuesta = requests.post(url, json=datos)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())