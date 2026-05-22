import pickle
import numpy as np
import os
import tempfile


def load_model(model_path=None):
    """
    Carga el modelo entrenado desde un archivo pickle.
    
    Args:
        model_path (str): Ruta al archivo del modelo pickle.
                         Si es None, busca en ubicación por defecto.
        
    Returns:
        Modelo cargado de sklearn
    """
    if model_path is None:
        # Intentar cargar desde la carpeta de trabajo primero
        if os.path.exists('breast_cancer_model.pkl'):
            model_path = 'breast_cancer_model.pkl'
        else:
            # Si no existe, buscar en la carpeta temporal
            temp_path = os.path.join(tempfile.gettempdir(), 'breast_cancer_model.pkl')
            if os.path.exists(temp_path):
                model_path = temp_path
            else:
                raise FileNotFoundError("No se encontró el archivo del modelo")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def predict_tumor(model, features, feature_names=None):
    """
    Realiza una predicción con el modelo para una muestra.
    
    Args:
        model: Modelo entrenado
        features (list): Array de características
        feature_names (list): Nombres de las características
        
    Returns:
        dict: Predicción y probabilidades
    """
    X = np.array([features])
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    return {
        'prediction': prediction,
        'probability_benign': probabilities[0],
        'probability_malignant': probabilities[1]
    }


def print_result(sample_name, result):
    """
    Imprime los resultados de una predicción de forma formateada.
    
    Args:
        sample_name (str): Nombre de la muestra
        result (dict): Resultado de la predicción
    """
    # En el dataset de sklearn:
    # prediction=0 -> 'malignant' (maligno)
    # prediction=1 -> 'benign' (benigno)
    prediction_label = 'BENIGNO' if result['prediction'] == 1 else 'MALIGNO'
    confidence = max(result['probability_benign'], result['probability_malignant'])
    
    print(f"\n{'-'*60}")
    print(f"Muestra: {sample_name}")
    print(f"Predicción: {prediction_label}")
    print(f"Confianza: {confidence:.2%}")
    print(f"  - Probabilidad BENIGNO (clase 1): {result['probability_benign']:.4f}")
    print(f"  - Probabilidad MALIGNO (clase 0): {result['probability_malignant']:.4f}")
    print(f"{'-'*60}")


def main():
    """
    Carga el modelo y realiza predicciones con muestras de validación.
    """
    print("\n" + "="*60)
    print("VALIDACIÓN DEL MODELO DE CÁNCER DE MAMA")
    print("="*60)
    
    # Cargar modelo
    print("\nCargando modelo...")
    try:
        model = load_model()
        print("✓ Modelo cargado exitosamente")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("Por favor ejecute 'python train_model.py' primero")
        return
    
    # Muestras de validación
    sample_1_malignant = [
        17.99, 10.38, 122.80, 1001.0, 0.1184, 0.2776, 0.3001, 0.1471,
        0.2419, 0.07871, 1.095, 0.9053, 8.589, 153.4, 0.006399, 0.04904,
        0.05373, 0.01587, 0.03003, 0.006193, 25.38, 17.33, 184.60, 2019.0,
        0.1622, 0.6656, 0.7119, 0.2654, 0.4601, 0.1189
    ]
    
    sample_2_benign = [
        13.08, 15.71, 85.63, 520.0, 0.1075, 0.1270, 0.04568, 0.03110,
        0.1967, 0.06811, 0.1852, 0.7477, 1.383, 14.67, 0.004097, 0.01898,
        0.01698, 0.00649, 0.01678, 0.002425, 14.50, 20.49, 96.09, 630.5,
        0.1312, 0.2776, 0.1890, 0.07283, 0.3184, 0.08183
    ]
    
    # Hacer predicciones
    print("\nRealizando predicciones...")
    
    result_1 = predict_tumor(model, sample_1_malignant)
    print_result("Muestra 1 (Esperado: MALIGNO)", result_1)
    
    result_2 = predict_tumor(model, sample_2_benign)
    print_result("Muestra 2 (Esperado: BENIGNO)", result_2)
    
    # Resumen de validación
    print("\n" + "="*60)
    print("RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    validation_results = [
        ("Muestra 1", "MALIGNO", result_1['prediction'] == 0),  # En sklearn: 0 = malignant
        ("Muestra 2", "BENIGNO", result_2['prediction'] == 1)   # En sklearn: 1 = benign
    ]
    
    correct = sum(1 for _, _, is_correct in validation_results if is_correct)
    total = len(validation_results)
    
    for sample_name, expected, is_correct in validation_results:
        status = "✓ CORRECTO" if is_correct else "✗ INCORRECTO"
        print(f"{sample_name}: Esperado {expected} - {status}")
    
    print(f"\nAccuracy en validación: {correct}/{total} ({100*correct/total:.1f}%)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
