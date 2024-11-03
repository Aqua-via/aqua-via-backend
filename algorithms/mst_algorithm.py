# algorithms/mst_algorithm.py
import networkx as nx
from geopy.distance import geodesic

def construir_grafo_mst(embalses_df, puntos_df, departamento):
    """
    Construye un grafo completo que incluye embalses y puntos críticos dentro de un departamento,
    calcula el Árbol de Expansión Mínima y retorna el grafo MST.

    :param embalses_df: DataFrame con datos de embalses
    :param puntos_df: DataFrame con datos de puntos críticos
    :param departamento: String que indica el departamento a filtrar (en mayúsculas)
    :return: Grafo MST de NetworkX o None si no es posible construirlo
    """
    print(f"Construyendo el grafo completo para MST en el departamento: {departamento}...")
    G = nx.Graph()

    # Filtrar embalses por departamento
    embalses_filtrados = embalses_df[embalses_df['Departamento'] == departamento]
    print(f"Número de embalses en {departamento}: {embalses_filtrados.shape[0]}")

    # Filtrar puntos críticos por departamento
    puntos_filtrados = puntos_df[puntos_df['Departamento'] == departamento]
    print(f"Número de puntos críticos en {departamento}: {puntos_filtrados.shape[0]}")

    # Verificar si hay suficientes nodos para construir un MST
    total_nodos = embalses_filtrados.shape[0] + puntos_filtrados.shape[0]
    if total_nodos < 2:
        print(f"No hay suficientes nodos en el departamento {departamento} para construir un MST.")
        return None

    # Añadir ID si falta en embalses_df
    if 'ID' not in embalses_filtrados.columns:
        embalses_filtrados = embalses_filtrados.reset_index().rename(columns={'index': 'ID'})

    # Añadir ID si falta en puntos_df
    if 'ID' not in puntos_filtrados.columns:
        puntos_filtrados = puntos_filtrados.reset_index().rename(columns={'index': 'ID'})

    # Añadir nodos de embalses con IDs únicos
    for _, row in embalses_filtrados.iterrows():
        nodo_id = f"embalse_{row['ID']}"  # Crear un identificador único para embalses
        G.add_node(nodo_id, pos=(row['Latitud'], row['Longitud']), tipo='embalse', nombre=row['Nombre de la Presa'])
        print(f"Añadido embalse: {nodo_id} - {row['Nombre de la Presa']}")

    # Añadir nodos de puntos críticos con IDs únicos
    for _, row in puntos_filtrados.iterrows():
        nodo_id = f"punto_{row['ID']}"  # Crear un identificador único para puntos críticos
        G.add_node(nodo_id, pos=(row['Latitud'], row['Longitud']), tipo='punto_critico', nombre=row['Sector'])
        print(f"Añadido punto crítico: {nodo_id} - {row['Sector']}")

    # Crear aristas completas entre todos los nodos con pesos basados en la distancia geográfica
    nodos = list(G.nodes(data=True))
    for i in range(len(nodos)):
        for j in range(i + 1, len(nodos)):
            nodo1, data1 = nodos[i]
            nodo2, data2 = nodos[j]
            coord1 = data1['pos']
            coord2 = data2['pos']
            distancia = geodesic(coord1, coord2).kilometers
            G.add_edge(nodo1, nodo2, weight=distancia)
            print(f"Arista añadida entre {nodo1} y {nodo2} con distancia {distancia:.2f} km")

    # Calcular el Árbol de Expansión Mínima
    try:
        mst = nx.minimum_spanning_tree(G, weight='weight')
        print("Árbol de Expansión Mínima construido exitosamente.")
        return mst
    except Exception as e:
        print(f"Error al calcular el MST: {e}")
        return None