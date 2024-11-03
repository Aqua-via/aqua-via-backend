# algorithms/mst_algorithm.py
import networkx as nx
from geopy.distance import geodesic

def construir_grafo(embalses_df, puntos_df, departamento):
    """
    Construye un grafo completo que incluye embalses y puntos críticos dentro de un departamento.
    """
    print(f"Construyendo el grafo completo en el departamento: {departamento}...")
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

    # Añadir ID si falta en puntos_filtrados
    if 'ID' not in puntos_filtrados.columns:
        puntos_filtrados = puntos_filtrados.reset_index().rename(columns={'index': 'ID'})

    # Añadir nodos de embalses con IDs únicos
    for _, row in embalses_filtrados.iterrows():
        nodo_id = f"embalse_{row['ID']}"
        G.add_node(nodo_id, pos=(row['Latitud'], row['Longitud']), tipo='embalse', nombre=row['Nombre de la Presa'])
        print(f"Añadido embalse: {nodo_id} - {row['Nombre de la Presa']}")

    # Añadir nodos de puntos críticos con IDs únicos
    for _, row in puntos_filtrados.iterrows():
        nodo_id = f"punto_{row['ID']}"
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
            # print(f"Arista añadida entre {nodo1} y {nodo2} con distancia {distancia:.2f} km")

    return G

def kruskal_mst(G):
    """
    Implementa el algoritmo de Kruskal para encontrar el Árbol de Expansión Mínima (MST).
    Además, registra los pasos intermedios con descripciones para visualización.
    """
    parent = {}
    rank = {}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]  # Compresión de ruta
            u = parent[u]
        return u

    def union(u, v):
        u_root = find(u)
        v_root = find(v)
        if u_root == v_root:
            return False  # Ya están conectados
        if rank[u_root] < rank[v_root]:
            parent[u_root] = v_root
        else:
            parent[v_root] = u_root
            if rank[u_root] == rank[v_root]:
                rank[u_root] += 1
        return True

    # Inicializar conjuntos
    for node in G.nodes():
        parent[node] = node
        rank[node] = 0

    # Ordenar las aristas por peso
    edges = list(G.edges(data=True))
    edges.sort(key=lambda x: x[2]['weight'])

    mst_edges = []
    steps = []  # Para registrar los pasos

    for u, v, data in edges:
        u_root = find(u)
        v_root = find(v)
        descripcion = f"Considerando la arista {u} - {v} con peso {data['weight']:.2f} km."

        if u_root != v_root:
            union(u, v)
            mst_edges.append((u, v, data))
            descripcion += " No forma ciclo. Arista añadida al MST."
            accion = 'añadida'
            print(f"Arista añadida al MST: {u} - {v} con peso {data['weight']:.2f}")
        else:
            descripcion += " Forma ciclo. Arista descartada."
            accion = 'descartada'
            print(f"Arista descartada: {u} - {v} (forma ciclo)")

        steps.append({
            'edge': (u, v),
            'weight': data['weight'],
            'descripcion': descripcion,
            'accion': accion
        })

    return mst_edges, steps
