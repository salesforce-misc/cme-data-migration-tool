
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import html
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dateutil import parser as date_parser

from src.cme_catalog_change_detection_tool.utils.config import AppConfig


class HtmlBuilder:

    def __init__(self, cfg: AppConfig, history_by_parent: Dict[str, List[Dict[str, Any]]]) -> None:
        self.cfg = cfg
        self.history_by_parent = history_by_parent
        self.rows_html: List[str] = []
        self.cutoff = datetime.now(timezone.utc) - timedelta(days=self.cfg.number_of_days)

    def traverse_nodes(self, nodes: Any, depth: int = 0) -> None:
        '''
        Traverse the nodes and add them to the report
        ''' 
        if len(nodes) == 0:
            return
        for entity, node_list in nodes.items():
            if node_list:
                self._add_section_header(entity + " (" + str(len(node_list)) + ")", depth)
                for node in node_list:
                    self._add_row(node["entity"], node["record"], depth+1, len(node.get("children", {})) > 0)
                    self.traverse_nodes(node.get("children", {}), depth + 2)

    def write_html(self):
        # Build HTML report
        title = f"EPC Changes in last {self.cfg.number_of_days} days"
        subtitle = f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)"

        # Copy html/css/js files to output directory
        output_path = self.cfg.output_path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            static_dir = Path(__file__).resolve().parents[1] / "static"
            for fname in ["hierarchy.js", "hierarchy.css"]:
                src = static_dir / fname
                dst = Path(output_path).parent / fname
                if src.exists():
                    content = src.read_text(encoding="utf-8")
                    dst.write_text(content, encoding="utf-8")
        except Exception:
            pass

        # Render report using Jinja2 template
        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tmpl = env.get_template("hierarchy_report.html.j2")
        html_doc = tmpl.render(title=title, subtitle=subtitle, rows_count=len(self.rows_html), rows_html="".join(self.rows_html))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        return output_path
        
    def _get_record_link(self, record: Dict[str, Any]) -> str:
        record_id = record.get("Id")
        href = f"{self.cfg.instance_url}/{record_id}" if self.cfg.instance_url else "#"
        return f'<a href="{html.escape(str((href)))}" target="_blank">{html.escape(str((record_id)))}</a>'
    
    def _highlight_classes(self, record: Dict[str, Any]) -> tuple[str, str]:
        def parse_dt(v: Any) -> datetime | None:
            if not v:
                return None
            try:
                dt = date_parser.parse(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                return None
        created = parse_dt(record.get("CreatedDate"))
        modified = parse_dt(record.get("LastModifiedDate"))
        created_cls = "highlight-cell" if (created and created >= self.cutoff) else ""
        modified_cls = "highlight-cell" if (modified and modified >= self.cutoff) else ""
        return created_cls, modified_cls

    def _add_row(self, entity_label: str, record: Dict[str, Any] | None, depth: int, has_children: bool = False) -> None:
        '''
        Add a row to the report
        '''
        created_cls, modified_cls = self._highlight_classes(record)
        name_value = record.get("Name")
        name_html = f'<div class="name">{html.escape(str(name_value))}</div>' if name_value else ''
        id_html = f'<div class="id id-link">{self._get_record_link(record)}</div>' if record.get("Id") else ''
        indent_px = max(0, depth) * 16
        toggle_html = (
            '<span class="material-icons tiny toggle-icon" onclick="toggleRow(this)" title="Collapse/Expand">expand_more</span>'
            if has_children else
            '<span class="material-icons tiny leaf-icon" title="Leaf">radio_button_unchecked</span>'
        )
        entity_cell = (
            f'<div style="margin-left:{indent_px}px; display:flex; align-items:flex-start; gap:6px">'
            f'{toggle_html}'
            f'<div>'
            f'<div style="font-weight:600">{html.escape(str(entity_label))}</div>'
            f'{name_html}{id_html}'
            f'</div>'
            f'</div>'
        )
        created_txt = html.escape(str(record.get("CreatedDate") or ""))
        modified_txt = html.escape(str(record.get("LastModifiedDate") or ""))
       
        changes_html = ''
        rid = record.get("Id") if record else None
        if rid and self.history_by_parent:
            changes = self.history_by_parent.get(rid, []) or []
            if changes:
                max_items = 50
                items: List[str] = []
                for idx, h in enumerate(changes):
                    if idx >= max_items:
                        remaining = len(changes) - max_items
                        items.append(
                            '<div class="change-more">'
                            f'<div class="grey-text">(+{remaining} more)</div>'
                            '</div>'
                        )
                        break
                    dt = html.escape(str(h.get('CreatedDate') or ''))
                    field = html.escape(str(h.get('Field') or ''))
                    has_old = (h.get('OldValue') is not None)
                    has_new = (h.get('NewValue') is not None)
                    oldv = html.escape(str(h.get('OldValue') if has_old else ''))
                    newv = html.escape(str(h.get('NewValue') if has_new else ''))
                    block_lines: List[str] = []
                    block_lines.append(f'<div>Date: <strong>{dt}</strong></div>')
                    block_lines.append(f'<div>Field: <strong>{field}</strong></div>')
                    if has_old:
                        block_lines.append(f'<div>Old: <strong>{oldv}</strong></div>')
                    if has_new:
                        block_lines.append(f'<div>New: <strong>{newv}</strong></div>')
                    items.append(
                        '<div class="change-block" style="margin-bottom:8px">' + ''.join(block_lines) + '</div>'
                    )
                changes_html = ''.join(items)

        self.rows_html.append(
            f'<tr data-depth="{depth}" class="{"parent" if has_children else ""}">'
            f'<td>{entity_cell}</td>'
            f'<td class="nowrap {created_cls}">{created_txt}</td>'
            f'<td class="nowrap {modified_cls}">{modified_txt}</td>'
            f'<td class="nowrap">{changes_html}</td>'
            '</tr>'
        )

    def _add_section_header(self, title: str, depth: int = 0) -> None:
        indent_px = max(0, depth) * 16
        self.rows_html.append(
            f'<tr data-depth="{depth}" class="section-header parent">'
            f'<td colspan="4">'
            f'<div style="margin-left:{indent_px}px; display:flex; align-items:flex-start; gap:6px">'
            f'<span class="material-icons tiny toggle-icon" onclick="toggleRow(this)" title="Collapse/Expand">expand_more</span>'
            f'<div style="font-weight:700">{html.escape(str(title))}</div>'
            f'</div>'
            f'</td>'
            '</tr>'
        )

    