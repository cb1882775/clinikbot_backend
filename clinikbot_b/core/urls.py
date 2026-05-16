

from django.urls import path
from . import views

urlpatterns = [
    path("recibir-signos/", views.recibir_signos, name="recibir_signos"),
    path("historial/<int:paciente_id>/", views.historial_paciente, name="historial_paciente"),
    path("alertas/<int:paciente_id>/", views.alertas_paciente, name="alertas_paciente"),

    path("citas/agendar/", views.agendar_cita, name="agendar_cita"),
    path("citas/paciente/<int:paciente_id>/", views.citas_paciente, name="citas_paciente"),
    path("citas/doctor/<int:doctor_id>/", views.citas_doctor, name="citas_doctor"),

    path("estudios/subir/", views.subir_estudio, name="subir_estudio"),
    path("estudios/paciente/<int:paciente_id>/", views.estudios_paciente, name="estudios_paciente"),

    path("chatbot/", views.chatbot_responder, name="chatbot_responder"),
    path("chatbot/historial/<int:paciente_id>/", views.historial_chatbot, name="historial_chatbot"),

    path("perfil/", views.perfil_usuario, name="perfil_usuario"),

    path("registro/paciente/", views.registrar_paciente, name="registrar_paciente"),
    path("registro/doctor/", views.registrar_doctor, name="registrar_doctor"),

    path("dashboard/paciente/", views.dashboard_paciente, name="dashboard_paciente"),
    path("dashboard/doctor/", views.dashboard_doctor, name="dashboard_doctor"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),

    path("citas/<int:cita_id>/estado/", views.actualizar_estado_cita, name="actualizar_estado_cita"),
    path("alertas/<int:alerta_id>/atender/", views.atender_alerta, name="atender_alerta"),
    path("pacientes/<int:paciente_id>/asignar-doctor/", views.asignar_doctor_paciente, name="asignar_doctor_paciente"),

    path("pacientes/", views.listar_pacientes, name="listar_pacientes"),
    path("doctores/", views.listar_doctores, name="listar_doctores"),

    path("graficas/paciente/<int:paciente_id>/", views.graficas_paciente, name="graficas_paciente"),

    path("estudios/<int:estudio_id>/observacion/", views.agregar_observacion_estudio, name="agregar_observacion_estudio"),

    path("reporte/paciente/<int:paciente_id>/", views.reporte_paciente, name="reporte_paciente"),

    path("historial/<int:paciente_id>/fechas/", views.historial_por_fechas, name="historial_por_fechas"),

    path("doctores/disponibles/", views.doctores_disponibles, name="doctores_disponibles"),
]