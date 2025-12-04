from django.core.management.base import BaseCommand
from api.scheduler import OptimizationScheduler

class Command(BaseCommand):
    help = 'Genera el horario automático usando OR-Tools'

    def handle(self, *args, **options):
        self.stdout.write("⏳ Iniciando proceso de optimización...")
        
        try:
            scheduler = OptimizationScheduler()
            self.stdout.write(f"📅 Periodo detectado: {scheduler.period}")
            
            success = scheduler.solve()
            
            if success:
                self.stdout.write(self.style.SUCCESS("✅ Horario generado y guardado correctamente."))
            else:
                self.stdout.write(self.style.WARNING("⚠️ No se encontró solución factible."))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))