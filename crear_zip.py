#!/usr/bin/env python3
"""
Script para crear un archivo ZIP con todos los archivos del proyecto
"""

import zipfile
import os
import tempfile

# Definir rutas
project_folder = r"c:\Users\adria\Documents\Tec\7mo semestre\M3"
temp_base = tempfile.gettempdir()
model_path = os.path.join(temp_base, "breast_cancer_model.pkl")
zip_path = os.path.join(temp_base, "clasificador_tumor.zip")

print("="*60)
print("CREANDO ARCHIVO ZIP")
print("="*60)
print(f"Ubicación de destino: {zip_path}\n")

# Archivos a incluir
files_to_zip = [
    ("clasificador_tumor_entrenamiento.ipynb", os.path.join(project_folder, "clasificador_tumor_entrenamiento.ipynb")),
    ("train_model.py", os.path.join(project_folder, "train_model.py")),
    ("run_model.py", os.path.join(project_folder, "run_model.py")),
    ("breast_cancer_model.pkl", model_path),
]

try:
    # Crear el ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for archivo_nombre, archivo_ruta in files_to_zip:
            if os.path.exists(archivo_ruta):
                tamaño = os.path.getsize(archivo_ruta)
                print(f"  ✓ Añadiendo: {archivo_nombre} ({tamaño:,} bytes)")
                zipf.write(archivo_ruta, arcname=archivo_nombre)
            else:
                print(f"  ✗ No encontrado: {archivo_nombre}")
    
    # Verificar tamaño del ZIP
    zip_size = os.path.getsize(zip_path)
    print(f"\n✓ Archivo ZIP creado exitosamente")
    print(f"  Ubicación: {zip_path}")
    print(f"  Tamaño total: {zip_size:,} bytes")
    
    # Listar contenido del ZIP
    print(f"\nContenido del archivo ZIP:")
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        for info in zipf.filelist:
            print(f"  - {info.filename} ({info.file_size:,} bytes)")
    
    print("\n" + "="*60)
    print("✓ ENTREGA COMPLETADA")
    print("="*60)
    
except Exception as e:
    print(f"✗ Error al crear el ZIP: {e}")
    import traceback
    traceback.print_exc()
