"""
stg.graph
---------

Sensory Translation Graph implementation. The Sensory Translation Graph (STG)
represents nodes that encapsulate sensory expressions or states and directed
edges that model possible translations between sensory modalities (e.g., from
`vision` to `hearing`). Edges include rich metadata and computed weights that
take into account modality transition penalties, user profile accessibility
preferences, and cultural emphasis.

The graph is intended to be used by traversal algorithms (e.g., Dijkstra)
exposed in `core.stg.traversal`.
"""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class STGNode:
    id: str
    modality: str
    text: str = ""
    meta: Dict = field(default_factory=dict)


@dataclass
class STGEdge:
    source: str
    target: str
    base_cost: float = 1.0
    transition_reason: Optional[str] = None
    meta: Dict = field(default_factory=dict)

    def weight(self, modality_penalty: float = 1.0, cultural_factor: float = 1.0) -> float:
        """Compute effective weight of the edge.

        Args:
            modality_penalty: additional multiplicative penalty for modality change
            cultural_factor: multiplicative cultural effect

        Returns:
            Effective numeric weight (lower is cheaper).
        """
        w = float(self.base_cost) * float(modality_penalty) / max(1e-6, float(cultural_factor))
        return max(0.0, w)


class SensoryTranslationGraph:
    """Directed graph with rich node and edge representations.

    Example:
        g = SensoryTranslationGraph()
        g.add_node('n1', 'vision', text='bright red')
        g.add_node('n2', 'hearing', text='a loud ring')
        g.add_edge('n1','n2', base_cost=1.2, transition_reason='metaphor')
    """

    def __init__(self):
        self._nodes: Dict[str, STGNode] = {}
        self._edges: Dict[str, List[STGEdge]] = {}

    def add_node(self, node_id: str, modality: str, text: str = "", meta: Optional[Dict] = None) -> STGNode:
        meta = meta or {}
        node = STGNode(id=node_id, modality=modality, text=text, meta=meta)
        self._nodes[node_id] = node
        logger.debug("Added node %s (modality=%s)", node_id, modality)
        return node

    def add_edge(self, source: str, target: str, base_cost: float = 1.0, transition_reason: Optional[str] = None, meta: Optional[Dict] = None) -> STGEdge:
        if source not in self._nodes or target not in self._nodes:
            raise KeyError("Both source and target nodes must be added before creating an edge")
        meta = meta or {}
        edge = STGEdge(source=source, target=target, base_cost=base_cost, transition_reason=transition_reason, meta=meta)
        self._edges.setdefault(source, []).append(edge)
        logger.debug("Added edge %s -> %s cost=%s", source, target, base_cost)
        return edge

    def neighbors(self, node_id: str) -> List[STGEdge]:
        return list(self._edges.get(node_id, []))

    def get_node(self, node_id: str) -> STGNode:
        return self._nodes[node_id]

    def nodes(self) -> Iterable[STGNode]:
        return list(self._nodes.values())

    def edges(self) -> Iterable[STGEdge]:
        for lst in self._edges.values():
            for e in lst:
                yield e

    def compute_transition_penalty(self, source_id: str, target_id: str, user_profile: Optional[Dict] = None, culture_factor: float = 1.0) -> float:
        """Compute a penalty for moving between two nodes based on modalities.

        Args:
            source_id: node id
            target_id: node id
            user_profile: optional user profile dict with modality preferences
            culture_factor: multiplicative cultural factor

        Returns:
            Penalty multiplier >= 0
        """
        s = self._nodes.get(source_id)
        t = self._nodes.get(target_id)
        if not s or not t:
            raise KeyError("Source or target node not found")

        # base penalty if modalities differ
        penalty = 1.0
        if s.modality != t.modality:
            penalty += 0.5

        # user profile may increase/decrease penalties for certain modalities
        if user_profile:
            pref = float(user_profile.get("modality_penalty_factor", {}).get(t.modality, 1.0))
            penalty *= pref

        # cultural factor reduces cost if culture favors target modality
        effective = penalty / max(1e-6, float(culture_factor))
        logger.debug("Transition %s->%s penalty=%s (culture=%s)", source_id, target_id, effective, culture_factor)
        return float(max(0.0, effective))

    def example_graph(self) -> None:
        """Populate the graph with a tiny example for testing/demonstration."""
        self.add_node("v_bright", "vision", text="bright light")
        self.add_node("h_ring", "hearing", text="a ringing sound")
        self.add_edge("v_bright", "h_ring", base_cost=1.2, transition_reason="visual->auditory metaphor")

    def to_dict(self) -> Dict[str, Dict]:
        """Serialize graph nodes and edges to a plain dict."""
        return {
            "nodes": {nid: {"modality": n.modality, "text": n.text, "meta": n.meta} for nid, n in self._nodes.items()},
            "edges": {src: [{"target": e.target, "base_cost": e.base_cost, "reason": e.transition_reason, "meta": e.meta} for e in lst] for src, lst in self._edges.items()},
        }

    def load_dict(self, payload: Dict[str, Dict]) -> None:
        """Load nodes and edges from a serialized dict (inverse of `to_dict`)."""
        nodes = payload.get("nodes", {})
        for nid, info in nodes.items():
            self.add_node(nid, info.get("modality", "unknown"), text=info.get("text", ""), meta=info.get("meta", {}))
        edges = payload.get("edges", {})
        for src, lst in edges.items():
            for e in lst:
                try:
                    self.add_edge(src, e.get("target"), base_cost=float(e.get("base_cost", 1.0)), transition_reason=e.get("reason"), meta=e.get("meta", {}))
                except Exception:
                    logger.exception("Failed to add edge %s->%s", src, e.get("target"))


__all__ = ["SensoryTranslationGraph", "STGNode", "STGEdge"]
