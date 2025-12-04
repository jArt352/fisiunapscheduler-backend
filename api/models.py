from django.db import models, transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import Group
from datetime import datetime, timedelta

# --- 1. APERTURA DE PERIODO Y CONFIGURACIÓN ---

class AcademicPeriod(models.Model):
    PERIOD_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
    ]
    year = models.PositiveIntegerField()
    period = models.CharField(max_length=4, choices=PERIOD_CHOICES)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    # Etapa de creación de horarios
    start_schedule_creation = models.DateTimeField("Inicio de creación de horarios")
    end_schedule_creation = models.DateTimeField("Fin de creación de horarios")
    end_date = models.DateTimeField("Cierre de periodo", null=True, blank=True)

    def __str__(self):
        return f"{self.year} - {self.period}"


class GeneralScheduleConfig(models.Model):
    """Configuración global de días y rango horario permitido."""
    DAY_CHOICES = [
        ("lunes", "Lunes"), ("martes", "Martes"), ("miércoles", "Miércoles"),
        ("jueves", "Jueves"), ("viernes", "Viernes"), ("sábado", "Sábado"), ("domingo", "Domingo"),
    ]
    day_name = models.CharField(max_length=50, choices=DAY_CHOICES, help_text="Días habilitados separados por comas")
    start_time = models.TimeField(help_text="Hora de inicio global permitida, ej: 06:00")
    end_time = models.TimeField(help_text="Hora de fin global permitida, ej: 23:00")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.day_name} : {self.start_time} - {self.end_time}"

# --- 2. INFRAESTRUCTURA (AULAS) ---

class Site(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=300)

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ("aula", "Aula"),
        ("laboratorio", "Laboratorio"),
    ]
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    capacity = models.PositiveIntegerField()
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='rooms')
    photo = models.ImageField(upload_to='rooms/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()}) - Cap: {self.capacity}"

# --- 3. ACADÉMICO (CURSOS Y OFERTAS) ---

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    credits = models.PositiveIntegerField(default=0)
    cycle = models.PositiveIntegerField()
    practical_hours = models.PositiveIntegerField(default=0)
    theoretical_hours = models.PositiveIntegerField(default=0)
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='courses')
    
    # Restricciones Físicas
    requires_lab = models.BooleanField(default=False, help_text="¿Requiere laboratorio obligatoriamente?")
    requires_room = models.BooleanField(default=True, help_text="¿Requiere aula?")
    requires_teacher = models.BooleanField(default=True, help_text="¿Requiere docente?")

    def __str__(self):
        return f"{self.code} - {self.name} (Ciclo {self.cycle})"


class CourseOffering(models.Model):
    """Cursos ofertados en un periodo específico."""
    OFFERING_TYPES = [
        ("normal", "Normal"),
        ("nivelacion", "Nivelación"),
        ("vacacional", "Vacacional"),
    ]

    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='offerings')
    academic_period = models.ForeignKey('AcademicPeriod', on_delete=models.CASCADE, related_name='offerings')
    offering_type = models.CharField(max_length=20, choices=OFFERING_TYPES, default='normal')
    
    # Capacidad base estimada para los grupos de este curso
    capacity = models.PositiveIntegerField(default=40, help_text="Capacidad base estimada para los grupos")
    
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (('course', 'academic_period', 'offering_type'),)

    def __str__(self):
        return f"{self.course.code} - {self.get_offering_type_display()} ({self.academic_period})"


class CourseGroup(models.Model):
    """Representa un grupo/sección de una oferta."""
    course_offering = models.ForeignKey('CourseOffering', on_delete=models.CASCADE, related_name='groups')
    code = models.CharField(max_length=20)
    
    # Capacidad específica del grupo (opcional)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Si se deja vacío, hereda de la Oferta")

    class Meta:
        unique_together = (('course_offering', 'code'),)

    @property
    def real_capacity(self):
        """Devuelve la capacidad real del grupo (o la heredada)."""
        if self.capacity is not None:
            return self.capacity
        return self.course_offering.capacity

    def __str__(self):
        return f"{self.course_offering.course.code} - G{self.code}"


class CourseGroupConfig(models.Model):
    """Configuración para generar grupos automáticamente."""
    course_offering = models.OneToOneField('CourseOffering', on_delete=models.CASCADE, related_name='group_config')
    num_groups = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Config {self.course_offering}: {self.num_groups} grupos"

