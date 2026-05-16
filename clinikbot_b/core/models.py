from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class Paciente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes"
    )
    edad = models.IntegerField()
    sexo = models.CharField(max_length=20)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estatura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class Medicion(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="mediciones")
    bpm = models.IntegerField()
    spo2 = models.DecimalField(max_digits=5, decimal_places=2)
    temperatura = models.DecimalField(max_digits=4, decimal_places=2)
    presion_sistolica = models.IntegerField(null=True, blank=True)
    presion_diastolica = models.IntegerField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="normal")

    def __str__(self):
        return f"{self.paciente} - {self.fecha_hora}"


class Alerta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="alertas")
    medicion = models.ForeignKey(Medicion, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=100)
    mensaje = models.TextField()
    nivel = models.CharField(max_length=20, default="medio")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    atendida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tipo} - {self.paciente}"


class Cita(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aceptada", "Aceptada"),
        ("rechazada", "Rechazada"),
        ("cancelada", "Cancelada"),
        ("finalizada", "Finalizada"),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="citas")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="citas")
    fecha_hora = models.DateTimeField()
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita de {self.paciente} con {self.doctor}"


class EstudioMedico(models.Model):
    TIPOS = [
        ("pdf", "PDF"),
        ("imagen", "Imagen"),
        ("laboratorio", "Laboratorio"),
        ("radiografia", "Radiografía"),
        ("otro", "Otro"),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="estudios")
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estudios"
    )
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=30, choices=TIPOS, default="otro")
    archivo = models.FileField(upload_to="estudios/")
    descripcion = models.TextField(blank=True)
    observaciones_doctor = models.TextField(blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class MensajeChatbot(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="mensajes_chatbot")
    pregunta = models.TextField()
    respuesta = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chatbot - {self.paciente}"