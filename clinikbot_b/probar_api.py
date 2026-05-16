import requests

url = "http://127.0.0.1:8000/api/recibir-signos/"

headers = {
    "X-ROBOT-TOKEN": "CLINIKBOT_ROBOT_12345"
}

datos = {
    "paciente_id": 1,
    "bpm": 78,
    "spo2": 97,
    "temperatura": 36.6,
    "presion_sistolica": 120,
    "presion_diastolica": 80
}

respuesta = requests.post(url, json=datos, headers=headers)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())