from core.stg.graph import SensoryTranslationGraph
from core.stg.weights import MODALITY_COST
import heapq

GRAPH = SensoryTranslationGraph()

GRAPH.add_node("loud", "hearing")
GRAPH.add_node("vibration", "touch")
GRAPH.add_node("bright", "vision")
GRAPH.add_node("warm", "touch")

GRAPH.add_edge("loud", "vibration", 0.3)
GRAPH.add_edge("bright", "warm", 0.4)

def traverse_stg(span, fingerprint):
    start = span["token"]
    visited = set()
    queue = [(0.0, start)]
    results = []

    while queue:
        cost, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        results.append(node)

        for neighbor, edge_cost in GRAPH.neighbors(node):
            modality = GRAPH.nodes.get(neighbor)
            penalty = fingerprint.data.get(modality, 0.0)
            total_cost = cost + edge_cost + penalty
            heapq.heappush(queue, (total_cost, neighbor))

    return results