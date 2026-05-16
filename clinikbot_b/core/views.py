
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_date

from django.conf import settings

from .models import Paciente, Medicion, Alerta, Cita, EstudioMedico, MensajeChatbot, Paciente, Doctor

from .serializers import (
    MedicionSerializer,
    HistorialMedicionSerializer,
    AlertaSerializer,
    CitaSerializer,
    EstudioMedicoSerializer,
    MensajeChatbotSerializer,
    RegistroPacienteSerializer,
    RegistroDoctorSerializer,
    PacienteSerializer,
    DoctorSerializer
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .permissions import es_administrador, es_doctor, es_paciente


def evaluar_alertas(paciente, medicion):
    alertas = []
    estado = "normal"

    if medicion.bpm < 60:
        alertas.append(("Ritmo cardíaco bajo", "BPM menor a 60", "medio"))
        estado = "alerta"

    if medicion.bpm > 100:
        alertas.append(("Ritmo cardíaco alto", "BPM mayor a 100", "medio"))
        estado = "alerta"

    if medicion.spo2 < 92:
        alertas.append(("Oxigenación baja", "SpO₂ menor a 92%", "alto"))
        estado = "alerta"

    if medicion.temperatura > 37.8:
        alertas.append(("Temperatura elevada", "Posible fiebre", "medio"))
        estado = "alerta"

    if medicion.presion_sistolica and medicion.presion_diastolica:
        if medicion.presion_sistolica > 140 or medicion.presion_diastolica > 90:
            alertas.append(("Presión alta", "Presión arterial elevada", "alto"))
            estado = "alerta"

        if medicion.presion_sistolica < 90 or medicion.presion_diastolica < 60:
            alertas.append(("Presión baja", "Presión arterial baja", "alto"))
            estado = "alerta"

    medicion.estado = estado
    medicion.save()

    for tipo, mensaje, nivel in alertas:
        Alerta.objects.create(
            paciente=paciente,
            medicion=medicion,
            tipo=tipo,
            mensaje=mensaje,
            nivel=nivel
        )


@api_view(["POST"])
def recibir_signos(request):
    token = request.headers.get("X-ROBOT-TOKEN")

    if token != settings.ROBOT_API_TOKEN:
        return Response(
            {"error": "Token del robot inválido"},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = MedicionSerializer(data=request.data)

    if serializer.is_valid():
        paciente_id = serializer.validated_data.pop("paciente_id")

        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        medicion = Medicion.objects.create(
            paciente=paciente,
            **serializer.validated_data
        )

        evaluar_alertas(paciente, medicion)

        return Response(
            {
                "mensaje": "Medición guardada correctamente",
                "medicion_id": medicion.id,
                "estado": medicion.estado
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response(
            {"error": "Paciente no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

    usuario = request.user

    if es_paciente(usuario):
        if paciente.usuario != usuario:
            return Response(
                {"error": "No tienes permiso para ver este historial"},
                status=status.HTTP_403_FORBIDDEN
            )

    elif es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response(
                {"error": "Perfil de doctor no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        if paciente.doctor != doctor:
            return Response(
                {"error": "Este paciente no está asignado a este doctor"},
                status=status.HTTP_403_FORBIDDEN
            )

    elif not es_administrador(usuario):
        return Response(
            {"error": "No tienes permiso para ver este historial"},
            status=status.HTTP_403_FORBIDDEN
        )

    mediciones = Medicion.objects.filter(paciente=paciente).order_by("-fecha_hora")
    serializer = HistorialMedicionSerializer(mediciones, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alertas_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response(
            {"error": "Paciente no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response(
            {"error": "No tienes permiso para ver estas alertas"},
            status=status.HTTP_403_FORBIDDEN
        )

    if es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response(
                {"error": "Perfil de doctor no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        if paciente.doctor != doctor:
            return Response(
                {"error": "Este paciente no está asignado a este doctor"},
                status=status.HTTP_403_FORBIDDEN
            )

    if not es_paciente(usuario) and not es_doctor(usuario) and not es_administrador(usuario):
        return Response(
            {"error": "No tienes permiso"},
            status=status.HTTP_403_FORBIDDEN
        )

    alertas = Alerta.objects.filter(paciente=paciente).order_by("-fecha_hora")
    serializer = AlertaSerializer(alertas, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agendar_cita(request):
    usuario = request.user

    if es_paciente(usuario):
        try:
            paciente = Paciente.objects.get(usuario=usuario)
        except Paciente.DoesNotExist:
            return Response({"error": "Perfil de paciente no encontrado"}, status=404)

        datos = request.data.copy()
        datos["paciente"] = paciente.id

        serializer = CitaSerializer(data=datos)

    elif es_administrador(usuario):
        serializer = CitaSerializer(data=request.data)

    else:
        return Response({"error": "Solo pacientes o administradores pueden agendar citas"}, status=403)

    if serializer.is_valid():
        cita = serializer.save()
        return Response({
            "mensaje": "Cita agendada correctamente",
            "cita_id": cita.id,
            "estado": cita.estado
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def citas_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso para ver estas citas"}, status=403)

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)
        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    citas = Cita.objects.filter(paciente=paciente).order_by("-fecha_hora")
    serializer = CitaSerializer(citas, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def citas_doctor(request, doctor_id):
    usuario = request.user

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)

        if doctor.id != doctor_id:
            return Response({"error": "No tienes permiso para ver citas de otro doctor"}, status=403)

    elif not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    citas = Cita.objects.filter(doctor_id=doctor_id).order_by("-fecha_hora")
    serializer = CitaSerializer(citas, many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subir_estudio(request):
    usuario = request.user

    if es_paciente(usuario):
        try:
            paciente = Paciente.objects.get(usuario=usuario)
        except Paciente.DoesNotExist:
            return Response({"error": "Perfil de paciente no encontrado"}, status=404)

        datos = request.data.copy()
        datos["paciente"] = paciente.id

        serializer = EstudioMedicoSerializer(data=datos)

    elif es_administrador(usuario):
        serializer = EstudioMedicoSerializer(data=request.data)

    else:
        return Response({"error": "Solo pacientes o administradores pueden subir estudios"}, status=403)

    if serializer.is_valid():
        estudio = serializer.save()
        return Response({
            "mensaje": "Estudio médico subido correctamente",
            "estudio_id": estudio.id,
            "archivo": estudio.archivo.url
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estudios_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso para ver estos estudios"}, status=403)

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)
        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    estudios = EstudioMedico.objects.filter(paciente=paciente).order_by("-fecha_subida")
    serializer = EstudioMedicoSerializer(estudios, many=True)
    return Response(serializer.data)

def generar_respuesta_chatbot(pregunta):
    pregunta = pregunta.lower()

    if "signos" in pregunta or "vitales" in pregunta:
        return "Para tomar tus signos vitales, coloca tu dedo en el sensor y espera unos segundos hasta que el sistema registre BPM, SpO₂ y temperatura."

    if "temperatura" in pregunta:
        return "La temperatura corporal normal suele estar alrededor de 36 a 37.5 °C. Si el sistema detecta temperatura elevada, generará una alerta."

    if "oxigeno" in pregunta or "spo2" in pregunta or "saturacion" in pregunta:
        return "La SpO₂ indica el nivel de oxígeno en sangre. Un valor bajo puede generar una alerta para revisión médica."

    if "pulso" in pregunta or "bpm" in pregunta or "ritmo" in pregunta:
        return "El BPM representa los latidos por minuto. El sistema puede detectar si el ritmo cardíaco está bajo o elevado."

    if "presion" in pregunta:
        return "La presión arterial se registra con los valores sistólico y diastólico. Si está fuera de rango, el sistema generará una alerta."

    if "cita" in pregunta:
        return "Puedes agendar una cita médica desde el módulo de citas. El doctor podrá aceptarla, rechazarla o finalizarla."

    if "estudio" in pregunta or "archivo" in pregunta or "pdf" in pregunta:
        return "Puedes subir estudios médicos en formato PDF o imagen para que el doctor los revise."

    return "Soy el asistente de Clinik Bot. Puedo orientarte sobre signos vitales, temperatura, pulso, SpO₂, presión arterial, citas y estudios médicos. Recuerda que no sustituyo a un médico."

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chatbot_responder(request):
    usuario = request.user
    pregunta = request.data.get("pregunta")

    if not pregunta:
        return Response({"error": "Debes enviar una pregunta"}, status=400)

    if es_paciente(usuario):
        try:
            paciente = Paciente.objects.get(usuario=usuario)
        except Paciente.DoesNotExist:
            return Response({"error": "Perfil de paciente no encontrado"}, status=404)

    elif es_administrador(usuario):
        paciente_id = request.data.get("paciente")

        if not paciente_id:
            return Response({"error": "Debes enviar paciente"}, status=400)

        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response({"error": "Paciente no encontrado"}, status=404)

    else:
        return Response({"error": "Solo pacientes o administradores pueden usar el chatbot"}, status=403)

    respuesta = generar_respuesta_chatbot(pregunta)

    mensaje = MensajeChatbot.objects.create(
        paciente=paciente,
        pregunta=pregunta,
        respuesta=respuesta
    )

    serializer = MensajeChatbotSerializer(mensaje)
    return Response(serializer.data, status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_chatbot(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso para ver este historial"}, status=403)

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)
        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    mensajes = MensajeChatbot.objects.filter(paciente=paciente).order_by("-fecha_hora")
    serializer = MensajeChatbotSerializer(mensajes, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    usuario = request.user

    rol = "Sin rol"

    if es_administrador(usuario):
        rol = "Administrador"
    elif es_doctor(usuario):
        rol = "Doctor"
    elif es_paciente(usuario):
        rol = "Paciente"

    data = {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "nombre": usuario.first_name,
        "apellido": usuario.last_name,
        "rol": rol,
    }

    if rol == "Paciente":
        try:
            paciente = Paciente.objects.get(usuario=usuario)
            data["paciente_id"] = paciente.id
        except Paciente.DoesNotExist:
            data["paciente_id"] = None

    if rol == "Doctor":
        try:
            doctor = Doctor.objects.get(usuario=usuario)
            data["doctor_id"] = doctor.id
        except Doctor.DoesNotExist:
            data["doctor_id"] = None

    return Response(data)

@api_view(["POST"])
def registrar_paciente(request):
    serializer = RegistroPacienteSerializer(data=request.data)

    if serializer.is_valid():
        paciente = serializer.save()
        return Response({
            "mensaje": "Paciente registrado correctamente",
            "paciente_id": paciente.id,
            "usuario": paciente.usuario.username
        }, status=201)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_doctor(request):
    if not es_administrador(request.user):
        return Response(
            {"error": "Solo el administrador puede registrar doctores"},
            status=403
        )

    serializer = RegistroDoctorSerializer(data=request.data)

    if serializer.is_valid():
        doctor = serializer.save()
        return Response({
            "mensaje": "Doctor registrado correctamente",
            "doctor_id": doctor.id,
            "usuario": doctor.usuario.username
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_paciente(request):
    if not es_paciente(request.user):
        return Response({"error": "Solo pacientes pueden acceder"}, status=403)

    try:
        paciente = Paciente.objects.get(usuario=request.user)
    except Paciente.DoesNotExist:
        return Response({"error": "Perfil de paciente no encontrado"}, status=404)

    ultima_medicion = Medicion.objects.filter(paciente=paciente).order_by("-fecha_hora").first()
    alertas_pendientes = Alerta.objects.filter(paciente=paciente, atendida=False).count()
    citas_pendientes = Cita.objects.filter(paciente=paciente, estado="pendiente").count()
    estudios = EstudioMedico.objects.filter(paciente=paciente).count()

    data = {
        "paciente_id": paciente.id,
        "nombre": paciente.usuario.get_full_name() or paciente.usuario.username,
        "ultima_medicion": None,
        "alertas_pendientes": alertas_pendientes,
        "citas_pendientes": citas_pendientes,
        "total_estudios": estudios,
    }

    if ultima_medicion:
        data["ultima_medicion"] = {
            "bpm": ultima_medicion.bpm,
            "spo2": ultima_medicion.spo2,
            "temperatura": ultima_medicion.temperatura,
            "presion_sistolica": ultima_medicion.presion_sistolica,
            "presion_diastolica": ultima_medicion.presion_diastolica,
            "estado": ultima_medicion.estado,
            "fecha_hora": ultima_medicion.fecha_hora,
        }

    return Response(data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_doctor(request):
    if not es_doctor(request.user):
        return Response({"error": "Solo doctores pueden acceder"}, status=403)

    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        return Response({"error": "Perfil de doctor no encontrado"}, status=404)

    pacientes = Paciente.objects.filter(doctor=doctor)
    citas_pendientes = Cita.objects.filter(doctor=doctor, estado="pendiente").count()
    alertas_pacientes = Alerta.objects.filter(paciente__doctor=doctor, atendida=False).count()

    data = {
        "doctor_id": doctor.id,
        "nombre": doctor.usuario.get_full_name() or doctor.usuario.username,
        "especialidad": doctor.especialidad,
        "total_pacientes": pacientes.count(),
        "citas_pendientes": citas_pendientes,
        "alertas_pendientes": alertas_pacientes,
        "pacientes": []
    }

    for paciente in pacientes:
        ultima = Medicion.objects.filter(paciente=paciente).order_by("-fecha_hora").first()

        data["pacientes"].append({
            "paciente_id": paciente.id,
            "nombre": paciente.usuario.get_full_name() or paciente.usuario.username,
            "edad": paciente.edad,
            "sexo": paciente.sexo,
            "ultima_medicion": {
                "bpm": ultima.bpm,
                "spo2": ultima.spo2,
                "temperatura": ultima.temperatura,
                "estado": ultima.estado,
                "fecha_hora": ultima.fecha_hora,
            } if ultima else None
        })

    return Response(data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_admin(request):
    if not es_administrador(request.user):
        return Response({"error": "Solo administradores pueden acceder"}, status=403)

    data = {
        "total_pacientes": Paciente.objects.count(),
        "total_doctores": Doctor.objects.count(),
        "total_mediciones": Medicion.objects.count(),
        "total_alertas": Alerta.objects.count(),
        "alertas_pendientes": Alerta.objects.filter(atendida=False).count(),
        "total_citas": Cita.objects.count(),
        "citas_pendientes": Cita.objects.filter(estado="pendiente").count(),
        "total_estudios": EstudioMedico.objects.count(),
    }

    return Response(data, status=200)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def actualizar_estado_cita(request, cita_id):
    try:
        cita = Cita.objects.get(id=cita_id)
    except Cita.DoesNotExist:
        return Response({"error": "Cita no encontrada"}, status=404)

    usuario = request.user
    nuevo_estado = request.data.get("estado")

    estados_validos = ["pendiente", "aceptada", "rechazada", "cancelada", "finalizada"]

    if nuevo_estado not in estados_validos:
        return Response({"error": "Estado no válido"}, status=400)

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)

        if cita.doctor != doctor:
            return Response({"error": "No puedes modificar esta cita"}, status=403)

    elif not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    cita.estado = nuevo_estado
    cita.observaciones = request.data.get("observaciones", cita.observaciones)
    cita.save()

    return Response({
        "mensaje": "Estado de cita actualizado",
        "cita_id": cita.id,
        "estado": cita.estado
    }, status=200)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def atender_alerta(request, alerta_id):
    try:
        alerta = Alerta.objects.get(id=alerta_id)
    except Alerta.DoesNotExist:
        return Response({"error": "Alerta no encontrada"}, status=404)

    usuario = request.user

    if es_doctor(usuario):
        doctor = Doctor.objects.get(usuario=usuario)

        if alerta.paciente.doctor != doctor:
            return Response({"error": "No puedes atender esta alerta"}, status=403)

    elif not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    alerta.atendida = True
    alerta.save()

    return Response({
        "mensaje": "Alerta marcada como atendida",
        "alerta_id": alerta.id,
        "atendida": alerta.atendida
    }, status=200)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def asignar_doctor_paciente(request, paciente_id):
    if not es_administrador(request.user):
        return Response({"error": "Solo el administrador puede asignar doctores"}, status=403)

    doctor_id = request.data.get("doctor_id")

    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({"error": "Doctor no encontrado"}, status=404)

    paciente.doctor = doctor
    paciente.save()

    return Response({
        "mensaje": "Doctor asignado correctamente",
        "paciente_id": paciente.id,
        "doctor_id": doctor.id
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_pacientes(request):
    usuario = request.user

    if es_administrador(usuario):
        pacientes = Paciente.objects.all().order_by("usuario__username")

    elif es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response({"error": "Perfil de doctor no encontrado"}, status=404)

        pacientes = Paciente.objects.filter(doctor=doctor).order_by("usuario__username")

    else:
        return Response({"error": "No tienes permiso para listar pacientes"}, status=403)

    serializer = PacienteSerializer(pacientes, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_doctores(request):
    if not es_administrador(request.user):
        return Response({"error": "Solo el administrador puede listar doctores"}, status=403)

    doctores = Doctor.objects.all().order_by("usuario__username")
    serializer = DoctorSerializer(doctores, many=True)
    return Response(serializer.data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def graficas_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso"}, status=403)

    if es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response({"error": "Perfil de doctor no encontrado"}, status=404)

        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    elif not es_paciente(usuario) and not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    mediciones = Medicion.objects.filter(paciente=paciente).order_by("fecha_hora")

    data = {
        "paciente_id": paciente.id,
        "paciente": paciente.usuario.get_full_name() or paciente.usuario.username,
        "labels": [],
        "bpm": [],
        "spo2": [],
        "temperatura": [],
        "presion_sistolica": [],
        "presion_diastolica": [],
    }

    for m in mediciones:
        data["labels"].append(m.fecha_hora.strftime("%Y-%m-%d %H:%M"))
        data["bpm"].append(m.bpm)
        data["spo2"].append(float(m.spo2))
        data["temperatura"].append(float(m.temperatura))
        data["presion_sistolica"].append(m.presion_sistolica)
        data["presion_diastolica"].append(m.presion_diastolica)

    return Response(data, status=200)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def agregar_observacion_estudio(request, estudio_id):
    try:
        estudio = EstudioMedico.objects.get(id=estudio_id)
    except EstudioMedico.DoesNotExist:
        return Response({"error": "Estudio médico no encontrado"}, status=404)

    usuario = request.user
    observacion = request.data.get("observaciones_doctor")

    if not observacion:
        return Response({"error": "Debes enviar una observación"}, status=400)

    if es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response({"error": "Perfil de doctor no encontrado"}, status=404)

        if estudio.paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

        estudio.doctor = doctor

    elif not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    estudio.observaciones_doctor = observacion
    estudio.save()

    return Response({
        "mensaje": "Observación agregada correctamente",
        "estudio_id": estudio.id,
        "observaciones_doctor": estudio.observaciones_doctor
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reporte_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso"}, status=403)

    if es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response({"error": "Perfil de doctor no encontrado"}, status=404)

        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    elif not es_paciente(usuario) and not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    mediciones = Medicion.objects.filter(paciente=paciente).order_by("-fecha_hora")
    ultima = mediciones.first()

    alertas = Alerta.objects.filter(paciente=paciente).order_by("-fecha_hora")
    citas = Cita.objects.filter(paciente=paciente).order_by("-fecha_hora")
    estudios = EstudioMedico.objects.filter(paciente=paciente).order_by("-fecha_subida")

    data = {
        "paciente": {
            "id": paciente.id,
            "nombre": paciente.usuario.get_full_name() or paciente.usuario.username,
            "edad": paciente.edad,
            "sexo": paciente.sexo,
            "telefono": paciente.telefono,
            "direccion": paciente.direccion,
            "doctor_asignado": paciente.doctor.usuario.get_full_name() if paciente.doctor else None,
        },
        "resumen": {
            "total_mediciones": mediciones.count(),
            "total_alertas": alertas.count(),
            "alertas_pendientes": alertas.filter(atendida=False).count(),
            "total_citas": citas.count(),
            "total_estudios": estudios.count(),
        },
        "ultima_medicion": None,
        "ultimas_alertas": [],
        "ultimas_citas": [],
        "ultimos_estudios": [],
    }

    if ultima:
        data["ultima_medicion"] = {
            "bpm": ultima.bpm,
            "spo2": float(ultima.spo2),
            "temperatura": float(ultima.temperatura),
            "presion_sistolica": ultima.presion_sistolica,
            "presion_diastolica": ultima.presion_diastolica,
            "estado": ultima.estado,
            "fecha_hora": ultima.fecha_hora,
        }

    for alerta in alertas[:5]:
        data["ultimas_alertas"].append({
            "id": alerta.id,
            "tipo": alerta.tipo,
            "mensaje": alerta.mensaje,
            "nivel": alerta.nivel,
            "atendida": alerta.atendida,
            "fecha_hora": alerta.fecha_hora,
        })

    for cita in citas[:5]:
        data["ultimas_citas"].append({
            "id": cita.id,
            "doctor": cita.doctor.usuario.get_full_name() or cita.doctor.usuario.username,
            "fecha_hora": cita.fecha_hora,
            "motivo": cita.motivo,
            "estado": cita.estado,
        })

    for estudio in estudios[:5]:
        data["ultimos_estudios"].append({
            "id": estudio.id,
            "titulo": estudio.titulo,
            "tipo": estudio.tipo,
            "archivo": estudio.archivo.url if estudio.archivo else None,
            "fecha_subida": estudio.fecha_subida,
            "observaciones_doctor": estudio.observaciones_doctor,
        })

    return Response(data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_por_fechas(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"error": "Paciente no encontrado"}, status=404)

    usuario = request.user

    if es_paciente(usuario) and paciente.usuario != usuario:
        return Response({"error": "No tienes permiso"}, status=403)

    if es_doctor(usuario):
        try:
            doctor = Doctor.objects.get(usuario=usuario)
        except Doctor.DoesNotExist:
            return Response({"error": "Perfil de doctor no encontrado"}, status=404)

        if paciente.doctor != doctor:
            return Response({"error": "Este paciente no está asignado a este doctor"}, status=403)

    elif not es_paciente(usuario) and not es_administrador(usuario):
        return Response({"error": "No tienes permiso"}, status=403)

    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")

    mediciones = Medicion.objects.filter(paciente=paciente)

    if fecha_inicio:
        inicio = parse_date(fecha_inicio)
        if not inicio:
            return Response({"error": "Fecha de inicio inválida. Usa YYYY-MM-DD"}, status=400)
        mediciones = mediciones.filter(fecha_hora__date__gte=inicio)

    if fecha_fin:
        fin = parse_date(fecha_fin)
        if not fin:
            return Response({"error": "Fecha de fin inválida. Usa YYYY-MM-DD"}, status=400)
        mediciones = mediciones.filter(fecha_hora__date__lte=fin)

    mediciones = mediciones.order_by("-fecha_hora")
    serializer = HistorialMedicionSerializer(mediciones, many=True)

    return Response({
        "paciente_id": paciente.id,
        "paciente": paciente.usuario.get_full_name() or paciente.usuario.username,
        "inicio": fecha_inicio,
        "fin": fecha_fin,
        "total": mediciones.count(),
        "mediciones": serializer.data
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctores_disponibles(request):
    doctores = Doctor.objects.all().order_by("usuario__username")
    serializer = DoctorSerializer(doctores, many=True)
    return Response(serializer.data, status=200)