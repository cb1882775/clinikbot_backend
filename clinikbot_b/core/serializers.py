from rest_framework import serializers
from .models import Medicion
from .models import Alerta, Cita, EstudioMedico, MensajeChatbot


class MedicionSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Medicion
        fields = [
            "id",
            "paciente_id",
            "bpm",
            "spo2",
            "temperatura",
            "presion_sistolica",
            "presion_diastolica",
            "estado",
            "fecha_hora",
        ]
        read_only_fields = ["id", "estado", "fecha_hora"]

    def validate_bpm(self, value):
        if value < 30 or value > 220:
            raise serializers.ValidationError("El BPM está fuera de un rango válido.")
        return value

    def validate_spo2(self, value):
        if value < 50 or value > 100:
            raise serializers.ValidationError("El SpO₂ debe estar entre 50 y 100.")
        return value

    def validate_temperatura(self, value):
        if value < 30 or value > 45:
            raise serializers.ValidationError("La temperatura está fuera de un rango válido.")
        return value

    def validate(self, data):
        sistolica = data.get("presion_sistolica")
        diastolica = data.get("presion_diastolica")

        if sistolica is not None and (sistolica < 60 or sistolica > 250):
            raise serializers.ValidationError({
                "presion_sistolica": "La presión sistólica está fuera de rango."
            })

        if diastolica is not None and (diastolica < 40 or diastolica > 150):
            raise serializers.ValidationError({
                "presion_diastolica": "La presión diastólica está fuera de rango."
            })

        if sistolica is not None and diastolica is not None:
            if diastolica >= sistolica:
                raise serializers.ValidationError(
                    "La presión diastólica no puede ser mayor o igual que la sistólica."
                )

        return data

class HistorialMedicionSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source="paciente.usuario.username", read_only=True)

    class Meta:
        model = Medicion
        fields = [
            "id",
            "paciente_nombre",
            "bpm",
            "spo2",
            "temperatura",
            "presion_sistolica",
            "presion_diastolica",
            "estado",
            "fecha_hora",
        ]
class AlertaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source="paciente.usuario.username", read_only=True)

    class Meta:
        model = Alerta
        fields = [
            "id",
            "paciente_nombre",
            "tipo",
            "mensaje",
            "nivel",
            "fecha_hora",
            "atendida",
        ]
    
class CitaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source="paciente.usuario.username", read_only=True)
    doctor_nombre = serializers.CharField(source="doctor.usuario.username", read_only=True)

    class Meta:
        model = Cita
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "doctor",
            "doctor_nombre",
            "fecha_hora",
            "motivo",
            "estado",
            "observaciones",
            "creado_en",
        ]
        read_only_fields = ["estado", "observaciones", "creado_en"]

class EstudioMedicoSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source="paciente.usuario.username", read_only=True)
    doctor_nombre = serializers.CharField(source="doctor.usuario.username", read_only=True)

    class Meta:
        model = EstudioMedico
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "doctor",
            "doctor_nombre",
            "titulo",
            "tipo",
            "archivo",
            "descripcion",
            "observaciones_doctor",
            "fecha_subida",
        ]
        read_only_fields = ["observaciones_doctor", "fecha_subida"]

    def validate_archivo(self, archivo):
        extensiones_permitidas = [".pdf", ".jpg", ".jpeg", ".png"]
        nombre = archivo.name.lower()

        if not any(nombre.endswith(ext) for ext in extensiones_permitidas):
            raise serializers.ValidationError(
                "Solo se permiten archivos PDF, JPG, JPEG o PNG."
            )

        limite_mb = 5
        if archivo.size > limite_mb * 1024 * 1024:
            raise serializers.ValidationError(
                "El archivo no debe superar los 5 MB."
            )

        return archivo

class MensajeChatbotSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source="paciente.usuario.username", read_only=True)

    class Meta:
        model = MensajeChatbot
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "pregunta",
            "respuesta",
            "fecha_hora",
        ]
        read_only_fields = ["respuesta", "fecha_hora"]


from django.contrib.auth.models import User, Group
from .models import Doctor, Paciente


class RegistroPacienteSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    nombre = serializers.CharField(required=False, allow_blank=True)
    apellido = serializers.CharField(required=False, allow_blank=True)
    edad = serializers.IntegerField()
    sexo = serializers.CharField()
    telefono = serializers.CharField(required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("nombre", ""),
            last_name=validated_data.get("apellido", "")
        )

        grupo, _ = Group.objects.get_or_create(name="Paciente")
        user.groups.add(grupo)

        paciente = Paciente.objects.create(
            usuario=user,
            edad=validated_data["edad"],
            sexo=validated_data["sexo"],
            telefono=validated_data.get("telefono", ""),
            direccion=validated_data.get("direccion", "")
        )

        return paciente


class RegistroDoctorSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    nombre = serializers.CharField(required=False, allow_blank=True)
    apellido = serializers.CharField(required=False, allow_blank=True)
    especialidad = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("nombre", ""),
            last_name=validated_data.get("apellido", "")
        )

        grupo, _ = Group.objects.get_or_create(name="Doctor")
        user.groups.add(grupo)

        doctor = Doctor.objects.create(
            usuario=user,
            especialidad=validated_data.get("especialidad", ""),
            telefono=validated_data.get("telefono", "")
        )

        return doctor
    
class PacienteSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    username = serializers.CharField(source="usuario.username", read_only=True)
    nombre = serializers.CharField(source="usuario.first_name", read_only=True)
    apellido = serializers.CharField(source="usuario.last_name", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)
    doctor_nombre = serializers.CharField(source="doctor.usuario.username", read_only=True)

    class Meta:
        model = Paciente
        fields = [
            "id",
            "usuario_id",
            "username",
            "nombre",
            "apellido",
            "email",
            "edad",
            "sexo",
            "peso",
            "estatura",
            "telefono",
            "direccion",
            "doctor",
            "doctor_nombre",
        ]


class DoctorSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    username = serializers.CharField(source="usuario.username", read_only=True)
    nombre = serializers.CharField(source="usuario.first_name", read_only=True)
    apellido = serializers.CharField(source="usuario.last_name", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "id",
            "usuario_id",
            "username",
            "nombre",
            "apellido",
            "email",
            "especialidad",
            "telefono",
        ]