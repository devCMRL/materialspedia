import json
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "materials_map.json"


@st.cache_data
def load_tree() -> Dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_tree(
    node: Dict,
    path: Optional[List[str]] = None,
    top_branch: Optional[str] = None,
) -> List[Dict]:
    path = (path or []) + [node["name"]]
    if len(path) >= 2 and top_branch is None:
        top_branch = path[1]

    record = {
        "id": node["id"],
        "name": node["name"],
        "description": node.get("description", ""),
        "tags": node.get("tags", []),
        "path": path,
        "depth": len(path) - 1,
        "top_branch": top_branch or node["name"],
        "children_count": len(node.get("children", [])),
    }

    rows = [record]
    for child in node.get("children", []):
        rows.extend(flatten_tree(child, path, top_branch))
    return rows


def build_index(
    node: Dict,
    index: Optional[Dict[str, Dict]] = None,
    parent: Optional[str] = None,
) -> Dict[str, Dict]:
    index = index or {}
    copied = dict(node)
    copied["_parent"] = parent
    index[node["id"]] = copied

    for child in node.get("children", []):
        build_index(child, index, node["id"])

    return index


def search_nodes(records: List[Dict], query: str, branch_filter: List[str]) -> List[Dict]:
    q = query.strip().lower()
    matches = []

    for rec in records:
        if branch_filter and rec["top_branch"] not in branch_filter and rec["depth"] != 0:
            continue

        haystack = " ".join(
            [
                rec["name"],
                rec["description"],
                " ".join(rec.get("tags", [])),
                " ".join(rec.get("path", [])),
            ]
        ).lower()

        if q in haystack:
            score = 0
            if q == rec["name"].lower():
                score += 20
            if q in rec["name"].lower():
                score += 10
            if any(q in tag.lower() for tag in rec.get("tags", [])):
                score += 5
            score -= rec["depth"] * 0.2
            matches.append((score, rec))

    matches.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [rec for _, rec in matches[:25]]


def children_of(node: Dict) -> List[Dict]:
    return node.get("children", [])


def breadcrumb(index: Dict[str, Dict], node_id: str) -> List[Dict]:
    trail = []
    current = index[node_id]

    while current:
        trail.append(current)
        parent_id = current.get("_parent")
        current = index.get(parent_id) if parent_id else None

    trail.reverse()
    return trail


def subtree_preview(node: Dict, depth: int = 0, max_depth: int = 2) -> List[str]:
    lines = []
    if depth > max_depth:
        return lines

    prefix = "  " * depth + ("• " if depth > 0 else "")
    if depth == 0:
        lines.append(node["name"])
    else:
        lines.append(prefix + node["name"])

    for child in node.get("children", []):
        lines.extend(subtree_preview(child, depth + 1, max_depth))

    return lines


def set_selected(node_id: str) -> None:
    st.session_state.selected_id = node_id


st.set_page_config(
    page_title="Materials Science Explorer",
    page_icon="🧪",
    layout="wide",
)

tree = load_tree()
index = build_index(tree)
records = flatten_tree(tree)
top_branches = [child["name"] for child in tree.get("children", [])]

if "selected_id" not in st.session_state or st.session_state.selected_id not in index:
    st.session_state.selected_id = tree["id"]

selected = index[st.session_state.selected_id]

st.title("Materials Science Explorer")
st.caption("Starter app for an interactive, browser-based materials science mind map.")

with st.sidebar:
    st.header("Search + filters")

    query = st.text_input(
        "Search topics",
        placeholder="e.g. dislocations, CALPHAD, CVD, piezoelectric",
    )

    selected_branches = st.multiselect(
        "Top-level branches",
        options=top_branches,
        default=top_branches,
    )

    st.button(
        "Reset to root",
        use_container_width=True,
        on_click=set_selected,
        args=(tree["id"],),
    )

    st.divider()
    st.subheader("Quick navigation")
    for branch in tree.get("children", []):
        st.button(
            branch["name"],
            key=f"nav_{branch['id']}",
            use_container_width=True,
            on_click=set_selected,
            args=(branch["id"],),
        )

    if query.strip():
        st.divider()
        st.subheader("Search results")
        results = search_nodes(records, query, selected_branches)

        if results:
            for rec in results:
                label = f"{rec['name']}  ·  {rec['top_branch']}"
                st.button(
                    label,
                    key=f"search_{rec['id']}",
                    use_container_width=True,
                    on_click=set_selected,
                    args=(rec["id"],),
                )
        else:
            st.info("No matches found. Try a broader term.")

left, right = st.columns([2.2, 1.1], gap="large")

with left:
    trail = breadcrumb(index, selected["id"])
    st.markdown(" / ".join([item["name"] for item in trail]))

    top1, top2 = st.columns([3, 1])

    with top1:
        st.subheader(selected["name"])
        st.write(selected.get("description", ""))

    with top2:
        parent_id = selected.get("_parent")
        if parent_id:
            st.button(
                "⬅ Back to parent",
                use_container_width=True,
                on_click=set_selected,
                args=(parent_id,),
            )

    meta_cols = st.columns(3)
    meta_cols[0].metric("Children", len(selected.get("children", [])))
    meta_cols[1].metric("Depth", len(trail) - 1)
    meta_cols[2].metric("Total topics", len(records) - 1)

    if selected.get("tags"):
        st.caption("Tags: " + ", ".join(selected["tags"]))

    st.markdown("### Explore children")
    kids = children_of(selected)

    if kids:
        cols = st.columns(3)
        for i, child in enumerate(kids):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{child['name']}**")
                    st.write(child.get("description", ""))
                    st.button(
                        "Open",
                        key=f"open_{child['id']}",
                        use_container_width=True,
                        on_click=set_selected,
                        args=(child["id"],),
                    )
    else:
        st.success("This is currently a leaf topic. You can go back to the parent or search for another branch.")
        
    with st.expander("Local tree preview", expanded=False):
        preview_depth = st.selectbox(
            "Preview depth",
            options=[1, 2, 3, 4],
            index=1,
            key=f"preview_depth_{selected['id']}",
        )
        preview_lines = subtree_preview(selected, max_depth=preview_depth)
        st.code("\n".join(preview_lines), language="text")

with right:
    st.markdown("### Notes for selected topic")
    st.info(selected.get("description", "No description yet."))

    st.markdown("### Path")
    for item in trail:
        st.write("• " + item["name"])

    siblings = []
    if selected.get("_parent"):
        parent = index[selected["_parent"]]
        siblings = [c["name"] for c in parent.get("children", []) if c["id"] != selected["id"]]

    if siblings:
        st.markdown("### Related sibling topics")
        for sib in siblings[:8]:
            st.write("• " + sib)

    if selected.get("children"):
        st.markdown("### Suggested next clicks")
        for child in selected.get("children", [])[:8]:
            st.button(
                f"→ {child['name']}",
                key=f"next_{child['id']}",
                use_container_width=True,
                on_click=set_selected,
                args=(child["id"],),
            )

st.divider()
with st.expander("About this starter app"):
    st.write(
        """
        This is version 1.0, I will launch V 1.1 soon.
        """
    )
    st.write(
        """
        Upcoming upgrades:
        1. True interactive graph view.
        2. Notes pages per topic.
        3. Citations, links, and paper/software cards.
        4. Map categorization into curriculum mode, research mode, and career mode.
        """
    )
