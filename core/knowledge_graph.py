#!/usr/bin/env python3
"""
Knowledge Graph Memory — Persistent cross-session attack knowledge.
Nodes: targets, tools, techniques, exploits, vulnerabilities, agents.
Edges: used_by, targets, exploits, mitigates, related_to.
Auto-learns from every mission. NetworkX + SQLite persistence.
"""

import json, sqlite3, time, hashlib, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

DATA_DIR = Path("/home/kali/HackWithAI/data/knowledge")
DATA_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DB = DATA_DIR / "knowledge_graph.db"

# Try NetworkX, fall back to pure dict
try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False


class Node:
    def __init__(self, name: str, node_type: str, properties: Dict = {}):
        self.name = name
        self.node_type = node_type
        self.properties = properties or {}
        self.properties.setdefault("created", datetime.now().isoformat())
        self.properties.setdefault("success_rate", 0.0)
        self.properties.setdefault("uses", 0)
        self.properties.setdefault("confidence", 0.5)

    def to_dict(self) -> Dict:
        return {"name": self.name, "type": self.node_type, "properties": self.properties}

    def __hash__(self): return hash(self.name)
    def __eq__(self, o): return isinstance(o, Node) and o.name == self.name


class Edge:
    def __init__(self, source: str, target: str, relationship: str, weight: float = 1.0):
        self.source = source
        self.target = target
        self.relationship = relationship
        self.weight = weight

    def to_dict(self) -> Dict:
        return {"source": self.source, "target": self.target,
                "relationship": self.relationship, "weight": self.weight}

    def __hash__(self): return hash((self.source, self.target, self.relationship))