# --- 4. POLÍTICAS Y PREFERENCIAS ---

class CourseSessionPolicy(models.Model):
    MODE_CHOICES = [("juntas", "Juntas"), ("separadas", "Separadas")]
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='session_policy')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='separadas')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Política {self.course.code}: {self.get_mode_display()}"



class CourseDayPreference(models.Model):
    """Solo días preferidos. Cada curso debe tener al menos un día preferido."""
    DAY_CHOICES = [
        ("mon", "Lunes"), ("tue", "Martes"), ("wed", "Miércoles"),
        ("thu", "Jueves"), ("fri", "Viernes"), ("sat", "Sábado"), ("sun", "Domingo")
    ]
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='day_preferences')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)

    class Meta:
        unique_together = (('course', 'day'),)

    # Ya no se requiere validación obligatoria de días preferidos


class CourseTeacherPreference(models.Model):
    """Solo docentes preferidos. Cada curso debe tener al menos un docente preferido."""
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='teacher_preferences')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='course_preferences')
    
    class Meta:
        unique_together = (('course', 'teacher'),)
        ordering = ['course', 'teacher']

    def clean(self):
        # Validar que cada curso tenga al menos un docente preferido
        if not CourseTeacherPreference.objects.filter(course=self.course).exclude(pk=self.pk).exists():
            raise ValidationError('Cada curso debe tener al menos un docente preferido.')
    
    def __str__(self):
        return f"Preferencia: {self.course.code} - {self.teacher.person.first_name} {self.teacher.person.last_name}"

# --- 5. PERSONAS Y DOCENTES ---

class Plan(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='plans')
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.school})"

class SchoolDirector(models.Model):
    school = models.OneToOneField('School', on_delete=models.CASCADE, related_name='director')
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='school_director_roles')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

class DepartmentHead(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='department_heads')
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='department_head_roles')
    department_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

class Faculty(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    def __str__(self): return self.name

class School(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="schools")
    def __str__(self): return self.name

class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField("Apellido paterno", max_length=100)
    middle_name = models.CharField("Apellido materno", max_length=100)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='person_profile')
    roles = models.ManyToManyField(Group, blank=True, related_name='people')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Teacher(models.Model):
    CONTRACT_TYPE_CHOICES = [("contratado", "Contratado"), ("nombrado", "Nombrado"), ("asociado", "Asociado")]
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="teacher")
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    min_weekly_hours = models.PositiveIntegerField()
    max_unavailability_hours = models.PositiveIntegerField(default=0)
    faculties = models.ManyToManyField('Faculty', related_name='teachers', blank=True)

    def __str__(self):
        return f"{self.person}"

class TeacherUnavailability(models.Model):
    DAY_CHOICES = [
        ("mon", "Lunes"), ("tue", "Martes"), ("wed", "Miércoles"),
        ("thu", "Jueves"), ("fri", "Viernes"), ("sat", "Sábado"),
    ]
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='unavailabilities')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['teacher', 'day', 'start_time']

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'La hora de fin debe ser posterior a la de inicio.'})
        
        overlapping = TeacherUnavailability.objects.filter(
            teacher=self.teacher, day=self.day
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time, end_time__gt=self.start_time
        )
        if overlapping.exists():
            raise ValidationError("Solapamiento de horario detectado.")

    def __str__(self):
        return f"{self.teacher} - {self.day} {self.start_time}-{self.end_time}"

# --- 6. HORARIO FINAL ---

class Schedule(models.Model):
    SESSION_TYPE_CHOICES = [("teoria", "Teoría"), ("practica", "Práctica")]

    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='schedules')
    group = models.ForeignKey('CourseGroup', on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    day_of_week = models.PositiveIntegerField()  # 0=Lunes, 6=Domingo
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
    
    class Meta:
        ordering = ['start_time']

    def __str__(self):
        room_name = self.room.name if self.room else "Sin Aula"
        return f"{self.course.name} ({self.get_session_type_display()}) - {self.group.code} - {room_name}"


# --- 7. SOLICITUDES DE CAMBIO DE HORARIO ---

class ScheduleChangeRequest(models.Model):
    REQUEST_TYPES = [
        ("cambio_vacio", "Cambio a espacio vacío"),
        ("cambio_ocupado", "Cambio a horario ocupado"),
        ("rechazo_curso", "Rechazo de curso"),
        ("abrir_grupo", "Abrir grupo"),
    ]
    STATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    schedule = models.ForeignKey('Schedule', null=True, blank=True, on_delete=models.SET_NULL, related_name='change_requests')
    requested_by = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='change_requests')
    target_teacher = models.ForeignKey('Teacher', null=True, blank=True, on_delete=models.SET_NULL, related_name='proposed_for_requests')
    target_room = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL)
    target_day = models.PositiveIntegerField(null=True, blank=True)
    target_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendiente")
    approvals = models.JSONField(default=dict)  # Ejemplo: {"director": null, "jefe": null, "docente": null}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Solicitud {self.get_request_type_display()} por {self.requested_by} - Estado: {self.get_status_display()}"


