from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
from algorithms import construir_grafo, calcular_rutas_optimas
import utm

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aquí'  # Reemplaza con una clave secreta segura
app.config['DATA_FOLDER'] = 'data/'

# Cargar los datos al iniciar la aplicación
def cargar_datos_estaticos():
    embalses_path = os.path.join(app.config['DATA_FOLDER'], 'embalses.csv')
    puntos_path = os.path.join(app.config['DATA_FOLDER'], 'puntos_criticos.csv')

    # Verificar si los archivos existen
    if not os.path.exists(embalses_path):
        print(f"El archivo {embalses_path} no existe.")
        exit(1)
    if not os.path.exists(puntos_path):
        print(f"El archivo {puntos_path} no existe.")
        exit(1)

    # Leer los archivos CSV
    embalses_df = pd.read_csv(embalses_path)
    puntos_df = pd.read_csv(puntos_path)

    # Verificar y agregar la columna 'ID' si no existe (si no usas el script separado)
    if 'ID' not in puntos_df.columns:
        puntos_df.reset_index(inplace=True)  # Resetea el índice para crear un contador
        puntos_df.rename(columns={'index': 'ID'}, inplace=True)
        puntos_df['ID'] = puntos_df['ID'] + 1  # Comienza el ID en 1 en lugar de 0

        # Guardar el CSV actualizado
        puntos_df.to_csv(puntos_path, index=False)
        print("Columna 'ID' agregada exitosamente.")
    else:
        print("La columna 'ID' ya existe.")

    # Verificar tipos de datos
    print("Tipos de datos en puntos_df antes de la conversión:")
    print(puntos_df.dtypes)

    # Convertir coordenadas UTM a Latitud y Longitud usando la librería utm
    def convertir_coordenadas(easting, northing, zona):
        try:
            lat, lon = utm.to_latlon(easting, northing, zona, northern=False)  # Asumiendo hemisferio sur
            #print(f"Convertido UTM ({easting}, {northing}, Zona {zona}) a Lat: {lat}, Lon: {lon}")
            return lat, lon
        except Exception as e:
            print(f"Error al convertir coordenadas: {e}")
            return None, None

    # Convertir coordenadas en puntos críticos
    puntos_df[['Latitud', 'Longitud']] = puntos_df.apply(
        lambda row: convertir_coordenadas(row['Este (Inicial)'], row['Norte (Inicial)'], row['Zona']),
        axis=1, result_type='expand'
    )

    # Eliminar puntos con coordenadas inválidas
    puntos_df.dropna(subset=['Latitud', 'Longitud'], inplace=True)

    # Asegurar que 'ID' es de tipo int
    puntos_df['ID'] = puntos_df['ID'].astype(int)

    # Verificar tipos de datos después de la conversión
    print("Tipos de datos en puntos_df después de la conversión:")
    print(puntos_df.dtypes)

    # Imprimir las primeras filas para verificar
    print("Primeras filas de puntos_df:")
    print(puntos_df.head())

    return embalses_df, puntos_df

# Cargar los datos una vez al iniciar
embalses_df, puntos_df = cargar_datos_estaticos()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analisis', methods=['GET', 'POST'])
def analisis():
    if request.method == 'POST':
        try:
            # Obtener filtros del formulario
            departamento = request.form.get('departamento')
            provincia = request.form.get('provincia')
            distrito = request.form.get('distrito')
            punto_id = request.form.get('punto_id')

            # Validar que 'punto_id' no esté vacío
            if not punto_id:
                flash('No se ha seleccionado ningún punto crítico.')
                return redirect(url_for('analisis'))

            # Convertir 'punto_id' a int si es necesario
            try:
                punto_id = int(punto_id)
            except ValueError:
                flash('ID de punto crítico inválido.')
                return redirect(url_for('analisis'))

            # Filtrar puntos críticos según los parámetros
            puntos_filtrados = puntos_df.copy()
            if departamento:
                puntos_filtrados = puntos_filtrados[puntos_filtrados['Departamento'] == departamento]
            if provincia:
                puntos_filtrados = puntos_filtrados[puntos_filtrados['Provincia'] == provincia]
            if distrito:
                puntos_filtrados = puntos_filtrados[puntos_filtrados['Distrito'] == distrito]

            # Añadir impresión para depurar
            print(f"Departamento: {departamento}, Provincia: {provincia}, Distrito: {distrito}, Punto ID: {punto_id}")
            print(f"Puntos filtrados:\n{puntos_filtrados}")

            # Verificar si el punto crítico existe
            punto = puntos_filtrados[puntos_filtrados['ID'] == punto_id]
            print(f"Punto encontrado:\n{punto}")
            if punto.empty:
                flash('Punto crítico no encontrado.')
                return redirect(url_for('analisis'))
            punto = punto.iloc[0]

            # Construir el grafo solo con embalses y el punto crítico seleccionado
            G = construir_grafo(embalses_df, [punto], max_distancia=100, max_embalses=5)  # Ajusta según sea necesario

            # Calcular rutas óptimas desde el punto crítico a todos los embalses
            distancias, rutas = calcular_rutas_optimas(G, punto['Latitud'], punto['Longitud'])

            # Preparar los datos para la plantilla
            data = {
                'embalses': embalses_df.to_dict(orient='records'),
                'punto_critico': punto.to_dict(),
                'rutas': rutas,
                'distancias': distancias,
            }

            return render_template('analisis.html', data=data)
        except Exception as e:
            print(f"Error durante el análisis: {e}")
            flash("Se produjo un error durante el análisis. Por favor, inténtalo de nuevo.")
            return redirect(url_for('analisis'))
    else:
        # Mostrar formulario de selección de punto crítico
        departamentos = puntos_df['Departamento'].unique()
        return render_template('analisis_form.html', departamentos=departamentos, puntos_df=puntos_df)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
