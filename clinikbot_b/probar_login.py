import requests

url = "http://127.0.0.1:8000/api/login/"

datos = {
    "username": "Carlos040404",
    "password": "C12345678"
}

respuesta = requests.post(url, json=datos)

print(respuesta.status_code)
print(respuesta.json())