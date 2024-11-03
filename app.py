# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
import utm

from algorithms.mst_algorithm import construir_grafo_mst
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aquí'  # Cambia esto por una clave secreta segura
app.config['DATA_FOLDER'] = 'data/'

def cargar_datos():
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

    # Convertir 'Departamento' a mayúsculas en ambos DataFrames para estandarizar
    embalses_df['Departamento'] = embalses_df['Departamento'].str.upper()
    puntos_df['Departamento'] = puntos_df['Departamento'].str.upper()

    # Convertir coordenadas UTM a Latitud y Longitud usando la librería utm
    def convertir_coordenadas(easting, northing, zona):
        try:
            lat, lon = utm.to_latlon(easting, northing, int(zona), northern=False)  # Asumiendo hemisferio sur
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

    # Si los embalses tienen coordenadas en UTM, conviértelas también
    # Aquí asumimos que embalses_df ya tiene 'Latitud' y 'Longitud'
    # Si no, necesitarás convertirlas de manera similar a los puntos críticos

    return embalses_df, puntos_df

# Cargar los datos al iniciar la aplicación
embalses_df, puntos_df = cargar_datos()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mst', methods=['GET', 'POST'])
def mst():
    if request.method == 'POST':
        try:
            # Obtener el departamento seleccionado desde el formulario
            departamento = request.form.get('departamento')

            if not departamento:
                flash('Debes seleccionar un departamento.')
                return redirect(url_for('mst'))

            # Construir el MST para el departamento seleccionado
            mst_graph = construir_grafo_mst(embalses_df, puntos_df, departamento)

            if mst_graph is None:
                flash(f"No se puede construir un MST para el departamento {departamento}. Asegúrate de que haya al menos dos nodos.")
                return redirect(url_for('mst'))

            # Preparar datos para la visualización
            nodos = []
            for node, data in mst_graph.nodes(data=True):
                nodos.append({
                    'id': node,
                    'lat': data['pos'][0],
                    'lon': data['pos'][1],
                    'tipo': data['tipo'],
                    'nombre': data['nombre']
                })

            aristas = []
            for u, v, data in mst_graph.edges(data=True):
                aristas.append({
                    'source': u,
                    'target': v,
                    'weight': round(data['weight'], 2),  # Redondear para mejor legibilidad
                    'coords': [
                        [mst_graph.nodes[u]['pos'][0], mst_graph.nodes[u]['pos'][1]],
                        [mst_graph.nodes[v]['pos'][0], mst_graph.nodes[v]['pos'][1]]
                    ],
                    'nombre_source': mst_graph.nodes[u]['nombre'],
                    'nombre_target': mst_graph.nodes[v]['nombre']
                })

            return render_template('mst.html', nodos=nodos, aristas=aristas, departamento=departamento)
        except Exception as e:
            print(f"Error al generar el MST: {e}")
            flash("Se produjo un error al generar el MST. Por favor, inténtalo de nuevo.")
            return redirect(url_for('mst'))
    else:
        # Mostrar formulario para seleccionar departamento
        # Obtener departamentos únicos de ambos DataFrames
        departamentos_embalses = embalses_df['Departamento'].dropna().unique().tolist()
        departamentos_puntos = puntos_df['Departamento'].dropna().unique().tolist()
        departamentos = list(set(departamentos_embalses + departamentos_puntos))
        departamentos.sort()
        return render_template('mst_form.html', departamentos=departamentos)

if __name__ == '__main__':
    app.run(debug=True)