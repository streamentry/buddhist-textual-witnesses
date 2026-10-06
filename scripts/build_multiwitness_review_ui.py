#!/usr/bin/env python3
"""Build a self-contained human-review UI for a multi-witness case study."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from review_evidence import alignment_evidence_digest, alignment_source_revisions

SUPPLIED_RE = re.compile(r"<supplied>(.*?)</supplied>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_index(pali: Path, chinese: Path, indic: Path) -> dict[str, dict[str, Any]]:
    return {
        **{row["unit_id"]: row for row in load_jsonl(pali)},
        **{row["block_id"]: row for row in load_jsonl(chinese)},
        **{row["unit_id"]: row for row in load_jsonl(indic)},
    }


def clean_text(value: str) -> str:
    return html.unescape(" ".join(TAG_RE.sub("", value).split()))


def render_sanskrit_html(value: str) -> str:
    out: list[str] = []
    cursor = 0
    for match in SUPPLIED_RE.finditer(value):
        before = clean_text(value[cursor:match.start()])
        supplied = clean_text(match.group(1))
        if before:
            out.append(html.escape(before))
        out.append(
            '<span class="supplied" title="Editorially supplied in the upstream edition">'
            + html.escape(supplied)
            + "</span>"
        )
        cursor = match.end()
    tail = clean_text(value[cursor:])
    if tail:
        out.append(html.escape(tail))
    return " ".join(part for part in out if part)


def row_text_html(row: dict[str, Any]) -> str:
    if row.get("language") == "san":
        return render_sanskrit_html(str(row.get("edition_text", "")))
    value = row.get("text") or row.get("search_text") or ""
    return html.escape(" ".join(str(value).split()))


def source_meta(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source") or {}
    locator = row.get("locator") or row.get("discourse_locator") or {}
    urls = []
    for key in ("root_url", "html_url", "url"):
        value = source.get(key)
        if value and value not in urls:
            urls.append(value)
    return {
        "project": source.get("project"),
        "revision": source.get("revision"),
        "path": source.get("path") or source.get("root_path"),
        "start_ref": locator.get("start_ref"),
        "end_ref": locator.get("end_ref"),
        "urls": urls,
    }


def case_payload(
    case: dict[str, Any],
    reviews: dict[str, Any],
    idx: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    review_map: dict[str, list[dict[str, Any]]] = {}
    for review in reviews.get("reviews", []):
        review_map.setdefault(review["alignment_id"], []).append(review)

    alignments = []
    for alignment in case["alignments"]:
        members = []
        for member in alignment["members"]:
            units = []
            for source_id in member["source_unit_ids"]:
                row = idx[source_id]
                units.append(
                    {
                        "source_id": source_id,
                        "text_html": row_text_html(row),
                        "meta": source_meta(row),
                    }
                )
            members.append({**member, "units": units})
        alignments.append(
            {
                **alignment,
                "members": members,
                "existing_reviews": review_map.get(
                    alignment["alignment_id"], []
                ),
                "evidence_snapshot": {
                    "digest": alignment_evidence_digest(
                        case["case_study_id"], alignment, idx
                    ),
                    "source_revisions": alignment_source_revisions(
                        alignment, idx
                    ),
                },
            }
        )
    return {
        "case_study_id": case["case_study_id"],
        "title": case["title"],
        "scope": case.get("scope", ""),
        "epistemic_policy": case.get("epistemic_policy", ""),
        "witnesses": case.get("witnesses", []),
        "alignments": alignments,
        "review_count": len(reviews.get("reviews", [])),
    }


def safe_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")


def build_page(payload: dict[str, Any]) -> str:
    data = safe_json(payload)
    title = html.escape(payload["title"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Review UI</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f4f1e9;
  --paper: #fffdf7;
  --ink: #1e211f;
  --muted: #69706b;
  --line: #d7d2c6;
  --accent: #215c50;
  --accent-soft: #dcebe6;
  --warn: #8b4b12;
  --supplied: #fff0a8;
  --code: #eee9dc;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#151817;--paper:#1e2220;--ink:#f1efe8;--muted:#a8afa9;
    --line:#3a403c;--accent:#89cdbb;--accent-soft:#243e37;
    --warn:#e9a160;--supplied:#66571c;--code:#2a2f2c;
  }}
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}}
button,input,select,textarea {{ font:inherit; }}
a {{ color:var(--accent); }}
header {{
  position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--paper) 94%,transparent);
  border-bottom:1px solid var(--line);backdrop-filter:blur(14px);
}}
.header-inner {{ max-width:1500px;margin:auto;padding:16px 22px;display:flex;gap:18px;align-items:center;justify-content:space-between; }}
h1 {{ margin:0;font-size:18px;letter-spacing:-.02em; }}
.badge {{ display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:3px 9px;font-size:12px;color:var(--muted); }}
.layout {{ max-width:1500px;margin:auto;display:grid;grid-template-columns:270px minmax(0,1fr);gap:18px;padding:18px; }}
aside {{ position:sticky;top:76px;height:calc(100vh - 94px);overflow:auto;background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:12px; }}
aside input {{ width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:10px;background:transparent;color:var(--ink);margin-bottom:10px; }}
.nav-item {{ display:block;width:100%;text-align:left;border:0;background:transparent;color:var(--ink);padding:9px;border-radius:10px;cursor:pointer; }}
.nav-item:hover,.nav-item.active {{ background:var(--accent-soft); }}
.nav-item small {{ display:block;color:var(--muted);margin-top:2px; }}
main {{ min-width:0; }}
.notice {{ background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:15px 18px;margin-bottom:16px; }}
.notice strong {{ color:var(--warn); }}
.alignment {{ display:none; }}
.alignment.active {{ display:block; }}
.card {{ background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px;margin-bottom:16px;box-shadow:0 6px 24px rgba(0,0,0,.035); }}
.card h2 {{ margin:0 0 5px;font-size:24px;letter-spacing:-.03em; }}
.meta-row {{ display:flex;flex-wrap:wrap;gap:7px;margin:10px 0 0; }}
.witness-grid {{ display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:14px 0; }}
.witness {{ border:1px solid var(--line);border-radius:14px;overflow:hidden;min-width:0;background:color-mix(in srgb,var(--paper) 93%,var(--accent-soft)); }}
.witness-head {{ padding:10px 12px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:8px; }}
.witness-body {{ padding:12px; }}
.source-unit {{ border-bottom:1px dashed var(--line);padding:0 0 12px;margin:0 0 12px; }}
.source-unit:last-child {{ border-bottom:0;margin-bottom:0;padding-bottom:0; }}
.source-id {{ font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);word-break:break-all; }}
.source-text {{ margin-top:8px;font-family:Georgia,"Noto Serif",serif;font-size:16px;line-height:1.7; }}
.supplied {{ background:var(--supplied);border-radius:3px;padding:0 1px;text-decoration:underline dotted; }}
.provenance {{ margin-top:8px;font-size:11px;color:var(--muted);word-break:break-word; }}
.variants {{ display:grid;gap:8px;margin-top:10px; }}
.variant {{ padding:10px 12px;border-left:3px solid var(--accent);background:var(--accent-soft);border-radius:8px; }}
.review-form {{ display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px; }}
.field {{ display:grid;gap:5px; }}
.field.full {{ grid-column:1/-1; }}
label {{ font-size:12px;color:var(--muted); }}
input,select,textarea {{ width:100%;border:1px solid var(--line);border-radius:9px;padding:9px;background:transparent;color:var(--ink); }}
textarea {{ min-height:100px;resize:vertical; }}
.actions {{ grid-column:1/-1;display:flex;gap:8px;flex-wrap:wrap; }}
button.action {{ border:0;border-radius:10px;padding:9px 12px;background:var(--accent);color:var(--paper);cursor:pointer; }}
button.secondary {{ background:var(--accent-soft);color:var(--ink);border:1px solid var(--line); }}
.json-output {{ min-height:240px;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code); }}
.existing-review {{ padding:10px;border:1px solid var(--line);border-radius:10px;margin-top:8px; }}
@media (max-width:1100px) {{
  .witness-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
}}
@media (max-width:760px) {{
  .layout {{ grid-template-columns:1fr;padding:10px; }}
  aside {{ position:static;height:auto; }}
  .witness-grid,.review-form {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<header><div class="header-inner">
  <div><h1>{title}</h1><span class="badge">human review surface</span></div>
  <span class="badge" id="reviewCount"></span>
</div></header>
<div class="layout">
<aside>
  <input id="filter" placeholder="Filter alignments…">
  <div id="nav"></div>
</aside>
<main>
  <div class="notice">
    <strong>Boundary:</strong> this page never writes to the repository and never promotes an alignment.
    It only prepares a human-review JSON record, including an evidence digest tied to the displayed source units, for you to copy, inspect, and commit through the normal review process.
    Highlighted Sanskrit letters are editorially supplied in the upstream edition.
    Example: <span class="supplied">supplied text</span>.
  </div>
  <div id="content"></div>
</main>
</div>
<script>
const DATA = {data};
const LANG_ORDER = ["pli","lzh","lzh","san"];
const WITNESS_ORDER = ["DN 14","DA 1","EA 48.4","SF 36"];
let activeId = DATA.alignments.length ? DATA.alignments[0].alignment_id : null;

function esc(value) {{
  return String(value == null ? "" : value)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}}

function slug(value) {{
  return String(value || "reviewer").toLowerCase()
    .normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"") || "reviewer";
}}

function unitMeta(unit) {{
  const m = unit.meta || {{}};
  const bits = [];
  if (m.project) bits.push(m.project);
  if (m.path) bits.push(m.path);
  if (m.start_ref || m.end_ref) bits.push((m.start_ref || "?") + " → " + (m.end_ref || "?"));
  if (m.revision) bits.push("rev " + String(m.revision).slice(0,12));
  let links = "";
  if ((m.urls || []).length) {{
    links = " · " + m.urls.map((url,i) => '<a href="' + esc(url) + '" target="_blank" rel="noopener">source ' + (i+1) + '</a>').join(" · ");
  }}
  return esc(bits.join(" · ")) + links;
}}

function witnessCard(member) {{
  const units = member.units.map(unit =>
    '<div class="source-unit">' +
      '<div class="source-id">' + esc(unit.source_id) + '</div>' +
      '<div class="source-text">' + unit.text_html + '</div>' +
      '<div class="provenance">' + unitMeta(unit) + '</div>' +
    '</div>'
  ).join("");
  return '<article class="witness">' +
    '<div class="witness-head"><strong>' + esc(member.witness_id) + '</strong><span class="badge">' + esc(member.coverage) + '</span></div>' +
    '<div class="witness-body">' + units +
      (member.notes ? '<p class="provenance">' + esc(member.notes) + '</p>' : '') +
    '</div></article>';
}}

function reviewForm(a) {{
  const key = a.alignment_id.replace(/[^a-zA-Z0-9]/g,"_");
  const existing = (a.existing_reviews || []).map(r =>
    '<div class="existing-review"><strong>' + esc(r.decision) + '</strong> · ' +
    esc((r.reviewer || {{}}).name || "unknown") + ' · ' + esc(r.reviewed_on || "") + '</div>'
  ).join("");
  return '<div class="card"><h3>Human review</h3>' +
    (existing ? '<div><p>Existing committed reviews:</p>' + existing + '</div>' : '<p class="provenance">No committed human review for this alignment yet.</p>') +
    '<div class="review-form" data-review-form="' + esc(a.alignment_id) + '">' +
      '<div class="field"><label>Reviewer name</label><input data-f="name" placeholder="Required human name"></div>' +
      '<div class="field"><label>Affiliation</label><input data-f="affiliation" placeholder="Optional"></div>' +
      '<div class="field"><label>Identifier (ORCID etc.)</label><input data-f="identifier" placeholder="Optional"></div>' +
      '<div class="field"><label>Decision</label><select data-f="decision"><option>needs_work</option><option>accepted</option><option>rejected</option></select></div>' +
      ["source_units","relation_type","variant_notes","editorial_handling"].map(f =>
        '<div class="field"><label>' + f.replace(/_/g," ") + '</label><select data-f="' + f + '"><option>uncertain</option><option>agree</option><option>revise</option></select></div>'
      ).join("") +
      '<div class="field full"><label>Notes</label><textarea data-f="notes" placeholder="Why do you accept/reject/revise this alignment?"></textarea></div>' +
      '<div class="actions"><button class="action" type="button" data-build="' + esc(a.alignment_id) + '">Prepare review JSON</button>' +
      '<button class="action secondary" type="button" data-copy="' + esc(a.alignment_id) + '">Copy JSON</button></div>' +
      '<div class="field full"><label>Generated review record</label><textarea class="json-output" data-json="' + esc(a.alignment_id) + '" spellcheck="false"></textarea></div>' +
    '</div></div>';
}}

function renderAlignment(a) {{
  const members = WITNESS_ORDER.map(w => a.members.find(m => m.witness_id === w)).filter(Boolean);
  const variants = (a.variants || []).map(v =>
    '<div class="variant"><strong>' + esc(v.type) + '</strong> · ' + esc(v.statement) + '</div>'
  ).join("");
  return '<section class="alignment" data-alignment="' + esc(a.alignment_id) + '">' +
    '<div class="card"><h2>' + esc(a.scope.replace(/_/g," ")) + '</h2>' +
      '<div class="meta-row"><span class="badge">' + esc(a.relation_type) + '</span><span class="badge">' + esc(a.status) + '</span><span class="badge">confidence ' + esc(a.review.confidence) + '</span></div>' +
      '<p>' + esc(a.review.notes || "") + '</p></div>' +
    '<div class="witness-grid">' + members.map(witnessCard).join("") + '</div>' +
    '<div class="card"><h3>Variant claims to review</h3><div class="variants">' + (variants || '<p class="provenance">No model variant claim for this alignment.</p>') + '</div></div>' +
    reviewForm(a) +
    '</section>';
}}

function buildReview(alignmentId) {{
  const a = DATA.alignments.find(row => row.alignment_id === alignmentId);
  const form = document.querySelector('[data-review-form="' + CSS.escape(alignmentId) + '"]');
  const value = name => form.querySelector('[data-f="' + name + '"]').value.trim();
  const reviewerName = value("name");
  if (!reviewerName) {{
    alert("Reviewer name is required. The UI will not invent a human identity.");
    return;
  }}
  const date = new Date().toISOString().slice(0,10);
  const review = {{
    review_id: "review:" + slug(reviewerName) + ":" + alignmentId + ":" + date,
    case_study_id: DATA.case_study_id,
    alignment_id: alignmentId,
    reviewer: {{
      reviewer_type: "human",
      name: reviewerName,
      affiliation: value("affiliation") || null,
      identifier: value("identifier") || null
    }},
    decision: value("decision"),
    assessments: {{
      source_units: value("source_units"),
      relation_type: value("relation_type"),
      variant_notes: value("variant_notes"),
      editorial_handling: value("editorial_handling")
    }},
    reviewed_on: date,
    evidence_snapshot: a.evidence_snapshot,
    notes: value("notes"),
    proposed_changes: null
  }};
  form.querySelector('[data-json="' + CSS.escape(alignmentId) + '"]').value = JSON.stringify(review,null,2);
}}

function selectAlignment(id) {{
  activeId = id;
  document.querySelectorAll(".alignment").forEach(el => el.classList.toggle("active", el.dataset.alignment === id));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.id === id));
  window.scrollTo({{top:0,behavior:"smooth"}});
}}

function renderNav(filter) {{
  const q = String(filter || "").toLowerCase();
  const nav = document.getElementById("nav");
  nav.innerHTML = DATA.alignments
    .filter(a => (a.scope + " " + a.alignment_id + " " + a.relation_type).toLowerCase().includes(q))
    .map((a,i) => '<button class="nav-item" data-id="' + esc(a.alignment_id) + '"><strong>' + (i+1) + '. ' + esc(a.scope.replace(/_/g," ")) + '</strong><small>' + esc(a.relation_type) + ' · ' + esc(a.review.confidence) + '</small></button>')
    .join("");
  nav.querySelectorAll(".nav-item").forEach(btn => btn.addEventListener("click", () => selectAlignment(btn.dataset.id)));
  if (activeId) {{
    const active = nav.querySelector('[data-id="' + CSS.escape(activeId) + '"]');
    if (active) active.classList.add("active");
  }}
}}

document.getElementById("content").innerHTML = DATA.alignments.map(renderAlignment).join("");
document.getElementById("reviewCount").textContent = DATA.review_count + " committed human review(s)";
renderNav("");
if (activeId) selectAlignment(activeId);
document.getElementById("filter").addEventListener("input", e => renderNav(e.target.value));
document.querySelectorAll("[data-build]").forEach(btn => btn.addEventListener("click", () => buildReview(btn.dataset.build)));
document.querySelectorAll("[data-copy]").forEach(btn => btn.addEventListener("click", async () => {{
  const out = document.querySelector('[data-json="' + CSS.escape(btn.dataset.copy) + '"]');
  if (!out.value.trim()) buildReview(btn.dataset.copy);
  if (out.value.trim()) {{
    try {{ await navigator.clipboard.writeText(out.value); btn.textContent = "Copied"; setTimeout(() => btn.textContent = "Copy JSON",1200); }}
    catch (_) {{ out.focus(); out.select(); }}
  }}
}}));
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    idx = build_index(args.pali_units, args.chinese_blocks, args.indic_units)
    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    payload = case_payload(case, reviews, idx)
    page = build_page(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    print(
        json.dumps(
            {
                "case_study": payload["case_study_id"],
                "alignments": len(payload["alignments"]),
                "existing_human_reviews": payload["review_count"],
                "output": str(args.output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
