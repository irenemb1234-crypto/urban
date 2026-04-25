"""
Generate thought map CSVs from the urban design knowledge base.

Outputs:
  data/thought_map_nodes.csv  — all entities as graph nodes
  data/thought_map_edges.csv  — all relationships as directed edges
"""

import csv
import json
import os
import re
import unicodedata
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Author name merges: shorter/variant → canonical (longer) form
# ---------------------------------------------------------------------------
AUTHOR_MERGE_RAW = {
    "Alejandro Quinto": "Alejandro Quinto Ferrández",
    "Dario Ávila": "Darío Ávila Briceño",
}

# Recursos item names that map to a tool nombre in tools.json
# (case-insensitive key → exact tool nombre)
RECITEM_TO_TOOL = {
    "pysal": "PySAL spaghetti",
}

# Recursos item names that map to a program (case-insensitive key → exact program)
RECITEM_TO_PROG = {
    "osmnx": "OSMnx",
    "openstreetmap": "OpenStreetMap",
    "sentinel-2": "Sentinel-2",
    "geopandas": "GeoPandas",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Lowercase, strip accents, replace non-alnum with _, collapse repeats."""
    nfkd = unicodedata.normalize("NFKD", str(text))
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return slug or "unknown"


def normalize_name(name: str) -> str:
    """Normalize a person/org name for deduplication lookup."""
    nfkd = unicodedata.normalize("NFKD", str(name))
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_str.lower()).strip()


def truncate(text, length=200):
    if not text:
        return ""
    return str(text)[:length]


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Node registry
# ---------------------------------------------------------------------------

nodes = []
node_lookup = {}  # canonical_key → id
counters = defaultdict(int)

PREFIX_MAP = {
    "herramientas": "tool",
    "empresas": "company",
    "academico": "paper",
    "recursos": "collection",
    "recitem": "recitem",
    "otros": "otros",
    "persona": "person",
    "programa": "program",
    "subcategoria": "subcat",
    "sector": "sector",
}

NODE_FIELDS = [
    "id", "label", "category", "type", "description", "url",
    "ia", "acceso", "subcategoria", "sector", "fecha", "source_file", "extra",
]


def make_id(category: str) -> str:
    prefix = PREFIX_MAP.get(category, category)
    idx = counters[prefix]
    counters[prefix] += 1
    return f"{prefix}_{idx}"


def add_node(key, label, category, type_,
             description="", url="", ia="", acceso="",
             subcategoria="", sector="", fecha="",
             source_file="", extra=""):
    if key in node_lookup:
        return node_lookup[key]
    nid = make_id(category)
    node_lookup[key] = nid
    nodes.append({
        "id": nid,
        "label": label,
        "category": category,
        "type": type_,
        "description": truncate(description),
        "url": url or "",
        "ia": ia,
        "acceso": acceso,
        "subcategoria": subcategoria,
        "sector": sector,
        "fecha": fecha or "",
        "source_file": source_file,
        "extra": extra,
    })
    return nid


# ---------------------------------------------------------------------------
# Edge registry
# ---------------------------------------------------------------------------

edges = []

EDGE_FIELDS = [
    "source_id", "target_id", "relationship", "weight", "label", "bidirectional",
]


def add_edge(source_id, target_id, relationship, weight, label, bidirectional=0):
    edges.append({
        "source_id": source_id,
        "target_id": target_id,
        "relationship": relationship,
        "weight": weight,
        "label": label,
        "bidirectional": bidirectional,
    })


# ---------------------------------------------------------------------------
# Person resolution
# ---------------------------------------------------------------------------

def build_person_lookup(tools, academic, otros, companies):
    """
    Returns:
      author_merge: normalized_raw → canonical_raw
      company_names_norm: normalized → canonical company nombre
      person_canon: normalized_canonical → canonical_raw (genuine persons only)
    """
    # Build company name set
    company_names_norm = {normalize_name(c["nombre"]): c["nombre"] for c in companies}

    # Build merge map (normalize both sides)
    author_merge = {}
    for short, long_ in AUTHOR_MERGE_RAW.items():
        author_merge[normalize_name(short)] = long_

    # Collect all raw author names
    all_raw = (
        [t["autor"] for t in tools]
        + [a["autor"] for a in academic]
        + [o["autor"] for o in otros]
    )

    person_canon = {}  # normalized_canonical → canonical_raw
    for raw in all_raw:
        # Apply merge to get canonical
        norm_raw = normalize_name(raw)
        canonical_raw = author_merge.get(norm_raw, raw)
        norm_canon = normalize_name(canonical_raw)

        # Skip if it's an org name
        if norm_canon in company_names_norm:
            continue

        if norm_canon not in person_canon:
            person_canon[norm_canon] = canonical_raw

    return author_merge, company_names_norm, person_canon


def resolve_autor(raw, author_merge, company_names_norm):
    """Return node_id for an author (person or company)."""
    norm_raw = normalize_name(raw)
    canonical_raw = author_merge.get(norm_raw, raw)
    norm_canon = normalize_name(canonical_raw)

    # Check if it's a company
    if norm_canon in company_names_norm:
        comp_name = company_names_norm[norm_canon]
        return node_lookup.get(f"company::{comp_name}")

    # Otherwise it's a person
    return node_lookup.get(f"person::{norm_canon}")


# ---------------------------------------------------------------------------
# Build all nodes
# ---------------------------------------------------------------------------

def build_nodes(tools, companies, academic, recursos, otros,
                author_merge, company_names_norm, person_canon):

    # --- 1. Subcategoria (topic) nodes ---
    all_subcats = set()
    for t in tools:
        all_subcats.update(t.get("subcategorias") or [])
    for a in academic:
        if a.get("cat"):
            all_subcats.add(a["cat"])

    for subcat in sorted(all_subcats):
        add_node(
            key=f"subcat::{subcat}",
            label=subcat,
            category="subcategoria",
            type_="topic",
            description=f"Temática: {subcat}",
            source_file="taxonomy",
        )

    # --- 2. Sector nodes ---
    all_sectors = sorted(set(c["sector"] for c in companies if c.get("sector")))
    for sec in all_sectors:
        add_node(
            key=f"sector::{sec}",
            label=sec,
            category="sector",
            type_="sector",
            description=f"Sector: {sec}",
            source_file="taxonomy",
        )

    # --- 3. Program nodes ---
    all_programs = set()
    for t in tools:
        all_programs.update(t.get("programas") or [])
    for prog in sorted(all_programs):
        add_node(
            key=f"prog::{prog}",
            label=prog,
            category="programa",
            type_="program",
            description=f"Software/plataforma: {prog}",
            source_file="taxonomy",
        )

    # --- 4. Company nodes ---
    for c in companies:
        add_node(
            key=f"company::{c['nombre']}",
            label=c["nombre"],
            category="empresas",
            type_=c.get("tipo") or "",
            description=c.get("descripcion") or "",
            url=c.get("url") or "",
            sector=c.get("sector") or "",
            fecha=c.get("fecha") or "",
            source_file="companies",
            extra=json.dumps({"tipo": c.get("tipo") or ""}, ensure_ascii=False),
        )

    # --- 5. Tool nodes ---
    for t in tools:
        subcats_str = "|".join(t.get("subcategorias") or [])
        add_node(
            key=f"tool::{t['nombre']}",
            label=t["nombre"],
            category="herramientas",
            type_=t.get("tipo") or "",
            description=t.get("descripcion") or "",
            url=t.get("url") or "",
            ia=t.get("ia") or "",
            acceso=t.get("acceso") or "",
            subcategoria=subcats_str,
            fecha=t.get("fecha") or "",
            source_file="tools",
            extra=json.dumps({
                "categoria": t.get("categoria") or "",
                "linkType": t.get("linkType") or "",
                "link": t.get("link") or "",
                "imagen": t.get("imagen") or "",
            }, ensure_ascii=False),
        )

    # --- 6. Academic (paper) nodes ---
    for a in academic:
        url = a.get("paperUrl") or a.get("linkUrl") or a.get("liUrl") or ""
        add_node(
            key=f"paper::{a['title']}",
            label=a["title"],
            category="academico",
            type_="paper",
            description=a.get("desc") or "",
            url=url,
            subcategoria=a.get("cat") or "",
            fecha=a.get("fecha") or "",
            source_file="academic",
        )

    # --- 7. Recursos: collection + item nodes ---
    for col in recursos:
        col_key = f"collection::{col['id']}"
        add_node(
            key=col_key,
            label=col["titulo"],
            category="recursos",
            type_="collection",
            description=col.get("descripcion") or "",
            url=col.get("sourceUrl") or "",
            fecha=col.get("fecha") or "",
            source_file="recursos",
            extra=json.dumps({
                "autor": col.get("autor") or "",
                "sourceLabel": col.get("sourceLabel") or "",
            }, ensure_ascii=False),
        )
        for item in col["items"]:
            add_node(
                key=f"recitem::{col['id']}::{item['nombre']}",
                label=item["nombre"],
                category="recursos",
                type_="collection_item",
                description=item.get("descripcion") or "",
                url=item.get("link") or "",
                source_file="recursos",
                extra=json.dumps({"collection": col["id"]}, ensure_ascii=False),
            )

    # --- 8. Otros (archived post) nodes ---
    for i, o in enumerate(otros):
        add_node(
            key=f"otros::{i}::{o['url']}",
            label=truncate(o.get("razon") or f"Post {i}", 80),
            category="otros",
            type_="archived_post",
            description=o.get("razon") or "",
            url=o.get("url") or "",
            fecha=o.get("fecha") or "",
            source_file="otros",
            extra=json.dumps({"autor": o.get("autor") or ""}, ensure_ascii=False),
        )

    # --- 9. Person nodes ---
    for norm_canon, canonical_raw in sorted(person_canon.items()):
        add_node(
            key=f"person::{norm_canon}",
            label=canonical_raw,
            category="persona",
            type_="person",
            description=f"Autor: {canonical_raw}",
            source_file="persons",
        )


# ---------------------------------------------------------------------------
# Build all edges
# ---------------------------------------------------------------------------

def build_edges(tools, companies, academic, recursos, otros,
                author_merge, company_names_norm):

    # --- 1. Tool → Author (CREATED_BY) ---
    for t in tools:
        tool_id = node_lookup[f"tool::{t['nombre']}"]
        author_id = resolve_autor(t["autor"], author_merge, company_names_norm)
        if author_id:
            add_edge(tool_id, author_id, "CREATED_BY", 3, "created by")

    # --- 2+3. Tool ↔ Company (DEVELOPED_BY / DEVELOPS) ---
    # Track pairs to set bidirectional flag and avoid duplicates
    dev_pairs = set()  # (tool_id, company_id)

    # From tools.empresa field
    for t in tools:
        if t.get("empresa"):
            tool_id = node_lookup[f"tool::{t['nombre']}"]
            comp_id = node_lookup.get(f"company::{t['empresa']}")
            if comp_id:
                pair = (tool_id, comp_id)
                if pair not in dev_pairs:
                    add_edge(tool_id, comp_id, "DEVELOPED_BY", 4, "developed by")
                    dev_pairs.add(pair)

    # From companies.herramientas field
    for c in companies:
        for h in c.get("herramientas") or []:
            comp_id = node_lookup[f"company::{c['nombre']}"]
            tool_id = node_lookup.get(f"tool::{h}")
            if tool_id:
                pair_fwd = (comp_id, tool_id)
                if pair_fwd not in dev_pairs:
                    # Check if reverse DEVELOPED_BY already exists
                    has_reverse = (tool_id, comp_id) in dev_pairs
                    add_edge(comp_id, tool_id, "DEVELOPS", 4, "develops",
                             bidirectional=1 if has_reverse else 0)
                    dev_pairs.add(pair_fwd)
                    # Retroactively mark reverse edge as bidirectional
                    if has_reverse:
                        for e in edges:
                            if (e["source_id"] == tool_id
                                    and e["target_id"] == comp_id
                                    and e["relationship"] == "DEVELOPED_BY"):
                                e["bidirectional"] = 1
                                break

    # --- 4. Tool → Program (RUNS_ON) ---
    for t in tools:
        tool_id = node_lookup[f"tool::{t['nombre']}"]
        for prog in t.get("programas") or []:
            prog_id = node_lookup.get(f"prog::{prog}")
            if prog_id:
                add_edge(tool_id, prog_id, "RUNS_ON", 2, "runs on")

    # --- 5. Tool → Subcategoria (CLASSIFIED_AS) ---
    for t in tools:
        tool_id = node_lookup[f"tool::{t['nombre']}"]
        for subcat in t.get("subcategorias") or []:
            subcat_id = node_lookup.get(f"subcat::{subcat}")
            if subcat_id:
                add_edge(tool_id, subcat_id, "CLASSIFIED_AS", 1, "classified as")

    # --- 6. Academic → Author (WRITTEN_BY) ---
    for a in academic:
        paper_id = node_lookup[f"paper::{a['title']}"]
        author_id = resolve_autor(a["autor"], author_merge, company_names_norm)
        if author_id:
            add_edge(paper_id, author_id, "WRITTEN_BY", 3, "written by")

    # --- 7. Academic → Topic (COVERS_TOPIC) ---
    for a in academic:
        if a.get("cat"):
            paper_id = node_lookup[f"paper::{a['title']}"]
            subcat_id = node_lookup.get(f"subcat::{a['cat']}")
            if subcat_id:
                add_edge(paper_id, subcat_id, "COVERS_TOPIC", 2, "covers topic")

    # --- 8. Collection → Item (INCLUDES) + cross-links ---
    for col in recursos:
        col_id = node_lookup[f"collection::{col['id']}"]
        for item in col["items"]:
            item_id = node_lookup[f"recitem::{col['id']}::{item['nombre']}"]
            add_edge(col_id, item_id, "INCLUDES", 3, "includes")

            # Cross-link: recitem → tool (manual table, case-insensitive)
            item_key = item["nombre"].lower()
            tool_nombre = RECITEM_TO_TOOL.get(item_key)
            if tool_nombre:
                tool_id = node_lookup.get(f"tool::{tool_nombre}")
                if tool_id:
                    add_edge(item_id, tool_id, "SAME_AS", 2, "same as")

            # Cross-link: recitem → program (case-insensitive)
            prog_name = RECITEM_TO_PROG.get(item_key)
            if prog_name:
                prog_id = node_lookup.get(f"prog::{prog_name}")
                if prog_id:
                    add_edge(item_id, prog_id, "SAME_AS", 2, "same as")

    # --- 9. Otros → Author (POSTED_BY) ---
    for i, o in enumerate(otros):
        otros_id = node_lookup[f"otros::{i}::{o['url']}"]
        author_id = resolve_autor(o["autor"], author_merge, company_names_norm)
        if author_id:
            add_edge(otros_id, author_id, "POSTED_BY", 1, "posted by")

    # --- 10. SIMILAR_PURPOSE (star pattern within each subcategoria, ≥3 tools) ---
    subcat_tools = defaultdict(list)
    for t in tools:
        for s in t.get("subcategorias") or []:
            subcat_tools[s].append(t["nombre"])

    similar_pairs = set()
    for subcat, tool_list in subcat_tools.items():
        if len(tool_list) < 3:
            continue
        hub_name = sorted(tool_list)[0]
        hub_id = node_lookup[f"tool::{hub_name}"]
        for other_name in tool_list:
            if other_name == hub_name:
                continue
            other_id = node_lookup[f"tool::{other_name}"]
            pair = tuple(sorted([hub_id, other_id]))
            if pair not in similar_pairs:
                add_edge(hub_id, other_id, "SIMILAR_PURPOSE", 1, "similar purpose")
                similar_pairs.add(pair)

    # --- 11. Company → Sector (OPERATES_IN) ---
    for c in companies:
        if c.get("sector"):
            comp_id = node_lookup[f"company::{c['nombre']}"]
            sector_id = node_lookup.get(f"sector::{c['sector']}")
            if sector_id:
                add_edge(comp_id, sector_id, "OPERATES_IN", 1, "operates in")


# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------

def write_csvs():
    nodes_path = os.path.join(DATA_DIR, "thought_map_nodes.csv")
    edges_path = os.path.join(DATA_DIR, "thought_map_edges.csv")

    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=NODE_FIELDS)
        w.writeheader()
        w.writerows(nodes)

    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EDGE_FIELDS)
        w.writeheader()
        w.writerows(edges)

    return nodes_path, edges_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tools = load_json("tools.json")
    companies = load_json("companies.json")
    academic = load_json("academic.json")
    recursos = load_json("recursos.json")
    otros = load_json("otros.json")

    author_merge, company_names_norm, person_canon = build_person_lookup(
        tools, academic, otros, companies
    )

    build_nodes(tools, companies, academic, recursos, otros,
                author_merge, company_names_norm, person_canon)

    build_edges(tools, companies, academic, recursos, otros,
                author_merge, company_names_norm)

    # Verify: all edge node IDs exist in nodes
    node_ids = {n["id"] for n in nodes}
    missing = [
        (e["source_id"], e["target_id"], e["relationship"])
        for e in edges
        if e["source_id"] not in node_ids or e["target_id"] not in node_ids
    ]
    if missing:
        print(f"WARNING: {len(missing)} edges reference missing node IDs:")
        for m in missing[:10]:
            print(f"  {m}")

    nodes_path, edges_path = write_csvs()

    # Summary
    from collections import Counter
    node_cats = Counter(n["category"] for n in nodes)
    edge_rels = Counter(e["relationship"] for e in edges)

    print(f"\nNodes: {len(nodes)}")
    for cat, count in sorted(node_cats.items()):
        print(f"  {cat}: {count}")

    print(f"\nEdges: {len(edges)}")
    for rel, count in sorted(edge_rels.items()):
        print(f"  {rel}: {count}")

    print(f"\nWrote:\n  {nodes_path}\n  {edges_path}")


if __name__ == "__main__":
    main()
