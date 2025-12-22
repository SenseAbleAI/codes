class SensoryTranslationGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node, modality):
        self.nodes[node] = modality

    def add_edge(self, source, target, cost):
        self.edges.setdefault(source, []).append((target, cost))

    def neighbors(self, node):
        return self.edges.get(node, [])