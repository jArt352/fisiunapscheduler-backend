import sys
import os

# Asegura que el directorio raíz del proyecto esté en sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from api.utils.scheduler import AlgorithmScheduler

if __name__ == "__main__":
    scheduler = AlgorithmScheduler()  # Usa el periodo actual automáticamente
    resultado = scheduler.generate()
    print("Resultado de la generación de horarios:")
    print(resultado)

    # Guardar cursos/grupos no asignados y motivos en un txt
    output_path = "no_asignados.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Cursos/Grupos NO asignados:\n")
        for error in resultado.get("errors", []):
            f.write(f"{error}\n")
        f.write("\nMotivos detallados:\n")
        for diag in resultado.get("diagnostics", []):
            f.write(f"{diag}\n")
    print(f"Resumen guardado en: {os.path.abspath(output_path)}")
