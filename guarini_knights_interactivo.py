#!/usr/bin/env python3
"""
Guarini 1512 – visor interactivo
================================

•   Slider paso a paso (ipywidgets + Jupyter).
•   Grafo navegable (pyvis -> HTML).

Uso rápido
----------
$ python3 guarini_knights_interactivo.py       # sólo estadísticas + CSV
$ python3 guarini_knights_interactivo.py --graph-html  # genera guarini.html

En un notebook:
>>> from guarini_knights_interactivo import show_slider, show_graph
>>> show_slider()   # deslizador
>>> show_graph()    # iframe con el grafo
"""
from collections import deque
import argparse
import networkx as nx
import pandas as pd
from typing import List, Tuple




# ─────────── Representación ────────────
INIT_STATE: Tuple[int, ...] = (1, 0, 1,
                               0, 0, 0,
                               2, 0, 2)

GOAL_STATE: Tuple[int, ...] = (2, 0, 2,
                               0, 0, 0,
                               1, 0, 1)

KNIGHT_OFFSETS = [(2, 1), (1, 2), (-1, 2), (-2, 1),
                  (-2, -1), (-1, -2), (1, -2), (2, -1)]


def idx_to_coord(idx: int) -> Tuple[int, int]:
    return divmod(idx, 3)


def coord_to_idx(r: int, c: int) -> int:
    return 3 * r + c

# precálculo de destinos
DEST = {}
for i in range(9):
    r, c = idx_to_coord(i)
    DEST[i] = [coord_to_idx(r + dr, c + dc)
               for dr, dc in KNIGHT_OFFSETS
               if 0 <= r + dr < 3 and 0 <= c + dc < 3]


def successors(state: Tuple[int, ...]):
    s = list(state)
    for i, piece in enumerate(s):
        if piece in (1, 2):
            for d in DEST[i]:
                if s[d] == 0:
                    nxt = s.copy()
                    nxt[i] = 0
                    nxt[d] = piece
                    yield tuple(nxt)


def build_graph(start: Tuple[int, ...]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node(start)
    q = deque([start])
    while q:
        u = q.popleft()
        for v in successors(u):
            if v not in g:
                q.append(v)
            g.add_edge(u, v)
    return g


def shortest_path(g: nx.DiGraph,
                  s: Tuple[int, ...],
                  t: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    return nx.shortest_path(g, source=s, target=t)


# ──────────── Pretty print ─────────────
def board_lines(state: Tuple[int, ...]) -> List[str]:
    sym = {0: "·", 1: "♞", 2: "♘"}
    return [" ".join(sym[state[3 * r + c]] for c in range(3)) for r in range(3)]


# ╭──────────────────────────────────────────────────────────╮
# │                1.  SLIDER  (ipywidgets)                 │
# ╰──────────────────────────────────────────────────────────╯
def show_slider():
    """Abre un slider interactivo en Jupyter para recorrer la ruta óptima."""
    try:
        import ipywidgets as widgets
        from IPython.display import display, Markdown
    except ImportError:
        raise RuntimeError("Necesitas instalar ipywidgets:  pip install ipywidgets")

    g = build_graph(INIT_STATE)
    path = shortest_path(g, INIT_STATE, GOAL_STATE)
    n_steps = len(path) - 1

    slider = widgets.IntSlider(min=0, max=n_steps, step=1,
                               description="Paso", value=0,
                               continuous_update=False)

    out = widgets.Output()

    def render(step: int):
        state = path[step]
        txt = "\n".join(board_lines(state))
        with out:
            out.clear_output(wait=True)
            display(Markdown(f"**Paso {step}/{n_steps}**\n```\n{txt}\n```"))

    render(0)  # inicial
    slider.observe(lambda ch: render(ch["new"]), names="value")
    display(slider, out)


# ╭──────────────────────────────────────────────────────────╮
# │        2.  GRAFO NAVEGABLE  (pyvis -> HTML)             │
# ╰──────────────────────────────────────────────────────────╯
def show_graph(filename: str = "guarini.html", height="750px", width="100%"):
    """Genera un HTML interactivo con el grafo completo y destaca la ruta óptima."""
    try:
        from pyvis.network import Network
        from IPython.display import IFrame
    except ImportError:
        raise RuntimeError("Necesitas instalar pyvis:  pip install pyvis")

    g = build_graph(INIT_STATE)
    path = shortest_path(g, INIT_STATE, GOAL_STATE)

    net = Network(height=height, width=width, directed=True, notebook=True,
                  bgcolor="#ffffff", font_color="black")

    # Mapea cada nodo a una cadena de texto para PyVis
    id_map = {node: str(node) for node in g.nodes()}

    # Marca nodos especiales (inicio, fin, normales)
    for node, node_id in id_map.items():
        color = "#ff7f0e" if node == INIT_STATE else \
                "#2ca02c" if node == GOAL_STATE else "#1f77b4"

        label = "\n".join("".join("♞" if x == 1 else "♘" if x == 2 else "·"
                                  for x in node[i*3:(i+1)*3]) for i in range(3))

        net.add_node(node_id, label=label, color=color, physics=True)

    # Crear conjunto de aristas en la ruta óptima
    path_edges = set(zip(path, path[1:]))

    for u, v in g.edges():
        uid = id_map[u]
        vid = id_map[v]
        if (u, v) in path_edges:
            # Arista en la ruta óptima (color rojo, más ancha)
            net.add_edge(uid, vid, color="red", width=4)
        else:
            # Arista normal
            net.add_edge(uid, vid, color="#cccccc", width=1)

    net.show(filename)
    print(f"Archivo HTML generado: {filename}")
    try:
        return IFrame(filename, height=height, width=width)
    except Exception:
        return None


# ╭──────────────────────────────────────────────────────────╮
# │                 3.  CLI / MAIN PROGRAM                  │
# ╰──────────────────────────────────────────────────────────╯
def main():
    parser = argparse.ArgumentParser(description="Guarini 1512 – explorador")
    parser.add_argument("--graph-html", action="store_true",
                        help="Genera guarini.html con el grafo completo.")
    parser.add_argument("--csv", action="store_true",
                        help="Guarda ruta óptima a ruta_optima_guarini.csv")
    args = parser.parse_args()

    g = build_graph(INIT_STATE)
    path = shortest_path(g, INIT_STATE, GOAL_STATE)
    min_moves = len(path) - 1

    print("─" * 60)
    print("Espacio de estados Guarini 3×3")
    print(f"Estados  : {g.number_of_nodes():>4}")
    print(f"Aristas  : {g.number_of_edges():>4}")
    print(f"Mínimos movimientos: {min_moves}")
    print("─" * 60)

    if args.csv:
        pd.DataFrame({"step": range(len(path)),
                      "state": path}).to_csv("ruta_optima_guarini.csv",
                                             index=False)
        print("CSV 'ruta_optima_guarini.csv' guardado.")

    if args.graph_html:
        show_graph()
    else:
        # muestra camino por consola
        for i, st in enumerate(path):
            print(f"Paso {i}")
            print("\n".join(board_lines(st)))
            print()


if __name__ == "__main__":
    main()
