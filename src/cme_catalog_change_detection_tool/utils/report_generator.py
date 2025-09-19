from __future__ import annotations

import html
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader, select_autoescape


def _escape(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))

def _dedupe_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return a new list with duplicate Ids removed
    """
    seen: set[str] = set()
    result: List[Dict[str, Any]] = []
    for rec in records or []:
        rid = (rec or {}).get("Id")
        if rid:
            if rid in seen:
                continue
            seen.add(rid)
        result.append(rec)
    return result

def _get_template_env() -> Environment:
    templates_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def generate_hierarchical_html_report(
    products: List[Dict[str, Any]],
    output_path: str,
    title: str,
    subtitle: str,
    instance_url: str | None,
    cutoff_iso: str,
    engine_results: Dict[str, List[Dict[str, Any]]] | None = None,
) -> str:
    """
    Generate a hierarchical HTML report
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cutoff = date_parser.parse(cutoff_iso)

    def highlight_classes(record: Dict[str, Any]) -> tuple[str, str]:
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
        created_cls = "highlight-cell" if (created and created >= cutoff) else ""
        modified_cls = "highlight-cell" if (modified and modified >= cutoff) else ""
        return created_cls, modified_cls

    rows_html: List[str] = []

    # Create ObjectClassId -> ObjectClass map, ObjectClassId -> ObjectFieldAttribute map
    id_object_class_map: Dict[str, Dict[str, Any]] = {r.get("Id"): r for r in (engine_results.get("ObjectClass", []) or [])}
    ocid_ofa_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in (engine_results.get("ObjectFieldAttribute", []) or []):
        ocid = r.get("vlocity_cmt__ObjectClassId__c")
        if ocid:
            ocid_ofa_map.setdefault(ocid, []).append(r)

    # Create ObjectClassId -> AttributeBinding map
    ocid_ab_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in (engine_results.get("AttributeBinding", []) or []):
        ocid = r.get("vlocity_cmt__ObjectClassId__c")
        if ocid:
            ocid_ab_map.setdefault(ocid, []).append(r)

    # Create AttributeId -> Attribute map, AttributeCategoryId -> AttributeCategory map, PicklistId -> Picklist map
    id_attribute_map: Dict[str, Dict[str, Any]] = {r.get("Id"): r for r in (engine_results.get("Attribute", []) or [])}
    id_attribute_category_map: Dict[str, Dict[str, Any]] = {r.get("Id"): r for r in (engine_results.get("AttributeCategory", []) or [])}
    id_picklist_map: Dict[str, Dict[str, Any]] = {r.get("Id"): r for r in (engine_results.get("Picklist", []) or [])}

    # RuleId -> RuleFilter records (for fallback when ra_bundle.rule_filters is empty)
    rule_filters_by_rule_id: Dict[str, List[Dict[str, Any]]] = {}
    for rf in (engine_results.get("RuleFilter", []) or []):
        rid = rf.get("vlocity_cmt__RuleId__c")
        if rid:
            rule_filters_by_rule_id.setdefault(rid, []).append(rf)

    # Build EntityFilter lookup maps for fallback rendering when bundles are missing
    entity_filter_by_id: Dict[str, Dict[str, Any]] = {r.get("Id"): r for r in (engine_results.get("EntityFilter", []) or [])}
    ef_conditions_by_ef: Dict[str, List[Dict[str, Any]]] = {}
    for r in (engine_results.get("EntityFilterCondition", []) or []):
        eid = r.get("vlocity_cmt__EntityFilterId__c")
        if eid:
            ef_conditions_by_ef.setdefault(eid, []).append(r)
    ef_members_by_ef: Dict[str, List[Dict[str, Any]]] = {}
    for r in (engine_results.get("EntityFilterMember", []) or []):
        eid = r.get("vlocity_cmt__EntityFilterId__c")
        if eid:
            ef_members_by_ef.setdefault(eid, []).append(r)
    ef_args_by_condition: Dict[str, List[Dict[str, Any]]] = {}
    for r in (engine_results.get("EntityFilterConditionArgument", []) or []):
        cid = r.get("vlocity_cmt__FilterConditionId__c")
        if cid:
            ef_args_by_condition.setdefault(cid, []).append(r)


    def rec_link(record: Dict[str, Any]) -> str:
        '''
        Generate a link to the record
        '''
        record_id = record.get("Id")
        href = f"{instance_url}/{record_id}" if instance_url else "#"
        return f'<a href="{_escape(href)}" target="_blank">{_escape(record_id)}</a>'

    def add_row(entity_label: str, record: Dict[str, Any] | None, depth: int, has_children: bool = False) -> None:
        '''
        Add a row to the report
        '''
        created_cls, modified_cls = highlight_classes(record)
        name_value = record.get("Name")
        name_html = f'<div class="name">{_escape(name_value)}</div>' if name_value else ''
        id_html = f'<div class="id id-link">{rec_link(record)}</div>' if record.get("Id") else ''
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
            f'<div style="font-weight:600">{_escape(entity_label)}</div>'
            f'{name_html}{id_html}'
            f'</div>'
            f'</div>'
        )
        created_txt = _escape(record.get("CreatedDate") or "")
        modified_txt = _escape(record.get("LastModifiedDate") or "")
        rows_html.append(
            f'<tr data-depth="{depth}" class="{"parent" if has_children else ""}">'
            f'<td>{entity_cell}</td>'
            f'<td class="{created_cls}">{created_txt}</td>'
            f'<td class="{modified_cls}">{modified_txt}</td>'
            '</tr>'
        )

    def add_section_header(title: str, depth: int = 0) -> None:
        indent_px = max(0, depth) * 16
        rows_html.append(
            f'<tr data-depth="{depth}" class="section-header parent">'
            f'<td colspan="3">'
            f'<div style="margin-left:{indent_px}px; display:flex; align-items:flex-start; gap:6px">'
            f'<span class="material-icons tiny toggle-icon" onclick="toggleRow(this)" title="Collapse/Expand">expand_more</span>'
            f'<div style="font-weight:700">{_escape(title)}</div>'
            f'</div>'
            f'</td>'
            '</tr>'
        )

    def traverse_rule_action(ra_bundle: Dict[str, Any], depth: int) -> None:

        # Generate RuleAction/Rule/RuleVariable rows
        add_row("", ra_bundle.get("record"), depth, has_children=bool(ra_bundle.get("rule") or ra_bundle.get("rule_variables") or ra_bundle.get("rule_filters") or ra_bundle.get("action_entity_filter")))
        rule = ra_bundle.get("rule")
        if rule:
            add_section_header("Rule", depth + 1)
            add_row("", rule, depth + 2)
            
        rvars = ra_bundle.get("rule_variables", []) or []
        if rvars:
            add_section_header("RuleVariable", depth + 1)
            for v in rvars:
                add_row("", v, depth + 2)
        
        # Generate RuleFilter rows
        rfilters = ra_bundle.get("rule_filters", []) or []
        # Fallback: if bundle lacks rule_filters but Rule exists, fetch from engine_results
        if (not rfilters) and rule and rule.get("Id"):
            for rf in rule_filters_by_rule_id.get(rule.get("Id"), []) or []:
                rfilters.append({"record": rf})
        if rfilters:
            add_section_header("RuleFilter", depth + 1)
            for rf in rfilters:
                rf_rec = rf.get("record") or {}
                rf_ef_id = rf_rec.get("vlocity_cmt__EntityFilterId__c")
                add_row("", rf_rec, depth + 2, has_children=bool(rf.get("entity_filter") or rf_ef_id))
                ef = rf.get("entity_filter")
                # Fallback: reconstruct EF bundle from engine_results if not attached by builder
                if (not ef) and rf_ef_id:
                    ef_rec = entity_filter_by_id.get(rf_ef_id)
                    if ef_rec:
                        ef = {
                            "record": ef_rec,
                            "conditions": ef_conditions_by_ef.get(rf_ef_id, []),
                            "members": ef_members_by_ef.get(rf_ef_id, []),
                            "arguments_by_condition": {c.get("Id"): ef_args_by_condition.get(c.get("Id"), []) for c in ef_conditions_by_ef.get(rf_ef_id, [])},
                        }
                if ef and ef.get("record"):
                    # Generate EntityFilter row
                    add_section_header("EntityFilter", depth + 2)
                    add_row("", ef.get("record"), depth + 3)

                    # Generate EntityFilterCondition rows
                    conds = ef.get("conditions", []) or []
                    if conds:
                        add_section_header("EntityFilterCondition", depth + 3)
                        for c in conds:
                            add_row("", c, depth + 4)
                    
                    # Generate EntityFilterMember rows
                    members = ef.get("members", []) or []
                    if members:
                        add_section_header("EntityFilterMember", depth + 3)
                        for m in members:
                            add_row("", m, depth + 4)

                    # Generate EntityFilterConditionArgument rows
                    args_by_cond = ef.get("arguments_by_condition", {}) if ef else {}
                    if args_by_cond:
                        add_section_header("EntityFilterConditionArgument", depth + 3)
                        for cond in conds:
                            for a in (args_by_cond.get(cond.get("Id"), []) or []):
                                add_row("", a, depth + 4)

        # Generate EntityFilterCondition/EntityFilterMember/EntityFilterConditionArgument rows
        aef = ra_bundle.get("action_entity_filter")
        # Fallback: reconstruct from RuleAction.EntityFilterId if missing
        if not aef:
            ra_rec = ra_bundle.get("record") or {}
            ra_ef_id = ra_rec.get("vlocity_cmt__EntityFilterId__c")
            if ra_ef_id:
                ef_rec = entity_filter_by_id.get(ra_ef_id)
                if ef_rec:
                    aef = {
                        "record": ef_rec,
                        "conditions": ef_conditions_by_ef.get(ra_ef_id, []),
                        "members": ef_members_by_ef.get(ra_ef_id, []),
                        "arguments_by_condition": {c.get("Id"): ef_args_by_condition.get(c.get("Id"), []) for c in ef_conditions_by_ef.get(ra_ef_id, [])},
                    }
        if aef and aef.get("record"):
            add_section_header("EntityFilter", depth + 1)
            add_row("", aef.get("record"), depth + 2)
            acond = aef.get("conditions", []) or []
            if acond:
                add_section_header("EntityFilterCondition", depth + 2)
                for c in acond:
                    add_row("", c, depth + 3)
            amembers = aef.get("members", []) or []
            if amembers:
                add_section_header("EntityFilterMember", depth + 2)
                for m in amembers:
                    add_row("", m, depth + 3)
            a_args_by_cond = aef.get("arguments_by_condition", {}) if aef else {}
            if a_args_by_cond and acond:
                add_section_header("EntityFilterConditionArgument", depth + 2)
                for cond in acond:
                    for a in (a_args_by_cond.get(cond.get("Id"), []) or []):
                        add_row("", a, depth + 3)

    def traverse_layout(layout_bundle: Dict[str, Any], depth: int) -> None:

        # Generate Layout, then group Facet/Section/UI entities
        add_row("", layout_bundle.get("record"), depth, has_children=False)
        facets = layout_bundle.get("facets", []) or []
        facet_records: List[Dict[str, Any]] = []
        ui_facet_records: List[Dict[str, Any]] = []
        section_records: List[Dict[str, Any]] = []
        ui_section_records: List[Dict[str, Any]] = []
        element_records: List[Dict[str, Any]] = []

        for facet in facets:
            rec = facet.get("record")
            if rec:
                facet_records.append(rec)
            ui_f = facet.get("ui_facet")
            if ui_f:
                ui_facet_records.append(ui_f)
            for section in (facet.get("sections", []) or []):
                srec = section.get("record")
                if srec:
                    section_records.append(srec)
                ui_s = section.get("ui_section")
                if ui_s:
                    ui_section_records.append(ui_s)
                for elem in (section.get("elements", []) or []):
                    element_records.append(elem)

        # De-dupe Facet/Section/UI entities
        facet_records = _dedupe_by_id(facet_records)
        if facet_records:
            add_section_header("ObjectFacet", depth + 1)
            for r in facet_records:
                add_row("", r, depth + 2)

        ui_facet_records = _dedupe_by_id(ui_facet_records)
        if ui_facet_records:
            add_section_header("UIFacet", depth + 1)
            for r in ui_facet_records:
                add_row("", r, depth + 2)

        section_records = _dedupe_by_id(section_records)
        if section_records:
            add_section_header("ObjectSection", depth + 1)
            for r in section_records:
                add_row("", r, depth + 2)

        ui_section_records = _dedupe_by_id(ui_section_records)
        if ui_section_records:
            add_section_header("UISection", depth + 1)
            for r in ui_section_records:
                add_row("", r, depth + 2)

        element_records = _dedupe_by_id(element_records)
        if element_records:
            add_section_header("ObjectElement", depth + 1)
            for r in element_records:
                add_row("", r, depth + 2)

    def traverse_product(node: Dict[str, Any], depth: int) -> None:
        children = node.get("children", {})
        has_kids = bool(children.get("attributes") or children.get("overrides") or children.get("relationships") or children.get("procedures") or children.get("pricing") or children.get("layouts") or children.get("products") or children.get("product_spec"))
        add_row("Product2", node.get("record"), depth, has_children=has_kids)

        # Generate ObjectClass and related ObjectFieldAttribute for this product's ObjectTypeId
        prod_rec = node.get("record") or {}
        obj_class_id = prod_rec.get("vlocity_cmt__ObjectTypeId__c")
        if obj_class_id and (obj_class_id in id_object_class_map or obj_class_id in ocid_ofa_map or obj_class_id in ocid_ab_map):
            add_section_header("ObjectClass", depth + 1)
            oc_rec = id_object_class_map.get(obj_class_id)
            if oc_rec:
                add_row("", oc_rec, depth + 2)

            # Generate ObjectFieldAttribute and its Attribute/Category children
            ofas = _dedupe_by_id(ocid_ofa_map.get(obj_class_id, []) or [])
            if ofas:
                add_section_header("ObjectFieldAttribute", depth + 2)
                for ofa in ofas:
                    add_row("", ofa, depth + 3)
                    
                ofa_attr_ids = [o.get("vlocity_cmt__AttributeId__c") for o in ofas]
                ofa_attr_ids = [i for i in ofa_attr_ids if i]
                ofa_cat_ids = [o.get("vlocity_cmt__AttributeCategoryId__c") for o in ofas]
                ofa_cat_ids = [i for i in ofa_cat_ids if i]
                ofa_attrs_details = _dedupe_by_id([id_attribute_map[i] for i in ofa_attr_ids if i in id_attribute_map])
                ofa_cats_details = _dedupe_by_id([id_attribute_category_map[i] for i in ofa_cat_ids if i in id_attribute_category_map])
                if ofa_attrs_details:
                    add_section_header("Attribute", depth + 3)
                    for ad in ofa_attrs_details:
                        add_row("", ad, depth + 4)
                    # Group Picklists for these attributes
                    pl_ids = [(ad or {}).get("vlocity_cmt__PicklistId__c") for ad in ofa_attrs_details]
                    pl_ids = [i for i in pl_ids if i]
                    pl_details = _dedupe_by_id([id_picklist_map[i] for i in pl_ids if i in id_picklist_map])
                    if pl_details:
                        add_section_header("Picklist", depth + 3)
                        for pl in pl_details:
                            add_row("", pl, depth + 4)
                if ofa_cats_details:
                    add_section_header("AttributeCategory", depth + 3)
                    for cd in ofa_cats_details:
                        add_row("", cd, depth + 4)

            # Generate AttributeBinding and its Attribute/Category children
            abs_for_oc = _dedupe_by_id(ocid_ab_map.get(obj_class_id, []) or [])
            if abs_for_oc:
                add_section_header("AttributeBinding", depth + 2)
                for ab in abs_for_oc:
                    add_row("", ab, depth + 3)
                ab_attr_ids = [b.get("vlocity_cmt__AttributeId__c") for b in abs_for_oc]
                ab_attr_ids = [i for i in ab_attr_ids if i]
                ab_cat_ids = [b.get("vlocity_cmt__AttributeCategoryId__c") for b in abs_for_oc]
                ab_cat_ids = [i for i in ab_cat_ids if i]
                ab_attrs_details = _dedupe_by_id([id_attribute_map[i] for i in ab_attr_ids if i in id_attribute_map])
                ab_cats_details = _dedupe_by_id([id_attribute_category_map[i] for i in ab_cat_ids if i in id_attribute_category_map])
                if ab_attrs_details:
                    add_section_header("Attribute", depth + 3)
                    for ad in ab_attrs_details:
                        add_row("", ad, depth + 4)
                    # Group Picklists for these attributes
                    pl_ids = [(ad or {}).get("vlocity_cmt__PicklistId__c") for ad in ab_attrs_details]
                    pl_ids = [i for i in pl_ids if i]
                    pl_details = _dedupe_by_id([id_picklist_map[i] for i in pl_ids if i in id_picklist_map])
                    if pl_details:
                        add_section_header("Picklist", depth + 3)
                        for pl in pl_details:
                            add_row("", pl, depth + 4)
                if ab_cats_details:
                    add_section_header("AttributeCategory", depth + 3)
                    for cd in ab_cats_details:
                        add_row("", cd, depth + 4)

            # Generate ObjectLayout/ObjectFacet/UISection/ObjectSection/ObjectElement under ObjectClass
            layouts_bundles = children.get("layouts", []) or []
            if layouts_bundles:
                layout_records: List[Dict[str, Any]] = []
                facet_records: List[Dict[str, Any]] = []
                ui_facet_records: List[Dict[str, Any]] = []
                section_records: List[Dict[str, Any]] = []
                ui_section_records: List[Dict[str, Any]] = []
                element_records: List[Dict[str, Any]] = []

                for lb in layouts_bundles:
                    lrec = lb.get("record")
                    if lrec:
                        layout_records.append(lrec)
                    for facet in (lb.get("facets", []) or []):
                        frec = facet.get("record")
                        if frec:
                            facet_records.append(frec)
                        ufr = facet.get("ui_facet")
                        if ufr:
                            ui_facet_records.append(ufr)
                        for section in (facet.get("sections", []) or []):
                            srec = section.get("record")
                            if srec:
                                section_records.append(srec)
                            usr = section.get("ui_section")
                            if usr:
                                ui_section_records.append(usr)
                            for elem in (section.get("elements", []) or []):
                                element_records.append(elem)

                layout_records = _dedupe_by_id(layout_records)
                if layout_records:
                    add_section_header("ObjectLayout", depth + 2)
                    for r in layout_records:
                        add_row("", r, depth + 3)

                facet_records = _dedupe_by_id(facet_records)
                if facet_records:
                    add_section_header("ObjectFacet", depth + 2)
                    for r in facet_records:
                        add_row("", r, depth + 3)

                ui_facet_records = _dedupe_by_id(ui_facet_records)
                if ui_facet_records:
                    add_section_header("UIFacet", depth + 2)
                    for r in ui_facet_records:
                        add_row("", r, depth + 3)

                section_records = _dedupe_by_id(section_records)
                if section_records:
                    add_section_header("ObjectSection", depth + 2)
                    for r in section_records:
                        add_row("", r, depth + 3)

                ui_section_records = _dedupe_by_id(ui_section_records)
                if ui_section_records:
                    add_section_header("UISection", depth + 2)
                    for r in ui_section_records:
                        add_row("", r, depth + 3)

                element_records = _dedupe_by_id(element_records)
                if element_records:
                    add_section_header("ObjectElement", depth + 2)
                    for r in element_records:
                        add_row("", r, depth + 3)

        # De-dupe AttributeAssignments
        attrs_bundles = children.get("attributes", []) or []
        seen_attr_assign_ids: set[str] = set()
        attrs: List[Dict[str, Any]] = []
        for bundle in attrs_bundles:
            rec = (bundle or {}).get("record") or {}
            rid = rec.get("Id")
            if rid:
                if rid in seen_attr_assign_ids:
                    continue
                seen_attr_assign_ids.add(rid)
            attrs.append(bundle)
        if attrs:
            add_section_header("AttributeAssignment", depth + 1)
            for a in attrs:
                add_row("", a.get("record"), depth + 2)

            # Group Attributes and Categories referenced by AttributeAssignments
            attr_ids = [a.get("record", {}).get("vlocity_cmt__AttributeId__c") for a in attrs]
            attr_ids = [i for i in attr_ids if i]
            cat_ids = [a.get("record", {}).get("vlocity_cmt__AttributeCategoryId__c") for a in attrs]
            cat_ids = [i for i in cat_ids if i]
            attrs_details = [id_attribute_map[i] for i in attr_ids if i in id_attribute_map]
            cats_details = [id_attribute_category_map[i] for i in cat_ids if i in id_attribute_category_map]
            
            # De-dupe Attribute and AttributeCategory
            attrs_details = _dedupe_by_id(attrs_details)
            cats_details = _dedupe_by_id(cats_details)
            if attrs_details:
                add_section_header("Attribute", depth + 2)
                for ad in attrs_details:
                    add_row("", ad, depth + 3)
            if cats_details:
                add_section_header("AttributeCategory", depth + 2)
                for cd in cats_details:
                    add_row("", cd, depth + 3)

        # Generate OverrideDefinition
        ovs = children.get("overrides", []) or []
        if ovs:
            add_section_header("OverrideDefinition", depth + 1)
            for o in ovs:
                add_row("", o.get("record"), depth + 2)

        # Generate Relationships and RuleActions
        rels = children.get("relationships", []) or []
        if rels:
            add_section_header("ProductRelationship", depth + 1)
            for rel in rels:
                add_row("", rel.get("record"), depth + 2, has_children=bool(rel.get("rule_actions")))
                ras = rel.get("rule_actions", []) or []
                if ras:
                    add_section_header("RuleAction", depth + 3)
                    for ra in ras:
                        traverse_rule_action(ra, depth + 4)

        # Generate ProductConfigurationProcedure and RuleActions
        procs = children.get("procedures", []) or []
        if procs:
            add_section_header("ProductConfigurationProcedure", depth + 1)
            for p in procs:
                add_row("", p.get("record"), depth + 2, has_children=bool(p.get("rule_actions")))
                pras = p.get("rule_actions", []) or []
                if pras:
                    add_section_header("RuleAction", depth + 3)
                    for ra in pras:
                        traverse_rule_action(ra, depth + 4)

        # Generate PriceListEntry and PricingElement/PricingVariable/PricingVariableBinding
        pricing = children.get("pricing", []) or []
        if pricing:
            add_section_header("PriceListEntry", depth + 1)
            pv_records: List[Dict[str, Any]] = []
            pvb_records: List[Dict[str, Any]] = []
            for price in pricing:
                has_price_children = bool(price.get("pricing_element"))
                add_row("", price.get("record"), depth + 2, has_children=has_price_children)
                if price.get("pricing_element"):
                    add_section_header("PricingElement", depth + 3)
                    add_row("", price.get("pricing_element"), depth + 4)
                pv = price.get("pricing_variable")
                if pv:
                    pv_records.append(pv)
                pvb_records.extend(price.get("bindings", []) or [])

            # Grouped PricingVariable under PriceListEntry (no hierarchy)
            pv_records = _dedupe_by_id(pv_records)
            if pv_records:
                add_section_header("PricingVariable", depth + 2)
                for pv in pv_records:
                    add_row("", pv, depth + 3)

            # Grouped PricingVariableBinding under PriceListEntry (no hierarchy)
            pvb_records = _dedupe_by_id(pvb_records)
            if pvb_records:
                add_section_header("PricingVariableBinding", depth + 2)
                for b in pvb_records:
                    add_row("", b, depth + 3)
                    
        # Product Spec (if present)
        product_spec = children.get("product_spec")
        if product_spec:
            add_section_header("ProductSpec", depth + 1)
            traverse_product(product_spec, depth + 2)

        # Child products last (to keep immediate product context above)
        child_products = children.get("products", []) or []
        if child_products:
            add_section_header("ProductChildItems", depth + 1)
            for child in child_products:
                traverse_product(child, depth + 2)

    # Generate Product2 from top level
    for p in products:
        traverse_product(p, 0)

    # Render extra hierarchies if provided (Calculation Matrix/Procedure and CPQ)
    engine_results = engine_results or {}

    # Build Calculation Matrix tree
    calculation_matrix_list = engine_results.get("CalculationMatrix", [])
    calculation_matrix_version_list = engine_results.get("CalculationMatrixVersion", [])
    calculation_matrix_row_list = engine_results.get("CalculationMatrixRow", [])
    if calculation_matrix_list:
        add_section_header("CalculationMatrix", 0)
        versions_by_matrix: Dict[str, List[Dict[str, Any]]] = {}
        for v in calculation_matrix_version_list:
            mid = v.get("vlocity_cmt__CalculationMatrixId__c")
            if mid:
                versions_by_matrix.setdefault(mid, []).append(v)
        rows_by_version: Dict[str, List[Dict[str, Any]]] = {}
        for r in calculation_matrix_row_list:
            vid = r.get("vlocity_cmt__CalculationMatrixVersionId__c")
            if vid:
                rows_by_version.setdefault(vid, []).append(r)
        for m in calculation_matrix_list:
            m_id = m.get("Id")
            m_versions = versions_by_matrix.get(m_id, [])
            add_row("", m, 1, has_children=bool(m_versions))
            for v in m_versions:
                v_rows = rows_by_version.get(v.get("Id"), [])
                add_row("CalculationMatrixVersion", v, 2, has_children=bool(v_rows))
                for r in v_rows:
                    add_row("CalculationMatrixRow", r, 3)

    # Build Calculation Procedure tree
    calculation_procedure_list = engine_results.get("CalculationProcedure", [])
    calculation_procedure_version_list = engine_results.get("CalculationProcedureVersion", [])
    calculation_procedure_step_list = engine_results.get("CalculationProcedureStep", [])
    if calculation_procedure_list:
        add_section_header("CalculationProcedure", 0)
        versions_by_proc: Dict[str, List[Dict[str, Any]]] = {}
        for v in calculation_procedure_version_list:
            pid = v.get("vlocity_cmt__CalculationProcedureId__c")
            if pid:
                versions_by_proc.setdefault(pid, []).append(v)
        steps_by_version: Dict[str, List[Dict[str, Any]]] = {}
        for s in calculation_procedure_step_list:
            vid = s.get("vlocity_cmt__CalculationProcedureVersionId__c")
            if vid:
                steps_by_version.setdefault(vid, []).append(s)
        for p in calculation_procedure_list:
            p_id = p.get("Id")
            p_versions = versions_by_proc.get(p_id, [])
            add_row("", p, 1, has_children=bool(p_versions))
            for v in p_versions:
                v_steps = steps_by_version.get(v.get("Id"), [])
                add_row("CalculationProcedureVersion", v, 2, has_children=bool(v_steps))
                for s in v_steps:
                    add_row("CalculationProcedureStep", s, 3)

    # Build CPQ Configuration Setup (flat)
    cpq_list = engine_results.get("CpqConfigurationSetup", [])
    if cpq_list:
        add_section_header("CpqConfigurationSetup", 0)
        for cs in cpq_list or []:
            add_row("", cs, 1)

    # Note: EntityFilters are rendered only when attached to RuleFilter/RuleAction.

    env = _get_template_env()
    tmpl = env.get_template("hierarchy_report.html.j2")
    # Copy html/css/js files to output directory
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
    html_doc = tmpl.render(title=title, subtitle=subtitle, rows_count=len(rows_html), rows_html="".join(rows_html))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return output_path

