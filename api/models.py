from django.db import models
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import Group


# Apertura de periodo y fases

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
	# El cierre del periodo puede quedar nulo
	end_date = models.DateTimeField("Cierre de periodo", null=True, blank=True)

	def __str__(self):
		return f"{self.year} - {self.period}"


## Eliminado PeriodPhase: ahora solo se usan los campos de AcademicPeriod


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
		return f"{self.name} ({self.get_room_type_display()}) - {self.site}"


class Course(models.Model):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=200)
	credits = models.PositiveIntegerField(default=0)
	cycle = models.PositiveIntegerField()
	practical_hours = models.PositiveIntegerField(default=0)
	theoretical_hours = models.PositiveIntegerField(default=0)
	plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='courses')

	def __str__(self):
		return f"{self.code} - {self.name}"


class CourseOffering(models.Model):
	"""Cursos ofertados: relación entre un curso y su tipo de oferta.

	- `course`: FK al curso base
	- `academic_period`: opcional, periodo en que se oferta
	- `offering_type`: normal, nivelación, vacacional
	- `capacity`: cupo estimado
	- `notes`: observaciones
	"""
	OFFERING_TYPES = [
		("normal", "Normal"),
		("nivelacion", "Nivelación"),
		("vacacional", "Vacacional"),
	]

	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='offerings')
	academic_period = models.ForeignKey('AcademicPeriod', on_delete=models.SET_NULL, null=True, blank=True, related_name='offerings')
	offering_type = models.CharField(max_length=20, choices=OFFERING_TYPES, default='normal')
	notes = models.TextField(blank=True)

	class Meta:
		unique_together = (('course', 'academic_period', 'offering_type'),)

	def __str__(self):
		period = self.academic_period or "(sin periodo)"
		return f"{self.course.code} - {self.get_offering_type_display()} {period}"


class CourseSessionPolicy(models.Model):
	"""Política por curso sobre si las horas prácticas y teóricas deben ir juntas o pueden ser separadas.

	- `course`: OneToOne con `Course` (una política por curso).
	- `mode`: 'juntas' = se requiere que las horas prácticas y teóricas se programen de forma conjunta;
			  'separadas' = se permiten sesiones diferentes para teoría y práctica.

	Nota: La implementación de la verificación automática puede depender de tus reglas exactas
	(por ejemplo, qué significa "juntas": misma franja horaria, sesiones contiguas, una única sesión
	que cubra ambas horas, etc.). Aquí se ofrece una validación básica que puedes ampliar.
	"""
	MODE_CHOICES = [
		("juntas", "Juntas"),
		("separadas", "Separadas"),
	]

	course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='session_policy')
	mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='separadas')
	notes = models.TextField(blank=True)

	def __str__(self):
		return f"Política {self.course.code}: {self.get_mode_display()}"

	def validate_group_schedules(self, group):
		"""Valida si las entradas de `Schedule` del `group` cumplen la política.

		Comportamiento actual (básico):
		- Si `mode == 'separadas'`: siempre válido.
		- Si `mode == 'juntas'`: considera inválido si existen `Schedule` para ese grupo
		  con session_type diferentes (es decir, hay sesiones separadas de teoría y práctica).

		Esta validación es deliberadamente conservadora; puedes ampliarla para aceptar
		sesiones contiguas o solapadas como "juntas" según tus reglas.

		Devuelve `True` si cumple, `False` si no cumple.
		"""
		if self.mode == 'separadas':
			return True

		# modo 'juntas'
		types = set(group.schedules.values_list('session_type', flat=True))
		# si hay más de un tipo distinto, consideramos que están separadas
		return len([t for t in types if t]) <= 1

class CourseShiftPreference(models.Model):
	"""Preferencia de turno para un curso (mañana, tarde, noche)."""
	SHIFT_CHOICES = [
		("morning", "Mañana"),
		("afternoon", "Tarde"),
		("night", "Noche"),
	]
	PREFERENCE_CHOICES = [
		("prefer", "Prefiere"),
		("avoid", "Evitar"),
	]
	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='shift_preferences')
	shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
	preference = models.CharField(max_length=10, choices=PREFERENCE_CHOICES, default='prefer')

	class Meta:
		unique_together = (('course', 'shift'),)

	def __str__(self):
		return f"{self.course.code} - {self.get_shift_display()} ({self.get_preference_display()})"


class CourseDayPreference(models.Model):
	"""Preferencias de día para un curso. Un curso puede tener varias preferencias (por ejemplo lunes y miércoles)."""
	DAY_CHOICES = [
		("mon", "Lunes"),
		("tue", "Martes"),
		("wed", "Miércoles"),
		("thu", "Jueves"),
		("fri", "Viernes"),
		("sat", "Sábado"),
		("sun", "Domingo"),
	]
	PREFERENCE_CHOICES = [
		("prefer", "Prefiere"),
		("avoid", "Evitar"),
	]

	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='day_preferences')
	day = models.CharField(max_length=3, choices=DAY_CHOICES)
	preference = models.CharField(max_length=10, choices=PREFERENCE_CHOICES, default='prefer')

	class Meta:
		unique_together = (('course', 'day'),)

	def __str__(self):
		return f"{self.course.code} - {self.get_day_display()} ({self.get_preference_display()})"


