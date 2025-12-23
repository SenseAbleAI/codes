"""
traversal
---------

Graph traversal utilities for the Sensory Translation Graph (STG). Implements
an adapted Dijkstra algorithm that incorporates modality transition penalties,
heuristic costs, user accessibility profiles, and returns ranked alternative
paths between nodes.
"""

from __future__ import annotations

import heapq
import logging
from typing import Dict, List, Optional, Tuple

from core.stg.graph import SensoryTranslationGraph

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _find_start_nodes(graph: SensoryTranslationGraph, start_token: str) -> List[str]:
    """Find candidate start node ids matching a token (exact or substring).

    Returns list of node ids ordered by match quality (exact first).
    """
    matches: List[Tuple[int, str]] = []
    for node in graph.nodes():
        if node.id == start_token or node.text == start_token:
            matches.append((0, node.id))
        elif start_token.lower() in node.text.lower():
            matches.append((1, node.id))
    matches.sort()
    return [mid for _, mid in matches]


def dijkstra_paths(
    graph: SensoryTranslationGraph,
    start_token: str,
    goal_modalities: Optional[List[str]] = None,
    user_profile: Optional[Dict] = None,
    max_paths: int = 3,
) -> List[Dict]:
    """Find ranked paths in the STG from start to nodes matching any of
    `goal_modalities`.

    Args:
        graph: SensoryTranslationGraph instance
        start_token: token or node id to start from
        goal_modalities: list of modality names to treat as acceptable goals
        user_profile: optional user profile dict used to modulate penalties
        max_paths: how many alternative paths to return

    Returns:
        A list of path dicts: {"nodes": [ids], "cost": float, "score": float, "explanation": str}
    """
    start_nodes = _find_start_nodes(graph, start_token)
    if not start_nodes:
        raise KeyError(f"No start node found matching '{start_token}'")

    # Dijkstra state: (cost, node_id, path)
    pq: List[Tuple[float, str, List[str]]] = []
    for s in start_nodes:
        heapq.heappush(pq, (0.0, s, [s]))

    found: List[Tuple[float, List[str]]] = []
    visited_best: Dict[str, float] = {}

    while pq and len(found) < max_paths:
        cost, node_id, path = heapq.heappop(pq)
        # if we have already a cheaper path to node_id, skip
        if node_id in visited_best and cost > visited_best[node_id] + 1e-9:
            continue
        visited_best[node_id] = cost

        node = graph.get_node(node_id)
        # goal test
        if goal_modalities and node.modality in goal_modalities:
            # score: lower cost -> higher score in [0,1]
            score = 1.0 / (1.0 + cost)
            found.append((cost, path))
            logger.debug("Found path to %s cost=%.3f", node_id, cost)
            continue

        # expand neighbors
        for edge in graph.neighbors(node_id):
            next_id = edge.target
            # compute modality penalty using graph helper
            culture_factor = user_profile.get("culture_factor", 1.0) if user_profile else 1.0
            penalty = graph.compute_transition_penalty(node_id, next_id, user_profile=user_profile, culture_factor=culture_factor)
            edge_weight = edge.weight(modality_penalty=penalty, cultural_factor=culture_factor)
            heuristic = user_profile.get("heuristic_bias", 0.0) if user_profile else 0.0
            total_cost = cost + edge_weight + heuristic

            # prune if we already have a better cost for next_id
            if next_id in visited_best and total_cost >= visited_best[next_id]:
                continue

            heapq.heappush(pq, (total_cost, next_id, path + [next_id]))

    # format results
    out: List[Dict] = []
    for cost, path in found:
        out.append({"nodes": path, "cost": cost, "score": 1.0 / (1.0 + cost), "explanation": f"cost={cost:.3f}"})

    return out


def traverse_stg(span: Dict, fingerprint: Optional[Dict] = None, max_paths: int = 3) -> List[str]:
    """Compatibility wrapper used by the pipeline.

    Accepts a detection `span` and optional `fingerprint` (or user_profile) and
    returns a flat list of node ids representing plausible STG translations.
    """
    if not span:
        return []
    start_token = span.get("token") or span.get("text")
    if not start_token:
        return []

    user_profile = fingerprint or {}
    # infer goal modalities from span or user profile
    goal_modalities = user_profile.get("preferred_goal_modalities") if user_profile else None
    # default to a broad set
    if not goal_modalities:
        goal_modalities = ["vision", "hearing", "touch", "cross_sensory"]

    try:
        paths = dijkstra_paths(graph=SensoryTranslationGraph(), start_token=start_token, goal_modalities=goal_modalities, user_profile=user_profile, max_paths=max_paths)
        # flatten to node ids
        out: List[str] = []
        for p in paths:
            out.extend(p.get("nodes", []))
        return out
    except Exception:
        return []


__all__ = ["dijkstra_paths"]
