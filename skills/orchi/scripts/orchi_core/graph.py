"""Disposable graph projection over an already resolved authority snapshot.

No graph database is authoritative or required. Projection is rebuilt in memory;
JSON and the self-contained HTML map can be deleted without affecting execution.
Controller-derived coverage is structural, never proof inferred from similarity.
"""
from __future__ import annotations

from collections import deque
import fnmatch
import json
from pathlib import Path, PurePosixPath

from .common import OrchiError, digest, require
from . import intent, ontology

RELATIONS = ontology.RELATIONS | {"addressed_by"}
SOURCE_FIELDS = ("target", "role", "layer", "kind", "area", "source_commit", "source_path", "content_hash",
                 "initiative_id", "intent_revision", "intent_digest", "knowledge_revision")


def _node_id(role: str, target: str) -> str:
    return role + ":" + target


def project(repo, state: dict, snapshot) -> dict:
    records = snapshot.records
    scoped = snapshot.identity.get("initiative_id") is not None
    view = snapshot.identity["view"]
    has_target = scoped and view in {"target", "all"} and bool(state.get("intent"))
    manifest = intent.accepted(repo, state)["manifest"] if has_target else {"requirements": {}, "architecture": []}
    code_commit = snapshot.identity.get("knowledge_head", snapshot.identity["canonical_commit"])
    files = repo.files(code_commit)
    nodes, edges, diagnostics = {}, {}, list(snapshot.diagnostics)
    refs = {}

    def node(identifier, **attributes):
        nodes.setdefault(identifier, {"id": identifier, **attributes})
        return identifier

    def edge(source, relation, target, origin, **attributes):
        if source is None or target is None:
            return
        key = (source, relation, target, origin)
        edges[key] = {"source": source, "relation": relation, "target": target, "origin": origin, **attributes}

    for target, rec in sorted(records.items()):
        identifier = _node_id(rec["role"], target)
        node(identifier, **{k: rec.get(k) for k in SOURCE_FIELDS}, node_type="knowledge", label=target)
        refs[target] = identifier
    for rid, ref in sorted(manifest["requirements"].items()):
        doc, _, anchor = ref.partition("#")
        if doc not in records:
            continue
        rec = records[doc]
        identifier = node("requirement:" + rid, **{k: rec.get(k) for k in SOURCE_FIELDS if k != "target"},
                          node_type="requirement", target=ref, requirement_id=rid, label=rid)
        refs[rid] = refs[ref] = identifier
        edge(identifier, "part_of", refs[doc], "hierarchy")

    def resolve(origin, raw):
        try:
            ref = ontology.reference(origin, raw, manifest["requirements"])
            if ref in refs:
                return refs[ref]
            doc, _, anchor = ref.partition("#")
            if doc in records and anchor in ontology.anchors(records[doc]["content"])[0]:
                rec = records[doc]
                identifier = node(_node_id(rec["role"], ref), **{k: rec.get(k) for k in SOURCE_FIELDS if k != "target"},
                                  node_type="section", target=ref, label=ref)
                refs[ref] = identifier
                edge(identifier, "part_of", refs[doc], "hierarchy")
                return identifier
            diagnostics.append({"code": "UNRESOLVED_GRAPH_REFERENCE", "target": origin, "reference": raw})
        except OrchiError as exc:
            diagnostics.append({"code": exc.code, "target": origin, "reference": raw})
        return None

    def artifact(p, planned=False):
        identifier = ("planned-artifact:" if planned else "implementation:") + p
        return node(identifier, target=p, label=p, node_type="artifact", role="target" if planned else "implementation",
                    status="planned" if planned else "present" if p in files else "removed",
                    source_commit=None if planned else code_commit,
                    git_blob=None if planned or p not in files else files[p][1])

    known_evidence = {e["id"]: e for e in state.get("evidence", [])} if scoped else {}

    def evidence(eid):
        if eid not in known_evidence:
            diagnostics.append({"code": "UNKNOWN_EVIDENCE", "target": "evidence:" + eid})
            return None
        rec = known_evidence[eid]
        return node("evidence:" + eid, target="evidence:" + eid, role="evidence", node_type="evidence", label="Checks " + eid[:12],
                    passed=rec["passed"], checks=sorted(rec["checks"]), source_commit=rec.get("commit"), evidence_id=eid)

    for target, rec in sorted(records.items()):
        source = refs[target]
        fm = ontology.frontmatter(rec["content"])
        for p in rec.get("artifacts", []):
            try:
                ontology.artifact_pattern(p)
                matches = [name for name in sorted(files) if fnmatch.fnmatchcase(name, p)]
                if rec["role"] == "target" and not matches:
                    matches = [p]
                for name in matches:
                    edge(source, "implemented_by", artifact(name, rec["role"] == "target"), "ownership",
                         status="planned" if rec["role"] == "target" else "documented")
            except OrchiError as exc:
                diagnostics.append({"code": exc.code, "target": target, "reference": p})
        relations = fm.get("relations", {})
        if not isinstance(relations, dict):
            diagnostics.append({"code": "INVALID_RELATIONS", "target": target})
            relations = {}
        for relation, values in sorted(relations.items()):
            if relation not in ontology.RELATIONS or not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                diagnostics.append({"code": "INVALID_RELATION", "target": target, "reference": relation})
                continue
            for raw in sorted(values):
                if relation in ontology.IMPLEMENTATION_RELATIONS:
                    try:
                        ontology.artifact_pattern(raw)
                        matches = [p for p in sorted(files) if fnmatch.fnmatchcase(p, raw)]
                        if rec["role"] == "target" and not matches:
                            matches = [raw]
                        for p in matches:
                            edge(source, relation, artifact(p, rec["role"] == "target"), "ontology",
                                 status="planned" if rec["role"] == "target" else "documented")
                    except OrchiError as exc:
                        diagnostics.append({"code": exc.code, "target": target, "reference": raw})
                elif relation == "verified_by" and raw.startswith("evidence:"):
                    edge(source, relation, evidence(raw[9:]), "ontology")
                else:
                    edge(source, relation, resolve(target, raw), "ontology")
        parent = str(PurePosixPath(target).parent / "README.md")
        if parent in refs and target != parent:
            edge(source, "part_of", refs[parent], "hierarchy")
        if rec.get("evidence") and scoped:
            edge(source, "verified_by", evidence(rec["evidence"]), "controller")

    completed = {e["epic_id"]: e for e in state.get("completed", [])} if scoped else {}
    if scoped:
        for epic in state.get("spec", {}).get("epics", []):
            eid = epic["id"]
            done = completed.get(eid)
            if not has_target and done is None:
                continue
            source = node("epic:" + eid, target="epic:" + eid, role="workflow", node_type="epic", label=eid,
                          status="implemented" if done else "planned", plan_digest=done.get("plan_digest") if done else None)
            if has_target:
                def binding_status(domain, key, ref):
                    if not done:
                        return "planned"
                    expected = {"ref": ref, "content_hash": manifest["documents"].get(ref.split("#")[0].removeprefix("intent/"))}
                    return "closed-target-binding" if done.get("target_bindings", {}).get(domain, {}).get(key) == expected else "stale-target-binding"
                for rid in epic["contributes_to"]:
                    ref = manifest["requirements"].get(rid)
                    if ref:
                        edge(refs.get(rid), "addressed_by", source, "controller", status=binding_status("requirements", rid, ref))
                for ref in epic.get("realizes", []):
                    doc, _, anchor = ref.partition("#")
                    if done and (doc not in records or anchor and anchor not in ontology.anchors(records[doc]["content"])[0]):
                        diagnostics.append({"code": "HISTORICAL_TARGET_REFERENCE", "target": "epic:" + eid, "reference": ref})
                        continue
                    edge(source, "realizes", resolve("intent/architecture/README.md", ref), "controller",
                         status=binding_status("architecture", doc, doc))
                for dependency in epic["depends_on"]:
                    if "epic:" + dependency in nodes:
                        edge(source, "depends_on", "epic:" + dependency, "controller")
            if done and view != "target":
                edge(source, "verified_by", evidence(done["evidence"]), "controller")
                for p in done.get("artifacts", []):
                    edge(source, "implemented_by", artifact(p), "controller", status="checked-epic-output")
    final = state.get("final") if scoped else None
    if final and final.get("verified", {}).get("passed") and view == "all" and final.get("intent_digest") == state["spec"]["intent"]["digest"]:
        proof = evidence(final["verified"]["id"])
        for req in final.get("reconciliation", {}).get("requirements", []):
            if req["disposition"] == "satisfied":
                edge(refs.get(req["requirement_id"]), "verified_by", proof, "controller")
        for arch in final.get("reconciliation", {}).get("architecture", []):
            if arch["disposition"] in {"realized", "deviated"}:
                target = resolve("intent/architecture/README.md", arch["target"])
                edge(target, "verified_by", proof, "controller")
                for p in arch["artifacts"]:
                    edge(target, "implemented_by", artifact(p), "controller", disposition=arch["disposition"])
    output = {"format": "orchi-knowledge-graph", "scope": snapshot.identity["scope"], "view": view,
              "snapshot": snapshot.identity, "nodes": [nodes[k] for k in sorted(nodes)],
              "edges": [edges[k] for k in sorted(edges)],
              "diagnostics": sorted(diagnostics, key=lambda d: json.dumps(d, sort_keys=True))}
    output["fingerprint"] = digest(output)
    return output


