# algorithms.py
import networkx as nx
from geopy.distance import geodesic

def construir_grafo(embalses_df, puntos_criticos, max_distancia=100, max_embalses=5):
    """
    Construye un grafo donde los nodos son embalses y puntos críticos.
    Conecta un punto crítico solo con los embalses más cercanos dentro de una distancia máxima.

    :param embalses_df: DataFrame con datos de embalses
    :param puntos_criticos: Lista de diccionarios con datos de puntos críticos
    :param max_distancia: Distancia máxima en km para conectar embalses
    :param max_embalses: Número máximo de embalses a conectar por punto crítico
    :return: Grafo de NetworkX
    """
    print("Iniciando la construcción del grafo optimizado...")
    G = nx.Graph()

    # Añadir nodos de embalses
    for _, row in embalses_df.iterrows():
        G.add_node(row['Nombre de la Presa'], pos=(row['Latitud'], row['Longitud']), tipo='embalse')

    # Añadir nodos de puntos críticos
    for punto in puntos_criticos:
        G.add_node(punto['ID'], pos=(punto['Latitud'], punto['Longitud']), tipo='punto_critico')

    # Conectar cada punto crítico con los embalses más cercanos dentro de la distancia máxima
    for punto in puntos_criticos:
        punto_coord = (punto['Latitud'], punto['Longitud'])
        embalses_filtrados = embalses_df.copy()
        embalses_filtrados['Distancia'] = embalses_filtrados.apply(
            lambda row: geodesic(punto_coord, (row['Latitud'], row['Longitud'])).kilometers, axis=1
        )
        embalses_cercanos = embalses_filtrados[embalses_filtrados['Distancia'] <= max_distancia]
        embalses_cercanos = embalses_cercanos.nsmallest(max_embalses, 'Distancia')

        for _, embalse in embalses_cercanos.iterrows():
            distancia = embalse['Distancia']
            G.add_edge(punto['ID'], embalse['Nombre de la Presa'], weight=distancia)
            print(f"Conectado {punto['ID']} con {embalse['Nombre de la Presa']} a {distancia:.2f} km")

    print("Grafo optimizado construido.")
    return G

def calcular_rutas_optimas(G, punto_lat, punto_lon):
    """
    Calcula las rutas óptimas desde un punto crítico a todos los embalses conectados.

    :param G: Grafo de NetworkX
    :param punto_lat: Latitud del punto crítico
    :param punto_lon: Longitud del punto crítico
    :return: distancias y rutas óptimas
    """
    print("Ejecutando el algoritmo de Dijkstra para rutas óptimas...")

    # Encontrar el nodo correspondiente al punto crítico
    punto_id = None
    for node, data in G.nodes(data=True):
        if data['pos'] == (punto_lat, punto_lon) and data['tipo'] == 'punto_critico':
            punto_id = node
            break

    if punto_id is None:
        print("Punto crítico no encontrado en el grafo.")
        return {}, []

    # Calcular rutas utilizando Dijkstra
    distancias, rutas = nx.single_source_dijkstra(G, punto_id, weight='weight')

    print("Algoritmo completado.")

    # Preparar los datos de las rutas
    rutas_optimas = []
    for destino in G.nodes():
        if G.nodes[destino]['tipo'] == 'embalse' and destino in rutas:
            ruta_coords = []
            for nodo in rutas[destino]:
                lat, lon = G.nodes[nodo]['pos']
                ruta_coords.append([lat, lon])
            rutas_optimas.append(ruta_coords)

    return distancias, rutas_optimas
