"""Step 3: build the knowledge graph from the decisions, and measure it against the truth.

A knowledge graph stores things (nodes) and how they connect (edges).
Here the things are companies and people, and the edge is WORKS_AT.

  before: every record is its own company node. One real company typed into
          three systems shows up as three companies, and its people are split.
  after:  records the policy said to merge become one company node, with all
          its people. Pairs sent to a person are drawn as dashed "check me"
          edges and are NOT merged.

Writes graph_before.html and graph_after.html (open them in a browser),
graph_after.graphml (opens in Gephi, or loads into Neo4j), and prints how
close the merged graph is to the truth.

    python capstone/step3_graph.py
    python capstone/step3_graph.py --model gpt-6-luna
    python capstone/step3_graph.py --focus orchid   # also a small, readable view of one name

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx

from jevcourse.calls import JEV_MODEL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "capstone/out"
RECORDS = ROOT / "data/companies/records.jsonl"
TRUTH = ROOT / "data/companies/truth.json"
HTML_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>body{{margin:0;font-family:system-ui,sans-serif;background:#fbfaf6}}
#h{{padding:14px 20px;font-size:20px}}#g{{width:100vw;height:calc(100vh - 56px)}}</style>
</head><body><div id="h">{title}</div><div id="g"></div><script>
const data = {data};
new vis.Network(document.getElementById("g"),
  {{nodes: new vis.DataSet(data.nodes), edges: new vis.DataSet(data.edges)}},
  {{physics: {{stabilization: {{iterations: 300}}, barnesHut: {{springLength: 90}}}},
    nodes: {{font: {{size: 16}}}}, edges: {{color: {{color: "#9a9a9a"}}}}}});
</script></body></html>"""


