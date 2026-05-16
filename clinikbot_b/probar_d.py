import requests

login_url = "http://127.0.0.1:8000/api/login/"
registro_url = "http://127.0.0.1:8000/api/registro/doctor/"

login_data = {
    "username": "Sadmin",
    "password": "Sadmin040404"
}

login_response = requests.post(login_url, json=login_data)
token = login_response.json()["access"]

headers = {
    "Authorization": f"Bearer {token}"
}

datos = {
    "username": "doctor2",
    "password": "Doctor12345",
    "email": "doctor1@test.com",
    "nombre": "Carlos",
    "apellido": "Ramírez",
    "especialidad": "Medicina general",
    "telefono": "2411111111"
}

respuesta = requests.post(registro_url, json=datos, headers=headers)

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.json())