def related(projection: dict, target: str, relation: str | None = None, *, depth=1, limit=40, direction="both") -> dict:
    require(relation is None or relation in RELATIONS, "INVALID_RELATION", str(relation))
    require(isinstance(depth, int) and not isinstance(depth, bool) and 1 <= depth <= 3, "INVALID_DEPTH", "Depth must be 1-3")
    require(isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= 100, "INVALID_LIMIT", "Limit must be 1-100")
    require(direction in {"in", "out", "both"}, "INVALID_DIRECTION", direction)
    nodes = {n["id"]: n for n in projection["nodes"]}
    seeds = sorted(k for k, n in nodes.items() if k == target or n.get("target") == target or n.get("requirement_id") == target)
    require(bool(seeds), "MISSING_GRAPH_NODE", target)
    queue = deque((s, 0) for s in seeds)
    seen, paths, selected_edges = set(seeds), {}, {}
    while queue and len(paths) < limit:
        source, distance = queue.popleft()
        if distance >= depth:
            continue
        for edge in projection["edges"]:
            if relation and edge["relation"] != relation:
                continue
            neighbor = None
            orientation = None
            if edge["source"] == source and direction != "in":
                neighbor, orientation = edge["target"], "out"
            elif edge["target"] == source and direction != "out":
                neighbor, orientation = edge["source"], "in"
            if neighbor is None:
                continue
            if neighbor not in seen:
                if len(paths) >= limit:
                    break
                seen.add(neighbor)
                paths[neighbor] = {"distance": distance + 1, "via": {**edge, "direction": orientation}}
                queue.append((neighbor, distance + 1))
            if neighbor in seen:
                selected_edges[(edge["source"], edge["relation"], edge["target"], edge["origin"])] = edge
    return {"scope": projection["scope"], "view": projection["view"], "target": target,
            "fingerprint": projection["fingerprint"], "roots": [nodes[s] for s in seeds],
            "related": [{**nodes[k], **paths[k]} for k in sorted(paths, key=lambda k: (paths[k]["distance"], k))],
            "edges": [selected_edges[k] for k in sorted(selected_edges)], "limit_reached": len(paths) >= limit}