class UnionFind:
    """Groups records into companies as merge decisions arrive."""

    def __init__(self, items: list[str]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        """The group leader for x."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        """Put a and b in the same group."""
        self.parent[self.find(a)] = self.find(b)


def build_graph(records: list[dict], group_of: dict[str, str]) -> nx.Graph:
    """Companies and people. Records in the same group become one company node."""
    g = nx.Graph()
    names: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        names[group_of[r["record_id"]]][r["name"]] += 1
    for gid, counter in names.items():
        g.add_node(gid, kind="company", label=counter.most_common(1)[0][0],
                   records=sum(counter.values()))
    for r in records:
        company = group_of[r["record_id"]]
        person = f"person:{r['contact']['name']}@{company}"
        g.add_node(person, kind="person", label=r["contact"]["name"])
        g.add_edge(person, company, kind="WORKS_AT")
    return g


def to_html(g: nx.Graph, title: str, check_edges: list[tuple[str, str]], path: Path) -> None:
    """A self-contained page that draws the graph with vis-network."""
    nodes = []
    for n, d in g.nodes(data=True):
        if d["kind"] == "company":
            nodes.append({"id": n, "label": d["label"], "shape": "box",
                          "color": "#2a78d6" if d["records"] > 1 else "#9fb7d6",
                          "font": {"color": "#ffffff" if d["records"] > 1 else "#1d2733"}})
        else:
            nodes.append({"id": n, "label": d["label"], "shape": "dot", "size": 8,
                          "color": "#eb6834"})
    edges = [{"from": a, "to": b} for a, b in g.edges()]
    edges += [{"from": a, "to": b, "dashes": True, "color": {"color": "#e0a100"}, "width": 3}
              for a, b in check_edges]
    path.write_text(HTML_TEMPLATE.format(title=title,
                                         data=json.dumps({"nodes": nodes, "edges": edges})))


def main() -> None:
    """Build both graphs, write them, and compare the result with the truth."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=JEV_MODEL)
    parser.add_argument("--wording", choices=["v1", "v2"], default="v2")
    parser.add_argument("--focus", default="",
                        help="also write a small before/after view of the records whose name "
                             "contains this text, for example 'orchid'")
    args = parser.parse_args()
    records = [json.loads(x) for x in RECORDS.read_text().splitlines()]
    truth = json.loads(TRUTH.read_text())["record_to_entity"]
    decisions = [json.loads(x) for x in
                 (OUT / f"decisions-{args.model}-{args.wording}.jsonl").read_text().splitlines()]

    ids = [r["record_id"] for r in records]
    uf = UnionFind(ids)
    for d in decisions:
        if d["action"] == "merge":
            uf.union(d["a"], d["b"])
    after_group = {i: uf.find(i) for i in ids}
    before = build_graph(records, {i: i for i in ids})
    after = build_graph(records, after_group)
    checks = [(after_group[d["a"]], after_group[d["b"]]) for d in decisions
              if d["action"] == "person_checks" and after_group[d["a"]] != after_group[d["b"]]]

    to_html(before, "Before: one company node per record", [], OUT / "graph_before.html")
    to_html(after, f"After: merged by {args.model} (dashed = a person should check)", checks,
            OUT / "graph_after.html")
    nx.write_graphml(after, OUT / "graph_after.graphml")
    if args.focus:
        keep = {r["record_id"] for r in records if args.focus.lower() in r["name"].lower()}
        groups = {after_group[i] for i in keep}
        nb = [n for n in before if n in keep or before.nodes[n]["kind"] == "person"
              and any(m in keep for m in before[n])]
        na = [n for n in after if n in groups or after.nodes[n]["kind"] == "person"
              and any(m in groups for m in after[n])]
        focus_checks = [(a, b) for a, b in checks if a in groups and b in groups]
        to_html(before.subgraph(nb), f"Before: '{args.focus}' records, one node per record",
                [], OUT / f"graph_before_{args.focus}.html")
        to_html(after.subgraph(na), f"After: '{args.focus}' records merged by {args.model}",
                focus_checks, OUT / f"graph_after_{args.focus}.html")
        print(f"focus '{args.focus}': {len(keep)} records -> {len(groups)} company nodes; "
              f"wrote graph_before_{args.focus}.html and graph_after_{args.focus}.html")

    members: dict[str, set[str]] = defaultdict(set)
    for rid, gid in after_group.items():
        members[gid].add(truth[rid])
    real_companies = len(set(truth.values()))
    mixed = sum(1 for ents in members.values() if len(ents) > 1)
    split = Counter(e for gid in members for e in members[gid])
    still_split = sum(1 for _, n in split.items() if n > 1)
    people_before = sum(1 for _, d in before.nodes(data=True) if d["kind"] == "person")
    people_after = sum(1 for _, d in after.nodes(data=True) if d["kind"] == "person")

    gold = {json.loads(x)["pair_id"]: json.loads(x)["same_entity"]
            for x in (OUT / "candidate_pairs.jsonl").read_text().splitlines()}
    merged = [d for d in decisions if d["action"] == "merge"]
    merged_right = sum(gold[d["pair_id"]] for d in merged)
    print(f"pairs merged: {len(merged)}, of which really the same company: {merged_right} "
          f"(precision {merged_right / max(len(merged), 1):.1%})")
    print(f"real duplicate pairs found by merging: {merged_right} of {sum(gold.values())} "
          f"(recall {merged_right / sum(gold.values()):.1%})")
    print(f"company nodes before: {len(ids)}   after: {len(members)}   "
          f"real companies (truth): {real_companies}")
    print(f"person nodes before: {people_before}   after: {people_after}")
    print(f"company nodes that wrongly mix two real companies: {mixed}")
    print(f"real companies still split over more than one node: {still_split}")
    sent = sum(d["action"] == "person_checks" for d in decisions)
    print(f"pairs sent to a person: {sent}; of those, {sent - len(checks)} were already joined "
          f"through other merges, so {len(checks)} still wait for a person")
    print("wrote capstone/out/graph_before.html, graph_after.html, graph_after.graphml")


if __name__ == "__main__":
    main()