# --- 7. SEÑALES (SIGNALS) ---

@receiver(pre_save, sender=CourseGroupConfig)
def courseconfig_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_num_groups = 0
        return
    try:
        old = CourseGroupConfig.objects.get(pk=instance.pk)
        instance._old_num_groups = getattr(old, 'num_groups', 0)
    except CourseGroupConfig.DoesNotExist:
        instance._old_num_groups = 0

@receiver(post_save, sender=CourseGroupConfig)
def courseconfig_post_save(sender, instance, created, **kwargs):
    new = instance.num_groups
    course_offering = instance.course_offering
    with transaction.atomic():
        CourseGroup.objects.filter(course_offering=course_offering).delete()
        for i in range(1, new + 1):
            CourseGroup.objects.create(course_offering=course_offering, code=str(i))

@receiver(post_delete, sender=CourseGroupConfig)
def courseconfig_post_delete(sender, instance, **kwargs):
    instance.course_offering.groups.all().delete()

@receiver(post_save, sender=AcademicPeriod)
def create_course_offerings_for_period(sender, instance, created, **kwargs):

    if not created:
        return

    # Solo dos planes activos
    planes = Plan.objects.filter(is_active=True).order_by('start_year')
    if planes.count() != 2:
        return  # No se puede abrir cursos si no hay exactamente dos planes activos
    plan_antiguo, plan_nuevo = planes[0], planes[1]

    # Calcular ciclo actual del plan nuevo
    años = instance.year - plan_nuevo.start_year
    ciclo_nuevo = años * 2 + (1 if instance.period == 'I' else 2)
    max_ciclo = Course.objects.filter(plan=plan_nuevo).aggregate(models.Max('cycle'))['cycle__max'] or 10

    # Abrir cursos del ciclo actual del plan nuevo
    cursos_nuevo = Course.objects.filter(plan=plan_nuevo, cycle__lte=ciclo_nuevo)
    # Abrir cursos del plan antiguo que no están cubiertos por el plan nuevo
    ciclos_antiguos = [c for c in range(1, max_ciclo+1) if c > ciclo_nuevo]
    cursos_antiguo = Course.objects.filter(plan=plan_antiguo, cycle__in=ciclos_antiguos)

    # Abrir cursos de nivelación del plan antiguo solo para el ciclo más alto que ya no se dicta normalmente
    ciclo_nivelacion = ciclo_nuevo - 1 if ciclo_nuevo > 1 else None
    cursos_nivelacion = Course.objects.filter(plan=plan_antiguo, cycle=ciclo_nivelacion)

    # Crear ofertas para cursos normales
    for curso in list(cursos_nuevo) + list(cursos_antiguo):
        offering, _ = CourseOffering.objects.get_or_create(
            course=curso,
            academic_period=instance,
            offering_type="normal",
            defaults={'capacity': 40}
        )
        if not hasattr(offering, 'group_config') and not offering.groups.exists():
            CourseGroup.objects.create(course_offering=offering, code="1")

    # Crear ofertas para cursos de nivelación
    for curso in cursos_nivelacion:
        offering, _ = CourseOffering.objects.get_or_create(
            course=curso,
            academic_period=instance,
            offering_type="nivelacion",
            defaults={'capacity': 40}
        )
        if not hasattr(offering, 'group_config') and not offering.groups.exists():
            CourseGroup.objects.create(course_offering=offering, code="1")

    # Desactivar plan antiguo si el plan nuevo ya cubre todos los ciclos
    if ciclo_nuevo >= max_ciclo:
        plan_antiguo.is_active = False
        plan_antiguo.end_year = instance.year
        plan_antiguo.save()