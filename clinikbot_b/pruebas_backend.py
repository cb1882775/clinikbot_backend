import requests

BASE_URL = "http://127.0.0.1:8000/api"

ADMIN_USER = "Sadmin"
ADMIN_PASS = "Sadmin040404"

ROBOT_TOKEN = "CLINIKBOT_ROBOT_12345"


def login(username, password):
    r = requests.post(f"{BASE_URL}/login/", json={
        "username": username,
        "password": password
    })
    print("LOGIN:", r.status_code)
    print(r.json())
    return r.json().get("access")


def probar_dashboard_admin(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/dashboard/admin/", headers=headers)
    print("DASHBOARD ADMIN:", r.status_code)
    print(r.json())


def probar_recibir_signos():
    headers = {"X-ROBOT-TOKEN": ROBOT_TOKEN}

    datos = {
        "paciente_id": 1,
        "bpm": 80,
        "spo2": 97,
        "temperatura": 36.7,
        "presion_sistolica": 120,
        "presion_diastolica": 80
    }

    r = requests.post(f"{BASE_URL}/recibir-signos/", json=datos, headers=headers)
    print("RECIBIR SIGNOS:", r.status_code)
    print(r.json())


def probar_historial(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/historial/1/", headers=headers)
    print("HISTORIAL:", r.status_code)
    print(r.json())


def probar_alertas(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/alertas/1/", headers=headers)
    print("ALERTAS:", r.status_code)
    print(r.json())


if __name__ == "__main__":
    token_admin = login(ADMIN_USER, ADMIN_PASS)

    if token_admin:
        probar_dashboard_admin(token_admin)
        probar_recibir_signos()
        probar_historial(token_admin)
        probar_alertas(token_admin)