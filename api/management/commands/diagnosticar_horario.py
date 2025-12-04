from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from api.models import CourseGroup, Room, Teacher, AcademicPeriod
from django.utils import timezone

class Command(BaseCommand):
    help = 'Diagnostica por qué falla el horario'

    def handle(self, *args, **options):
        self.stdout.write("🕵️ INICIANDO DIAGNÓSTICO PROFUNDO...")

        # 1. Detectar Periodo
        now = timezone.now()
        period = AcademicPeriod.objects.filter(
            start_schedule_creation__lte=now, 
            end_schedule_creation__gte=now
        ).order_by('-start_schedule_creation').first()
        
        if not period:
            self.stdout.write(self.style.ERROR("❌ No hay periodo activo."))
            return

        groups = CourseGroup.objects.filter(course_offering__academic_period=period)
        if not groups.exists():
            self.stdout.write(self.style.ERROR("❌ No hay grupos creados para este periodo."))
            return

        self.stdout.write(f"✅ Analizando {groups.count()} grupos para el periodo {period}")

        # --- 2. CHEQUEO DE DOCENTES (Causa #1 de fallos) ---
        self.stdout.write("\n--- 1. VERIFICACIÓN DE DOCENTES ---")
        teachers = Teacher.objects.all()
        if not teachers.exists():
            self.stdout.write(self.style.ERROR("❌ CRÍTICO: No hay docentes registrados en el sistema."))
        
        cursos_sin_profe = []
        for g in groups:
            course = g.course_offering.course
            if not course.requires_teacher:
                continue
            
            # Docentes no vetados
            vetados = course.teacher_preferences.filter(level='nula').values_list('teacher_id', flat=True)
            candidatos = teachers.exclude(id__in=vetados)
            
            if not candidatos.exists():
                cursos_sin_profe.append(f"{course.name} (Grupo {g.code})")

        if cursos_sin_profe:
            self.stdout.write(self.style.ERROR(f"❌ IMPOSIBLE RESOLVER: Hay {len(cursos_sin_profe)} grupos sin docentes elegibles."))
            self.stdout.write("Ejemplos: " + ", ".join(cursos_sin_profe[:3]))
            self.stdout.write("SOLUCIÓN: Agrega docentes o quita el veto 'nula' en preferencias.")
        else:
            self.stdout.write(self.style.SUCCESS("✅ Todos los grupos tienen al menos un docente candidato."))

        # --- 3. CHEQUEO DE LABORATORIOS (Causa #2 de fallos) ---
        self.stdout.write("\n--- 2. VERIFICACIÓN DE AULAS VS LABS ---")
        num_aulas = Room.objects.filter(room_type='aula').count()
        num_labs = Room.objects.filter(room_type='laboratorio').count()
        
        if num_aulas == 0 and num_labs == 0:
            self.stdout.write(self.style.ERROR("❌ CRÍTICO: No hay Rooms creados."))
            return

        demand_lab_hours = 0
        for g in groups:
            c = g.course_offering.course
            if c.requires_lab:
                demand_lab_hours += c.practical_hours # Práctica obligatoria en Lab
                # Si teoría es flexible, no cuenta como demanda dura, pero suma.

        # Capacidad semanal de 1 sala (aprox 100 horas según tu config)
        capacidad_sala_semanal = 100 
        capacidad_total_labs = num_labs * capacidad_sala_semanal
        
        print(f"Total Labs: {num_labs} | Capacidad Aprox: {capacidad_total_labs} horas")
        print(f"Demanda Labs: {demand_lab_hours} horas")
        
        if demand_lab_hours > capacidad_total_labs:
             self.stdout.write(self.style.ERROR(f"❌ SOBRECARGA DE LABORATORIO: Pides {demand_lab_hours} horas pero solo tienes {capacidad_total_labs} horas disponibles."))
        elif num_labs == 0 and demand_lab_hours > 0:
             self.stdout.write(self.style.ERROR(f"❌ CRÍTICO: Hay cursos que piden Laboratorio pero tienes 0 Laboratorios creados."))
        else:
             self.stdout.write(self.style.SUCCESS("✅ La demanda de laboratorios parece sostenible."))

        # --- 4. CHEQUEO DE CICLOS (Causa #3 de fallos - El asesino silencioso) ---
        self.stdout.write("\n--- 3. VERIFICACIÓN DE CONGESTIÓN POR CICLO ---")
        # Agrupar horas por ciclo
        ciclos_horas = {} # {ciclo: horas_totales}
        
        for g in groups:
            c = g.course_offering.course
            horas_curso = c.theoretical_hours + c.practical_hours
            if c.cycle not in ciclos_horas:
                ciclos_horas[c.cycle] = 0
            ciclos_horas[c.cycle] += horas_curso
            
        horas_semana_disponibles = 17 * 6 # 102 horas (aprox tu config)
        
        for ciclo, horas in ciclos_horas.items():
            percentage = (horas / horas_semana_disponibles) * 100
            msg = f"Ciclo {ciclo}: Requiere {horas} horas lineales (Semana tiene {horas_semana_disponibles})"
            
            if horas > horas_semana_disponibles:
                self.stdout.write(self.style.ERROR(f"❌ IMPOSIBLE CICLO {ciclo}: {msg}"))
                self.stdout.write("SOLUCIÓN: Tienes demasiados cursos en el mismo ciclo. Los alumnos no pueden clonarse.")
            elif percentage > 80:
                self.stdout.write(self.style.WARNING(f"⚠️ RIESGO CICLO {ciclo}: {msg} (Muy ajustado)"))
            else:
                self.stdout.write(f"✅ Ciclo {ciclo}: {horas} horas (Ok)")

        self.stdout.write("\n--- FIN DEL DIAGNÓSTICO ---")