class KnowledgeGraph:
    """Persistent knowledge graph for cross-session attack knowledge."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Set[Edge] = set()
        self.nx_graph = nx.DiGraph() if HAS_NX else None
        self._load()
        self._start_auto_save()

    # ── CRUD ──────────────────────────────────────────────────────────

    def add_node(self, name: str, node_type: str, properties: Dict = {}) -> Node:
        if name in self.nodes:
            node = self.nodes[name]
            node.properties.update(properties)
        else:
            node = Node(name, node_type, properties)
            self.nodes[name] = node
        if self.nx_graph is not None:
            self.nx_graph.add_node(name, type=node_type, **properties)
        return node

    def add_edge(self, from_node: str, to_node: str, relationship: str,
                 weight: float = 1.0) -> Edge:
        # Ensure nodes exist
        if from_node not in self.nodes:
            self.add_node(from_node, "unknown")
        if to_node not in self.nodes:
            self.add_node(to_node, "unknown")

        edge = Edge(from_node, to_node, relationship, weight)
        self.edges.add(edge)
        if self.nx_graph is not None:
            self.nx_graph.add_edge(from_node, to_node, relationship=relationship, weight=weight)
        return edge

    def get_node(self, name: str) -> Optional[Node]:
        return self.nodes.get(name)

    # ── Queries ───────────────────────────────────────────────────────

    def query_related(self, node_name: str, depth: int = 2) -> List[Dict]:
        """Find all nodes connected to given node up to specified depth."""
        if node_name not in self.nodes:
            return []

        related = []
        visited = {node_name}
        frontier = [node_name]

        for _ in range(depth):
            next_frontier = []
            for current in frontier:
                for edge in self.edges:
                    if edge.source == current and edge.target not in visited:
                        next_frontier.append(edge.target)
                        visited.add(edge.target)
                        target_node = self.nodes.get(edge.target)
                        if target_node:
                            related.append({
                                "node": target_node.to_dict(),
                                "relationship": edge.relationship,
                                "weight": edge.weight,
                            })
                    elif edge.target == current and edge.source not in visited:
                        next_frontier.append(edge.source)
                        visited.add(edge.source)
                        source_node = self.nodes.get(edge.source)
                        if source_node:
                            related.append({
                                "node": source_node.to_dict(),
                                "relationship": edge.relationship,
                                "weight": edge.weight,
                            })
            frontier = next_frontier

        return related

    def find_best_path(self, start_type: str, end_type: str) -> List[Dict]:
        """Find the best attack path from start type to end type."""
        start_nodes = [n for n in self.nodes.values() if n.node_type == start_type]
        end_nodes = [n for n in self.nodes.values() if n.node_type == end_type]

        if HAS_NX and self.nx_graph is not None and start_nodes and end_nodes:
            return self._nx_best_path(start_nodes[0].name, end_nodes[0].name)

        # Fallback: BFS
        return self._bfs_best_path(start_type, end_type)

    def _nx_best_path(self, start: str, end: str) -> List[Dict]:
        try:
            if self.nx_graph is None: return []
            path = nx.shortest_path(self.nx_graph, source=start, target=end, weight="weight")
            result = []
            for i, name in enumerate(path):
                node = self.nodes.get(name)
                if node:
                    step = node.to_dict()
                    if i < len(path) - 1:
                        edge_data = self.nx_graph.get_edge_data(path[i], path[i + 1])
                        step["next_relationship"] = edge_data.get("relationship", "") if edge_data else ""
                    result.append(step)
            return result
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def _bfs_best_path(self, start_type: str, end_type: str) -> List[Dict]:
        start_nodes = [n.name for n in self.nodes.values() if n.node_type == start_type]
        if not start_nodes:
            return []
        return [self.nodes.get(n, Node(n, "")).to_dict() for n in start_nodes[:1]]

    def get_recommendations(self, target_type: str) -> Dict:
        """Suggest best tools/techniques for a target type."""
        # Find all nodes of this type
        targets = [n for n in self.nodes.values() if n.node_type == target_type]

        # Find tools used against these targets
        tool_scores: Dict[str, float] = {}
        for target in targets:
            related = self.query_related(target.name)
            for r in related:
                if r["node"]["type"] == "tool":
                    name = r["node"]["name"]
                    tool_scores[name] = tool_scores.get(name, 0) + r["weight"]

        # Find successful techniques
        techniques = {}
        for edge in self.edges:
            if (edge.relationship in ("used_by", "exploits") and
                any(t.name == edge.target for t in targets)):
                source = self.nodes.get(edge.source)
                if source:
                    techniques[source.name] = source.properties.get("success_rate", 0)

        return {
            "target_type": target_type,
            "target_count": len(targets),
            "recommended_tools": sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)[:10],
            "successful_techniques": sorted(techniques.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    # ── Learning ──────────────────────────────────────────────────────

    def learn_from_mission(self, mission_result: Dict):
        """Store mission results as knowledge graph nodes and edges."""
        target = mission_result.get("target", "unknown")
        debate = mission_result.get("debate", {})
        winner = debate.get("winner", "")
        strategy = debate.get("strategy", "")
        success = mission_result.get("execution", {}).get("overall_success", False)

        # Add target node
        target_node = self.add_node(target, "target", {
            "last_attacked": datetime.now().isoformat(),
        })

        # Add agent node and link
        if winner:
            agent_node = self.add_node(winner, "agent", {
                "debate_wins": 1,
            })
            self.add_edge(agent_node.name, target_node.name, "attacked")

        # Add strategy node
        if strategy:
            strategy_id = hashlib.md5(strategy.encode()).hexdigest()[:10]
            strategy_node = self.add_node(f"strategy_{strategy_id}", "strategy", {
                "text": strategy[:500],
                "success": success,
            })
            if winner:
                self.add_edge(winner, strategy_node.name, "proposed")

        # Update success rates
        if winner:
            agent_node = self.nodes.get(winner)
            if agent_node:
                uses = agent_node.properties.get("uses", 0) + 1
                old_rate = agent_node.properties.get("success_rate", 0)
                new_rate = (old_rate * (uses - 1) + (1 if success else 0)) / uses
                agent_node.properties["uses"] = uses
                agent_node.properties["success_rate"] = new_rate
                agent_node.properties["last_mission"] = datetime.now().isoformat()

    def learn_from_debate(self, debate_result: Dict):
        """Learn from debate results."""
        target = debate_result.get("target", "")
        winner = debate_result.get("final_winner", "")

        if target:
            self.add_node(target, "target", {
                "debated_at": datetime.now().isoformat(),
            })

        if winner:
            agent = self.add_node(winner, "agent")
            agent.properties["debate_wins"] = agent.properties.get("debate_wins", 0) + 1
            agent.properties["confidence"] = debate_result.get("agent_stats", {}).get(
                winner, {}).get("confidence", 0.5)

        # Link agents who voted together
        for rnd in debate_result.get("rounds", []):
            votes = rnd.get("votes", {})
            for voter, chosen in votes.items():
                self.add_edge(voter, chosen, "voted_for")

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self):
        """Load graph from SQLite on startup."""
        if not GRAPH_DB.exists():
            return
        try:
            with sqlite3.connect(GRAPH_DB) as db:
                db.execute("""CREATE TABLE IF NOT EXISTS nodes (
                    name TEXT PRIMARY KEY, type TEXT, properties TEXT)""")
                db.execute("""CREATE TABLE IF NOT EXISTS edges (
                    source TEXT, target TEXT, relationship TEXT, weight REAL)""")

                for row in db.execute("SELECT name, type, properties FROM nodes"):
                    try:
                        props = json.loads(row[2])
                    except Exception:
                        props = {}
                    self.add_node(row[0], row[1], props)

                for row in db.execute("SELECT source, target, relationship, weight FROM edges"):
                    self.add_edge(row[0], row[1], row[2], row[3])

            print(f"[KG] Loaded {len(self.nodes)} nodes, {len(self.edges)} edges")
        except Exception as e:
            print(f"[KG] Load failed: {e}")

    def save(self):
        """Persist graph to SQLite."""
        try:
            with sqlite3.connect(GRAPH_DB) as db:
                db.execute("CREATE TABLE IF NOT EXISTS nodes (name TEXT PRIMARY KEY, type TEXT, properties TEXT)")
                db.execute("CREATE TABLE IF NOT EXISTS edges (source TEXT, target TEXT, relationship TEXT, weight REAL)")
                db.execute("DELETE FROM nodes")
                db.execute("DELETE FROM edges")
                for node in self.nodes.values():
                    db.execute("INSERT INTO nodes VALUES (?,?,?)",
                              (node.name, node.node_type, json.dumps(node.properties)))
                for edge in self.edges:
                    db.execute("INSERT INTO edges VALUES (?,?,?,?)",
                              (edge.source, edge.target, edge.relationship, edge.weight))
                db.commit()
        except Exception as e:
            print(f"[KG] Save failed: {e}")

    def _start_auto_save(self, interval: int = 300):
        """Auto-save every interval seconds."""
        def autosave():
            while True:
                time.sleep(interval)
                try:
                    self.save()
                except Exception:
                    pass
        t = threading.Thread(target=autosave, daemon=True)
        t.start()

    def stats(self) -> Dict:
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": {t: sum(1 for n in self.nodes.values() if n.node_type == t)
                          for t in set(n.node_type for n in self.nodes.values())},
            "db_file": str(GRAPH_DB),
            "db_size_mb": round(GRAPH_DB.stat().st_size / 1024 / 1024, 2) if GRAPH_DB.exists() else 0,
        }


# ── Singleton ────────────────────────────────────────────────────────────
_kg: Optional[KnowledgeGraph] = None

def get_knowledge_graph() -> KnowledgeGraph:
    global _kg
    if _kg is None:
        _kg = KnowledgeGraph()
    return _kg


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    kg = KnowledgeGraph()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        print(json.dumps(kg.stats(), indent=2))
    elif cmd == "add-node":
        kg.add_node(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "unknown")
        kg.save()
        print(f"Added node: {sys.argv[2]}")
    elif cmd == "add-edge":
        kg.add_edge(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "related")
        kg.save()
        print(f"Added edge: {sys.argv[2]} → {sys.argv[3]}")
    elif cmd == "related":
        results = kg.query_related(sys.argv[2])
        print(json.dumps(results, indent=2))
    elif cmd == "recommend":
        ttype = sys.argv[2] if len(sys.argv) > 2 else "target"
        print(json.dumps(kg.get_recommendations(ttype), indent=2))
    elif cmd == "path":
        start = sys.argv[2] if len(sys.argv) > 2 else "agent"
        end = sys.argv[3] if len(sys.argv) > 3 else "target"
        print(json.dumps(kg.find_best_path(start, end), indent=2))
    else:
        print("Commands: stats | add-node | add-edge | related | recommend | path")
