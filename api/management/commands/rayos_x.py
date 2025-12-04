from django.core.management.base import BaseCommand
from django.db.models import Sum
from api.models import CourseGroup, GeneralScheduleConfig, AcademicPeriod
from django.utils import timezone

class Command(BaseCommand):
    help = 'Radiografía matemática de los ciclos y turnos'

    def handle(self, *args, **options):
        # 1. Detectar Periodo
        now = timezone.now()
        period = AcademicPeriod.objects.filter(
            start_schedule_creation__lte=now, end_schedule_creation__gte=now
        ).order_by('-start_schedule_creation').first()
        
        if not period:
            print("❌ No hay periodo activo.")
            return

        groups = CourseGroup.objects.filter(course_offering__academic_period=period)
        
        # 2. Configuración de Turnos (Tus reglas de negocio)
        # Asumimos Lunes a Sábado (6 días)
        DIAS_SEMANA = 6 
        
        # Definición de horas reales por turno (Ajusta esto si tus horas son diferentes)
        # Mañana: 07:00 - 13:00 = 6 horas/día
        HORAS_MANANA_DIA = 6 
        # Tarde: 13:00 - 18:00 = 5 horas/día
        HORAS_TARDE_DIA = 5
        # Noche: 18:00 - 22:00 = 4 horas/día (¡OJO AQUÍ!)
        HORAS_NOCHE_DIA = 4 

        CAPACIDAD_SEMANAL_MANANA = HORAS_MANANA_DIA * DIAS_SEMANA # 36 horas
        CAPACIDAD_SEMANAL_TARDE = HORAS_TARDE_DIA * DIAS_SEMANA   # 30 horas
        CAPACIDAD_SEMANAL_NOCHE = HORAS_NOCHE_DIA * DIAS_SEMANA   # 24 horas

        print(f"\n📊 CAPACIDAD MÁXIMA TEÓRICA (por alumno/ciclo):")
        print(f"   🌞 Mañana: {CAPACIDAD_SEMANAL_MANANA} horas/semana")
        print(f"   uws Tarde:  {CAPACIDAD_SEMANAL_TARDE} horas/semana")
        print(f"   🌚 Noche:  {CAPACIDAD_SEMANAL_NOCHE} horas/semana (¡El turno más peligroso!)")
        print("="*60)

        # 3. Análisis por Ciclo
        # Agrupamos horas requeridas por ciclo
        analisis_ciclos = {} # {ciclo: horas_totales}
        
        for g in groups:
            c = g.course_offering.course
            horas = c.theoretical_hours + c.practical_hours
            if c.cycle not in analisis_ciclos:
                analisis_ciclos[c.cycle] = 0
            analisis_ciclos[c.cycle] += horas

        # 4. Reporte
        print(f"{'CICLO':<6} | {'TURNO IDEAL':<10} | {'DEMANDA':<8} | {'OFERTA':<8} | {'ESTADO'}")
        print("-" * 60)

        conflictos = False

        for ciclo in sorted(analisis_ciclos.keys()):
            horas_necesarias = analisis_ciclos[ciclo]
            
            # Determinar turno y capacidad según tus reglas
            turno = "???"
            oferta = 0
            
            if 1 <= ciclo <= 4:
                turno = "Mañana"
                oferta = CAPACIDAD_SEMANAL_MANANA
            elif 5 <= ciclo <= 7:
                turno = "Tarde"
                oferta = CAPACIDAD_SEMANAL_TARDE
            elif ciclo >= 8:
                turno = "Noche"
                oferta = CAPACIDAD_SEMANAL_NOCHE
            
            # Análisis
            diff = oferta - horas_necesarias
            estado = "✅ OK"
            
            if diff < 0:
                estado = f"❌ IMPOSIBLE (Faltan {abs(diff)}h)"
                conflictos = True
            elif diff < 5:
                estado = "⚠️ AL LÍMITE"
            
            print(f"{ciclo:<6} | {turno:<10} | {horas_necesarias:<8} | {oferta:<8} | {estado}")

        print("="*60)
        if conflictos:
            print("\n🚨 CONCLUSIÓN: El horario falla porque MATEMÁTICAMENTE no caben las horas.")
            print("   Ejemplo: Si el Ciclo 8 pide 28 horas, y el turno noche solo tiene 24 horas (4h x 6 días),")
            print("   JAMÁS encontrarás una solución, no importa qué algoritmo uses.")
            print("\n💡 SOLUCIONES:")
            print("   1. Mover cursos de Noche a Tarde/Sábado.")
            print("   2. Aumentar horas al día (ej. hasta las 23:00).")
            print("   3. Reducir horas de los cursos.")
        else:
            print("\n✅ CONCLUSIÓN: Los ciclos caben en sus turnos.")
            print("   Si el scheduler sigue fallando, el problema son los DOCENTES (Solapamiento).")