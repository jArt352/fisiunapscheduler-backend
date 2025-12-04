from django.core.management.base import BaseCommand
from api.models import Teacher, TeacherUnavailability, GeneralScheduleConfig
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Revisa si los docentes tienen tiempo suficiente'

    def handle(self, *args, **options):
        self.stdout.write("🕵️ ANALIZANDO DISPONIBILIDAD DE DOCENTES...")
        
        teachers = Teacher.objects.all()
        config = GeneralScheduleConfig.objects.first()
        
        start_h = config.start_time.hour if config else 7
        end_h = config.end_time.hour if config else 22
        horas_totales_semana = (end_h - start_h) * 6 # Asumiendo 6 días
        
        print(f"Horas teóricas por semana: {horas_totales_semana}")
        print(f"{'DOCENTE':<30} | {'INDISPONIBILIDAD':<15} | {'LIBRE':<10}")
        print("-" * 60)
        
        horas_libres_totales_plantel = 0
        
        for t in teachers:
            # Calcular horas ocupadas
            horas_bloqueadas = 0
            for u in t.unavailabilities.all():
                inicio = u.start_time.hour + (u.start_time.minute/60)
                fin = u.end_time.hour + (u.end_time.minute/60)
                horas_bloqueadas += (fin - inicio)
            
            horas_libres = max(0, horas_totales_semana - horas_bloqueadas)
            horas_libres_totales_plantel += horas_libres
            
            # Alerta visual si tiene muy poco tiempo
            status = f"{horas_libres:.1f} h"
            if horas_libres < 10:
                status += " ⚠️ MUY POCO"
            
            print(f"{str(t.person):<30} | {horas_bloqueadas:<15.1f} | {status}")

        print("-" * 60)
        print(f"Total horas hombre disponibles: {horas_libres_totales_plantel:.1f}")