def related_context(projection, primary_matches, limit=8, relation=None):
    primary = {hit["target"] for hit in primary_matches}
    found = {}
    for origin in sorted(primary):
        neighborhood = related(projection, origin, relation, depth=2, limit=100)
        for neighbor in neighborhood["related"]:
            doc = neighbor.get("target", "").split("#")[0]
            if neighbor["node_type"] not in {"knowledge", "section", "requirement"} or doc in primary:
                continue
            key = (neighbor["role"], doc)
            found.setdefault(key, {**{k: neighbor.get(k) for k in SOURCE_FIELDS}, "target": doc,
                                    "primary_match": False, "distance": neighbor["distance"],
                                    "related_to": origin, "via": neighbor["via"]})
    return [found[k] for k in sorted(found, key=lambda k: (found[k]["distance"], k))][:limit]


def coverage(repo, state, initiative_id):
    require(state.get("spec") and initiative_id == state["spec"]["id"], "INITIATIVE_SCOPE", "Select the active initiative explicitly")
    manifest = intent.accepted(repo, state)["manifest"]
    completed = {e["epic_id"]: e for e in state["completed"]}
    final = state.get("final")
    final_valid = final and final.get("verified", {}).get("passed") and final.get("intent_digest") == state["spec"]["intent"]["digest"]
    final_reqs = {r["requirement_id"]: r for r in final["reconciliation"]["requirements"]} if final_valid else {}
    final_arch = {a["target"]: a for a in final["reconciliation"]["architecture"]} if final_valid else {}

    def row(ref, epics, domain, key, final_disposition):
        content_hash = manifest["documents"][ref.split("#")[0].removeprefix("intent/")]
        done = [e for e in epics if e in completed]
        current = [e for e in done if completed[e].get("target_bindings", {}).get(domain, {}).get(key) == {"ref": ref, "content_hash": content_hash}]
        verified = final_disposition and final_disposition["disposition"] in {"satisfied", "realized", "deviated"}
        return {"target": ref, "state": "unresolved" if final_disposition and final_disposition["disposition"] == "unresolved" else "verified" if verified else "implemented" if current else "planned" if epics else "unresolved",
                "planned_epics": epics, "completed_epics": done, "current_target_completed_epics": current,
                "stale_target_epics": [e for e in done if e not in current],
                "epic_evidence": [completed[e]["evidence"] for e in current],
                "final_evidence": final["verified"]["id"] if verified else None,
                "disposition": final_disposition["disposition"] if final_disposition else None,
                "checks": final_disposition["checks"] if final_disposition else []}

    requirements = []
    for rid, ref in sorted(manifest["requirements"].items()):
        epics = [e["id"] for e in state["spec"]["epics"] if rid in e["contributes_to"]]
        requirements.append({"requirement_id": rid, **row(ref, epics, "requirements", rid, final_reqs.get(rid))})
    architecture = []
    for ref in manifest["architecture"]:
        epics = [e["id"] for e in state["spec"]["epics"] if any(r.split("#")[0] == ref for r in e.get("realizes", []))]
        architecture.append(row(ref, epics, "architecture", ref, final_arch.get(ref)))
    return {"format": "orchi-coverage", "initiative_id": initiative_id, "intent_digest": state["spec"]["intent"]["digest"],
            "knowledge_head": state["knowledge_head"], "phase": state["phase"], "requirements": requirements,
            "resolved_requirements": manifest["resolved_requirements"], "architecture": architecture,
            "notice": "Planned links and completed-epic checks are structural traceability, not proof of requirement satisfaction. Verified means explicit final disposition backed by passed trusted candidate checks; publication still requires review and approval."}


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>Orchi knowledge map</title><style>
:root{font-family:system-ui,sans-serif;color:#192a3a;background:#f4f7fa}body{margin:0}header{padding:22px 28px;background:#172c43;color:white}h1{font-size:24px;margin:0 0 8px}.meta{font:12px ui-monospace,monospace;overflow-wrap:anywhere}nav{padding:14px 28px;display:flex;gap:16px;flex-wrap:wrap;align-items:center;background:white;border-bottom:1px solid #ccd6df}input[type=search]{padding:9px 12px;width:270px;border:1px solid #b8c6d1;border-radius:5px}main{display:grid;grid-template-columns:minmax(0,1fr) 360px}#canvas{overflow:auto;padding:20px}svg{min-width:1000px;width:100%;background:white;border:1px solid #dce3e9}aside{background:white;padding:20px;border-left:1px solid #dce3e9;overflow-wrap:anywhere}h2{font-size:17px}pre{white-space:pre-wrap;font-size:11px}line{stroke:#a7b6c4;stroke-width:1.1;opacity:.45}line.active{stroke:#172c43;stroke-width:2.3;opacity:1}g{cursor:pointer}g text{font-size:11px;fill:#152a3d}g.selected rect{stroke:#111;stroke-width:3}.hint{font-size:12px;line-height:1.6}.edge{padding:8px 0;border-bottom:1px solid #edf0f3;font-size:12px}button{border:1px solid #b8c6d1;background:white;border-radius:4px;padding:6px 10px;cursor:pointer}@media(max-width:850px){main{grid-template-columns:1fr}aside{border-left:0}}
</style></head><body><header><h1>Orchi knowledge map</h1><div class="meta" id="identity"></div></header><nav><input type="search" id="query" placeholder="Filter node paths or labels"><span id="roles"></span><button id="reset">Reset selection</button><span id="counts"></span></nav><main><div id="canvas"><svg id="graph" role="img" aria-label="Authority-scoped knowledge graph"></svg><p class="hint">Edges are structural relationships, not lexical relevance or inferred proof. Click a node to inspect exact provenance and relations. Large maps display the first 300 matching nodes; narrow the filter to inspect the rest.</p></div><aside><h2 id="title">Select a node</h2><pre id="detail"></pre><div id="edges"></div></aside></main><script id="data" type="application/json">__DATA__</script><script>
'use strict';const data=JSON.parse(document.getElementById('data').textContent),roles=['current','target','workflow','implementation','evidence'],palette={current:'#d9edf8',target:'#fce8bf',workflow:'#e4dff5',implementation:'#d9eee1',evidence:'#f1dfe8'},enabled=new Set(roles);let selected=null;
const byId=new Map(data.nodes.map(n=>[n.id,n])),svg=document.getElementById('graph'),ns='http://www.w3.org/2000/svg';document.getElementById('identity').textContent=data.scope+' | '+data.view+' | '+data.fingerprint;
function element(name,attrs){const e=document.createElementNS(ns,name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e}
for(const role of roles){const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=true;input.onchange=()=>{input.checked?enabled.add(role):enabled.delete(role);draw()};label.append(input,document.createTextNode(role+' '));document.getElementById('roles').append(label)}
function select(id){selected=id;const n=byId.get(id);document.getElementById('title').textContent=n.label;document.getElementById('detail').textContent=JSON.stringify(n,null,2);const list=document.getElementById('edges');list.replaceChildren();for(const e of data.edges.filter(e=>e.source===id||e.target===id)){const div=document.createElement('div');div.className='edge';div.textContent=(byId.get(e.source)?.label||e.source)+' --'+e.relation+'--> '+(byId.get(e.target)?.label||e.target)+' ['+e.origin+']';list.append(div)}draw()}
function draw(){const query=document.getElementById('query').value.toLowerCase(),visible=data.nodes.filter(n=>enabled.has(n.role)&&JSON.stringify(n).toLowerCase().includes(query)),shown=visible.slice(0,300),positions=new Map(),rows=Object.fromEntries(roles.map(r=>[r,0]));for(const n of shown){positions.set(n.id,{x:roles.indexOf(n.role)*225+15,y:45+rows[n.role]++*48})}const height=Math.max(400,80+Math.max(...Object.values(rows))*48);svg.setAttribute('viewBox','0 0 1135 '+height);svg.style.height=height+'px';svg.replaceChildren();for(let i=0;i<roles.length;i++){const t=element('text',{x:i*225+20,y:24,'font-size':14,'font-weight':600});t.textContent=roles[i];svg.append(t)}for(const e of data.edges){const a=positions.get(e.source),b=positions.get(e.target);if(a&&b){const line=element('line',{x1:a.x+100,y1:a.y+16,x2:b.x+100,y2:b.y+16});if(e.source===selected||e.target===selected)line.classList.add('active');svg.append(line)}}for(const n of shown){const p=positions.get(n.id),g=element('g',{transform:'translate('+p.x+','+p.y+')',tabindex:0,role:'button','aria-label':n.label});if(n.id===selected)g.classList.add('selected');g.append(element('rect',{width:205,height:34,rx:5,fill:palette[n.role],stroke:'#bdcbd7'}));const t=element('text',{x:8,y:21});t.textContent=n.label.length>30?n.label.slice(0,27)+'...':n.label;g.append(t);const title=element('title',{});title.textContent=n.label;g.append(title);g.onclick=()=>select(n.id);g.onkeydown=e=>{if(e.key==='Enter')select(n.id)};svg.append(g)}document.getElementById('counts').textContent=shown.length+'/'+visible.length+' nodes | '+data.edges.length+' edges'}
document.getElementById('query').oninput=draw;document.getElementById('reset').onclick=()=>{selected=null;document.getElementById('title').textContent='Select a node';document.getElementById('detail').textContent='';document.getElementById('edges').replaceChildren();draw()};draw();
</script></body></html>
'''


def html(projection: dict) -> str:
    # No source prose is rendered as HTML; JSON cannot terminate its script element.
    data = json.dumps(projection, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return _HTML.replace("__DATA__", data)


def write_map(projection: dict, output: str | Path) -> dict:
    output = Path(output)
    require(not any(p.is_symlink() for p in [output, *output.parents]), "UNSAFE_PATH", str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html(projection), encoding="utf-8")
    return {"path": str(output), "scope": projection["scope"], "view": projection["view"],
            "fingerprint": projection["fingerprint"], "nodes": len(projection["nodes"]), "edges": len(projection["edges"]),
            "derived": True, "diagnostics": projection["diagnostics"]}
