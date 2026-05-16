from django.contrib import admin
from .models import Doctor, Paciente, Medicion, Alerta, Cita, EstudioMedico, MensajeChatbot


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "especialidad", "telefono")


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "edad", "sexo", "doctor", "telefono")


@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "bpm",
        "spo2",
        "temperatura",
        "presion_sistolica",
        "presion_diastolica",
        "estado",
        "fecha_hora",
    )


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "tipo", "nivel", "atendida", "fecha_hora")
    list_filter = ("nivel", "atendida")


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "doctor", "fecha_hora", "estado")
    list_filter = ("estado", "fecha_hora")


@admin.register(EstudioMedico)
class EstudioMedicoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "paciente", "doctor", "tipo", "fecha_subida")
    list_filter = ("tipo", "fecha_subida")


@admin.register(MensajeChatbot)
class MensajeChatbotAdmin(admin.ModelAdmin):
    list_display = ("paciente", "pregunta", "fecha_hora")