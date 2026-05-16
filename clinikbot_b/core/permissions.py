def es_administrador(user):
    return user.is_superuser or user.groups.filter(name="Administrador").exists()


def es_doctor(user):
    return user.groups.filter(name="Doctor").exists()


def es_paciente(user):
    return user.groups.filter(name="Paciente").exists()