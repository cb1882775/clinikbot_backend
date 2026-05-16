import requests

url = "http://127.0.0.1:8000/api/chatbot/"

datos = {
    "paciente": 1,
    "pregunta": "¿Cómo tomo mis signos vitales?"
}

respuesta = requests.post(url, json=datos)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())