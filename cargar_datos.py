import os
import django
import pandas as pd
import glob

# 1. Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sis_Hospital_project.settings')
django.setup()

from hospital.models import EnfermedadCIE10

def importar_cie10():
    # Buscamos cualquier archivo que empiece con 'CIE-10' y termine en '.xlsx'
    archivos = glob.glob("CIE-10*.xlsx")
    
    if not archivos:
        print("❌ ERROR: No se encontró ningún archivo que empiece con 'CIE-10' en esta carpeta.")
        print(f"Directorio actual: {os.getcwd()}")
        print("Archivos encontrados en la carpeta:", os.listdir())
        return

    archivo_excel = archivos[0] # Toma el primero que encuentre
    print(f"✅ Archivo encontrado: {archivo_excel}")
    
    try:
        print("Leyendo datos... (esto puede tardar un poco)")
        df = pd.read_excel(archivo_excel)
        
        # Limpiamos la tabla antes de cargar para no duplicar si falló antes
        # Descomenta la siguiente línea si quieres borrar lo que haya antes:
        # EnfermedadCIE10.objects.all().delete()

        enfermedades_para_guardar = []
        for index, fila in df.iterrows():
            enfermedades_para_guardar.append(EnfermedadCIE10(
                codigo=str(fila['CIE_ALFA']).strip(),
                descripcion=str(fila['CIE_DESCRIPCION']).strip()
            ))
        
        print(f"Insertando {len(enfermedades_para_guardar)} registros en la base de datos...")
        EnfermedadCIE10.objects.bulk_create(enfermedades_para_guardar, ignore_conflicts=True)
        print("🚀 ¡EXITO TOTAL! El catálogo CIE-10 ya está en tu sistema.")

    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    importar_cie10()