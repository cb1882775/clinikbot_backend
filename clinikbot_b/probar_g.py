import requests

login_url = "http://127.0.0.1:8000/api/login/"
url = "http://127.0.0.1:8000/api/graficas/paciente/1/"

login_data = {
    "username": "Sadmin",
    "password": "Sadmin040404"
}

token = requests.post(login_url, json=login_data).json()["access"]

headers = {
    "Authorization": f"Bearer {token}"
}

respuesta = requests.get(url, headers=headers)

print(respuesta.status_code)
print(respuesta.json())