class CourseTeacherPreference(models.Model):
	"""Preferencia de docentes para un curso.

	Relaciona un `Teacher` con un `Course` y un nivel de preferencia:
	- alto
	- normal
	- baja
	- nula (no debe dictar)
	"""
	PREFERENCE_LEVELS = [
		("alto", "Alto"),
		("normal", "Normal"),
		("baja", "Baja"),
		("nula", "Nula"),
	]

	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='teacher_preferences')
	teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='course_preferences')
	level = models.CharField(max_length=10, choices=PREFERENCE_LEVELS, default='normal')
	notes = models.TextField(blank=True)

	class Meta:
		unique_together = (('course', 'teacher'),)
		ordering = ['course', 'level']

	def __str__(self):
		return f"{self.course.code} - {self.teacher.person} ({self.get_level_display()})"

class CourseGroup(models.Model):
	"""Representa un grupo/ sección de un curso (varios grupos por curso)."""
	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='groups')
	code = models.CharField(max_length=20)

	class Meta:
		unique_together = (('course', 'code'),)

	def __str__(self):
		return f"{self.course.code}-{self.code}"



class CourseGroupConfig(models.Model):
	"""Configuración separada de grupos para un curso.

	Permite especificar cuántos grupos tendrá un curso sin modificar la tabla `Course`.
	"""
	course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='group_config')
	num_groups = models.PositiveIntegerField(default=1)

	def __str__(self):
		return f"Config grupos {self.course.code}: {self.num_groups}"


# --- Señales para crear/ajustar CourseGroup automáticamente basadas en CourseGroupConfig ---
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
	course = instance.course
	with transaction.atomic():
		# Eliminar todos los grupos existentes para evitar duplicados
		CourseGroup.objects.filter(course=course).delete()
		# Crear los grupos nuevos
		for i in range(1, new + 1):
			CourseGroup.objects.create(course=course, code=str(i))



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

	def __str__(self):
		return f"Director de {self.school}: {self.person}"

class DepartmentHead(models.Model):
	school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='department_heads')
	person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='department_head_roles')
	department_name = models.CharField(max_length=200)
	start_date = models.DateField()
	end_date = models.DateField(blank=True, null=True)

	def __str__(self):
		return f"Jefe de {self.department_name} en {self.school}: {self.person}"

class Faculty(models.Model):
	name = models.CharField(max_length=200, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name

class School(models.Model):
	name = models.CharField(max_length=200, unique=True)
	description = models.TextField(blank=True)
	faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="schools")

	def __str__(self):
		return self.name

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
		return f"{self.first_name} {self.last_name} {self.middle_name}"

class Teacher(models.Model):
	CONTRACT_TYPE_CHOICES = [
		("contratado", "Contratado"),
		("nombrado", "Nombrado"),
		("asociado", "Asociado"),
	]
	person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="teacher")
	contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
	min_weekly_hours = models.PositiveIntegerField()
	max_unavailability_hours = models.PositiveIntegerField(default=0, help_text="Horas máximas de indisponibilidad por semana")
	faculties = models.ManyToManyField('Faculty', related_name='teachers', blank=True)

	def __str__(self):
		return f"{self.person} - {self.get_contract_type_display()}"


class TeacherUnavailability(models.Model):
	"""Indisponibilidades del docente: día de la semana, hora inicio y hora fin."""
	DAY_CHOICES = [
		("mon", "Lunes"),
		("tue", "Martes"),
		("wed", "Miércoles"),
		("thu", "Jueves"),
		("fri", "Viernes"),
		("sat", "Sábado"),
	]

	teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='unavailabilities')
	day = models.CharField(max_length=3, choices=DAY_CHOICES)
	start_time = models.TimeField()
	end_time = models.TimeField()

	class Meta:
		ordering = ['teacher', 'day', 'start_time']

	def clean(self):
		# Validación básica: end_time debe ser mayor que start_time
		if self.end_time <= self.start_time:
			raise ValidationError({'end_time': 'La hora de fin debe ser posterior a la hora de inicio.'})

	def __str__(self):
		return f"{self.teacher.person} - {self.get_day_display()} {self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"


class Schedule(models.Model):
	"""Entrada de horario que une curso, grupo, docente, aula y tiempo.

	start_time y end_time son campos `TimeField`. session_type indica si la sesión
	es teórica o práctica.
	"""
	SESSION_TYPE_CHOICES = [
		("teoria", "Teoría"),
		("practica", "Práctica"),
	]

	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='schedules')
	group = models.ForeignKey('CourseGroup', on_delete=models.CASCADE, related_name='schedules')
	teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
	day_of_week = models.PositiveIntegerField()  # 0=Monday, 6=Sunday
	room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
	start_time = models.TimeField()
	end_time = models.TimeField()
	session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
	
	class Meta:
		ordering = ['start_time']

	def __str__(self):
		return f"{self.course.code} {self.group.code} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} ({self.get_session_type_display()})"


class Shift(models.Model):
	"""Define los turnos (mañana, tarde, noche) con su hora de inicio y fin."""
	SHIFT_CHOICES = [
		("morning", "Mañana"),
		("afternoon", "Tarde"),
		("night", "Noche"),
	]

	name = models.CharField(max_length=20, choices=SHIFT_CHOICES, unique=True)
	start_time = models.TimeField()
	end_time = models.TimeField()
	description = models.CharField(max_length=200, blank=True)

	class Meta:
		ordering = ['start_time']

	def __str__(self):
		return f"{self.get_name_display()} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
