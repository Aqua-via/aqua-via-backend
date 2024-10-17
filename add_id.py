import pandas as pd
import os

def agregar_id_a_puntos_criticos(csv_path):
    # Verificar si el archivo existe
    if not os.path.exists(csv_path):
        print(f"El archivo {csv_path} no existe.")
        return

    # Cargar el CSV existente
    puntos_df = pd.read_csv(csv_path)

    # Verificar si 'ID' existe
    if 'ID' not in puntos_df.columns:
        puntos_df.reset_index(inplace=True)  # Resetea el índice para crear un contador
        puntos_df.rename(columns={'index': 'ID'}, inplace=True)
        puntos_df['ID'] = puntos_df['ID'] + 1  # Comienza el ID en 1 en lugar de 0

        # Guardar el CSV actualizado
        puntos_df.to_csv(csv_path, index=False)
        print("Columna 'ID' agregada exitosamente.")
    else:
        print("La columna 'ID' ya existe.")

if __name__ == "__main__":
    csv_path = os.path.join('data', 'puntos_criticos.csv')
    agregar_id_a_puntos_criticos(csv_path)
