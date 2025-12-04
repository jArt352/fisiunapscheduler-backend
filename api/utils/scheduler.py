import random
from datetime import time, datetime, timedelta
from django.db import transaction
from django.db.models import Q

# Ajusta el import según el nombre de tu app
from api.models import (
    AcademicPeriod, CourseGroup, Schedule, Room, Teacher, 
    TeacherUnavailability, CourseTeacherPreference, GeneralScheduleConfig,
    CourseDayPreference, CourseSessionPolicy
)

class AlgorithmScheduler:
    def __init__(self, period_id=None):
        from django.utils import timezone
        if period_id is not None:
            self.period = AcademicPeriod.objects.get(pk=period_id)
        else:
            now = timezone.now()
            self.period = AcademicPeriod.objects.filter(
                start_schedule_creation__lte=now,
                end_schedule_creation__gte=now
            ).order_by('-start_schedule_creation').first()
            if not self.period:
                raise ValueError("No hay un periodo académico activo para la creación de horarios.")
        # Traemos datos optimizados con select_related para evitar N+1 queries
        self.groups = CourseGroup.objects.filter(
            course_offering__academic_period=self.period
        ).select_related(
            'course_offering__course', 
            'course_offering__course__session_policy'
        )
        
        # --- MEMORIA RAM DE OCUPACIÓN (Para velocidad) ---
        # Estructura: set((id_entidad, dia_int, hora_int))
        self.teacher_occupied = set()
        self.room_occupied = set()
        self.cycle_occupied = set()  # Evita cruces de alumnos del mismo ciclo
        
        # --- CONFIGURACIÓN DE TIEMPO ---
        self.days_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
        self.days_indices = [0, 1, 2, 3, 4, 5] # Lunes a Sábado
        self.time_slots = self._load_time_slots() # Lista de enteros [7, 8, ..., 22]

    def _load_time_slots(self):
        """Genera el rango de horas operativas basado en GeneralScheduleConfig"""
        config = GeneralScheduleConfig.objects.first()
        start = config.start_time.hour if config else 7
        end = config.end_time.hour if config else 22
        return list(range(start, end)) # range no incluye el último número, ajusta si necesario

    def prepare_environment(self):
        """Limpia horarios previos y carga restricciones duras"""
        # 1. Limpiar horario actual del periodo
        Schedule.objects.filter(group__in=self.groups).delete()
        
        # 2. Cargar Indisponibilidad de Docentes (TeacherUnavailability)
        unavails = TeacherUnavailability.objects.all()
        for u in unavails:
            day_idx = self._get_day_index(u.day)
            if day_idx is not None:
                # Marcar cada hora del rango como ocupada
                h_start = u.start_time.hour
                h_end = u.end_time.hour
                for h in range(h_start, h_end):
                    self.teacher_occupied.add((u.teacher.id, day_idx, h))

    def _get_day_index(self, day_code):
        reverse_map = {v: k for k, v in self.days_map.items()}
        return reverse_map.get(day_code)

    def generate(self):
        from collections import defaultdict
        with transaction.atomic():
            self.prepare_environment()
            # Agrupar grupos por ciclo
            groups_by_cycle = defaultdict(list)
            for group in self.groups:
                cycle = group.course_offering.course.cycle
                groups_by_cycle[cycle].append(group)
            # Procesar de mayor a menor ciclo
            sorted_cycles = sorted(groups_by_cycle.keys(), reverse=True)
            report = {'created': [], 'errors': [], 'diagnostics': []}
            self._vacant_slots = []  # Para guardar espacios vacíos
            for cycle in sorted_cycles:
                # Ordenar dentro del ciclo por tamaño de bloque (opcional, como antes)
                cycle_groups = sorted(
                    groups_by_cycle[cycle],
                    key=lambda g: g.course_offering.course.theoretical_hours + g.course_offering.course.practical_hours,
                    reverse=True
                )
                for group in cycle_groups:
                    success, reason = self._process_group(group, diagnostics=True)
                    if success:
                        report['created'].append(str(group))
                    else:
                        report['errors'].append(f"No se pudo agendar: {group}")
                        report['diagnostics'].append(f"{group}: {reason}")
            # Al final, imprimir espacios vacíos
            report['vacant_slots'] = self._get_vacant_slots()
            return report

    def _process_group(self, group, diagnostics=False):
        """Decide la estrategia según la política de sesión (Juntas o Separadas). Siempre el mismo docente para todas las horas del grupo."""
        course = group.course_offering.course
        try:
            policy = course.session_policy.mode
        except:
            policy = 'separadas'
        h_teo = course.theoretical_hours
        h_prac = course.practical_hours
        reason = ''
        # Si no requiere docente, usar lógica original
        if not course.requires_teacher:
            if policy == 'juntas':
                total_duration = h_teo + h_prac
                if total_duration == 0:
                    return True, ''
                structure = []
                if h_teo > 0: structure.append(('teoria', h_teo))
                if h_prac > 0: structure.append(('practica', h_prac))
                # Forzar que el docente sea None
                ok, reason = self._find_best_slot_and_assign(group, total_duration, structure, diagnostics=diagnostics, force_teacher=None)
                return ok, reason
            else:
                ok_teo, reason_teo = True, ''
                ok_prac, reason_prac = True, ''
                if h_teo > 0:
                    ok_teo, reason_teo = self._find_best_slot_and_assign(group, h_teo, [('teoria', h_teo)], diagnostics=diagnostics, force_teacher=None)
                if h_prac > 0:
                    ok_prac, reason_prac = self._find_best_slot_and_assign(group, h_prac, [('practica', h_prac)], diagnostics=diagnostics, force_teacher=None)
                ok = ok_teo and ok_prac
                reason = f"Teoría: {reason_teo}; Práctica: {reason_prac}" if not ok else ''
                return ok, reason
        # Si requiere docente, buscar un docente que pueda cubrir todas las horas (teoría y práctica)
        # 1. Buscar solo con docentes preferidos
        teacher_candidates = self._get_teacher_candidates(course)
        if not teacher_candidates:
            # No hay docentes preferidos para este curso
            return False, "No hay docentes preferidos asignados para este curso"
        
        for teacher in teacher_candidates:
            if teacher is None:
                continue
            # Intentar agendar teoría y práctica con el mismo docente
            ok_teo, reason_teo = True, ''
            ok_prac, reason_prac = True, ''
            # Guardar ocupación temporal para rollback si falla
            temp_teacher_occupied = set()
            temp_room_occupied = set()
            temp_cycle_occupied = set()
            # Teoría
            if h_teo > 0:
                ok_teo, reason_teo = self._find_best_slot_and_assign(group, h_teo, [('teoria', h_teo)], diagnostics=diagnostics, force_teacher=teacher, temp_occupied=(temp_teacher_occupied, temp_room_occupied, temp_cycle_occupied))
            # Práctica
            if h_prac > 0:
                ok_prac, reason_prac = self._find_best_slot_and_assign(group, h_prac, [('practica', h_prac)], diagnostics=diagnostics, force_teacher=teacher, temp_occupied=(temp_teacher_occupied, temp_room_occupied, temp_cycle_occupied))
            ok = ok_teo and ok_prac
            if ok:
                # Si ambos bloques se pudieron agendar, registrar ocupación definitiva
                self.teacher_occupied.update(temp_teacher_occupied)
                self.room_occupied.update(temp_room_occupied)
                self.cycle_occupied.update(temp_cycle_occupied)
                return True, ''
        # Si no se pudo con ningún docente preferido
        reason = f"No hay docente preferido disponible. Últimos motivos: Teoría: {reason_teo}; Práctica: {reason_prac}"
        return False, reason

    def _find_best_slot_and_assign(self, group, total_duration, structure, diagnostics=False, force_teacher=None, temp_occupied=None):
        """
        Núcleo del Algoritmo:
        1. Intenta agendar con docentes preferidos y días preferidos.
        2. Si no encuentra con días preferidos, intenta con cualquier día disponible.
        Si diagnostics=True, retorna (ok, reason) con el motivo del fallo.
        """
        course = group.course_offering.course
        # Obtener docentes candidatos
        candidates_teachers = self._get_teacher_candidates(course) if force_teacher is None else [force_teacher]
        best_proposal = None
        best_score = -float('inf')
        fail_reasons = []
        
        def search_slots(teachers, ignore_day_preferences=False):
            nonlocal best_proposal, best_score, fail_reasons
            for day in self.days_indices:
                score_day = self._score_day(course, day) if not ignore_day_preferences else 0
                for start_h in self.time_slots:
                        if start_h + total_duration > self.time_slots[-1] + 1:
                            continue
                        hours_range = list(range(start_h, start_h + total_duration))
                        # Si temp_occupied está presente, usarlo para simulación
                        teacher_occ = self.teacher_occupied.copy()
                        room_occ = self.room_occupied.copy()
                        cycle_occ = self.cycle_occupied.copy()
                        if temp_occupied:
                            teacher_occ.update(temp_occupied[0])
                            room_occ.update(temp_occupied[1])
                            cycle_occ.update(temp_occupied[2])
                        if any((course.cycle, day, h) in cycle_occ for h in hours_range):
                            fail_reasons.append(f"Cruce de ciclo en día {day}, horas {hours_range}")
                            continue
                        score_shift = self._score_shift(course, start_h)
                        for teacher in teachers:
                            if teacher is not None:
                                if any((teacher.id, day, h) in teacher_occ for h in hours_range):
                                    fail_reasons.append(f"Docente ocupado {teacher} en día {day}, horas {hours_range}")
                                    continue
                            score_teacher = self._score_teacher(course, teacher)
                            room_allocation = []
                            current_offset = 0
                            possible_allocation = True
                            for s_type, s_dur in structure:
                                req_type = 'laboratorio' if s_type == 'practica' else 'aula'
                                sub_range = hours_range[current_offset : current_offset + s_dur]
                                found_room = self._find_free_room(req_type, day, sub_range, course)
                                if found_room:
                                    room_allocation.append({
                                        'room': found_room,
                                        'type': s_type,
                                        'start': start_h + current_offset,
                                        'duration': s_dur
                                    })
                                    current_offset += s_dur
                                else:
                                    possible_allocation = False
                                    fail_reasons.append(f"No hay aula/lab libre tipo {req_type} día {day}, horas {sub_range}")
                                    break
                            if possible_allocation:
                                total_score = score_day + score_shift + score_teacher + random.uniform(0, 0.5)
                                if total_score > best_score:
                                    best_score = total_score
                                    best_proposal = {
                                        'day': day,
                                        'teacher': teacher,
                                        'allocation': room_allocation
                                    }
                                    # Si temp_occupied está presente, registrar ocupación temporal
                                    if temp_occupied is not None:
                                        for h in hours_range:
                                            if teacher and course.requires_teacher:
                                                temp_occupied[0].add((teacher.id, day, h))
                                            for alloc in room_allocation:
                                                if alloc['room'] and (course.requires_room or course.requires_lab):
                                                    temp_occupied[1].add((alloc['room'].id, day, h))
                                            temp_occupied[2].add((course.cycle, day, h))
        
        # 1. Intentar con días preferidos
        search_slots(candidates_teachers, ignore_day_preferences=False)
        # 2. Si no hay propuesta, relajar: usar cualquier día disponible
        if not best_proposal:
            search_slots(candidates_teachers, ignore_day_preferences=True)
        if best_proposal:
            self._commit_schedule(group, best_proposal)
            return (True, '') if diagnostics else True
        reason = '; '.join(set(fail_reasons)) if diagnostics else ''
        return (False, reason) if diagnostics else False

    def _get_vacant_slots(self):
        """Devuelve todos los espacios (día, hora, aula) que quedaron vacíos y no fueron usados."""
        vacant = []
        all_rooms = Room.objects.all()
        for day in self.days_indices:
            for h in self.time_slots:
                for room in all_rooms:
                    if not (room.id, day, h) in self.room_occupied:
                        vacant.append({'room': str(room), 'day': day, 'hour': h})
        return vacant

    def _find_free_room(self, room_type, day, hour_list, course, group=None):
        """Busca la primera aula/lab disponible que cumpla el tipo y capacidad real"""
        # Si el curso no requiere aula/lab según el tipo, retorna None
        if room_type == 'aula' and not course.requires_room:
            return None
        if room_type == 'laboratorio' and not course.requires_lab:
            return None
        # Capacidad real: usa la del grupo/oferta si existe
        min_capacity = 1
        if group and hasattr(group, 'capacity') and group.capacity:
            min_capacity = group.capacity
        elif hasattr(course, 'capacity') and course.capacity:
            min_capacity = course.capacity
        candidates = Room.objects.filter(room_type=room_type, capacity__gte=min_capacity)
        for room in candidates:
            if not any((room.id, day, h) in self.room_occupied for h in hour_list):
                return room
        return None

    def _commit_schedule(self, group, proposal):
        """Guarda en BD y actualiza memoria"""
        day = proposal['day']
        teacher = proposal['teacher']
        course = group.course_offering.course
        for alloc in proposal['allocation']:
            start_t = time(alloc['start'], 0)
            end_t = time(alloc['start'] + alloc['duration'], 0)
            # Si el curso no requiere aula ni laboratorio, no asignar room
            room_to_assign = alloc['room'] if (course.requires_room or course.requires_lab) else None
            Schedule.objects.create(
                course=course,
                group=group,
                teacher=teacher if course.requires_teacher else None,
                day_of_week=day,
                room=room_to_assign,
                start_time=start_t,
                end_time=end_t,
                session_type=alloc['type']
            )
            # Actualizar Sets de Ocupación
            rng = range(alloc['start'], alloc['start'] + alloc['duration'])
            if teacher and course.requires_teacher:
                for h in rng:
                    self.teacher_occupied.add((teacher.id, day, h))
            if (room_to_assign and (course.requires_room or course.requires_lab)):
                for h in rng:
                    self.room_occupied.add((room_to_assign.id, day, h))
            for h in rng:
                self.cycle_occupied.add((course.cycle, day, h))

    # --- HELPERS DE PUNTUACIÓN (SCORING) ---

    def _get_teacher_candidates(self, course):
        # Si el curso no requiere docente, devolver [None]
        if not course.requires_teacher:
            return [None]
        # Obtener todos los docentes que tienen preferencia para este curso
        prefs = CourseTeacherPreference.objects.filter(course=course).select_related('teacher')
        if prefs.exists():
            return [p.teacher for p in prefs]
        # Si no hay preferencias definidas, retornar lista vacía (no asignar docente)
        return []

    def _score_day(self, course, day_idx):
        """Si el curso tiene preferencia de día, retorna puntos positivos; si no tiene preferencia para ese día, retorna 0."""
        day_str = self.days_map[day_idx]
        try:
            course.day_preferences.get(day=day_str)
            return 20  # Día preferido
        except CourseDayPreference.DoesNotExist:
            return 0  # No es preferido, pero permitido

    def _score_shift(self, course, start_h):
        """Puntuación por turno - retorna 0 ya que no hay preferencias de turno definidas."""
        return 0

    def _score_teacher(self, course, teacher):
        """Si el docente está en las preferencias del curso, retorna puntos positivos; si no, retorna 0."""
        if not teacher:
            return 0
        try:
            course.teacher_preferences.get(teacher=teacher)
            return 40  # Docente preferido
        except CourseTeacherPreference.DoesNotExist:
            return 0  # No preferido