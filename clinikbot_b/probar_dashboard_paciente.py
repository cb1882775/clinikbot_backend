import requests

login_url = "http://127.0.0.1:8000/api/login/"
dashboard_url = "http://127.0.0.1:8000/api/dashboard/paciente/"

login_data = {
    "username": "paciente1",
    "password": "Paciente12345"
}

login_response = requests.post(login_url, json=login_data)
token = login_response.json()["access"]

headers = {
    "Authorization": f"Bearer {token}"
}

respuesta = requests.get(dashboard_url, headers=headers)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())