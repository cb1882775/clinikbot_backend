import requests

login_url = "http://127.0.0.1:8000/api/login/"
historial_url = "http://127.0.0.1:8000/api/historial/1/"

login_data = {
    "username": "Carlos040404",
    "password": "C12345678"
}

login_response = requests.post(login_url, json=login_data)
token = login_response.json()["access"]

headers = {
    "Authorization": f"Bearer {token}"
}

respuesta = requests.get(historial_url, headers=headers)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())