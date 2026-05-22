import pickle
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import tempfile
import os
import base64


def main():
    """
    Entrena un modelo RandomForest con el dataset de cáncer de mama
    y guarda el modelo en un archivo pickle.
    """
    # Cargar dataset
    data = load_breast_cancer()
    X = data.data
    y = data.target
    
    print("="*60)
    print("ENTRENAMIENTO DEL CLASIFICADOR DE CÁNCER DE MAMA")
    print("="*60)
    print(f"\nDataset cargado:")
    print(f"  - Número de muestras: {X.shape[0]}")
    print(f"  - Número de características: {X.shape[1]}")
    print(f"  - Clases: {data.target_names}")
    
    # Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nDatos divididos:")
    print(f"  - Entrenamiento: {X_train.shape[0]} muestras")
    print(f"  - Prueba: {X_test.shape[0]} muestras")
    
    # Entrenar modelo
    print("\nEntrenando modelo RandomForest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    print("✓ Modelo entrenado exitosamente")
    
    # Evaluar modelo
    print("\nEvaluando modelo...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nPrecisión en el conjunto de prueba: {accuracy:.4f}")
    print("\nReporte de clasificación:")
    print(classification_report(y_test, y_pred, target_names=data.target_names))
    
    # Guardar modelo en ubicación temporal primero
    print("\nGuardando modelo...")
    temp_dir = tempfile.gettempdir()
    temp_model_path = os.path.join(temp_dir, 'breast_cancer_model.pkl')
    
    with open(temp_model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Leer los bytes del modelo
    with open(temp_model_path, 'rb') as f:
        model_bytes = f.read()
    
    # Almacenar en la carpeta de trabajo
    final_path = os.path.join(os.getcwd(), 'breast_cancer_model.pkl')
    
    # Intentar guardar directamente
    try:
        with open(final_path, 'wb') as f:
            f.write(model_bytes)
        print(f"✓ Modelo guardado como 'breast_cancer_model.pkl'")
    except Exception as e:
        print(f"✓ Modelo generado en ubicación temporal: {temp_model_path}")
        print(f"  Tamaño: {len(model_bytes)} bytes")
    
    print("\n" + "="*60)
    return model_bytes


if __name__ == "__main__":
    main()
