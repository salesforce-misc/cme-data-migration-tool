from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


def build_product_hierarchy(engine: Any, product_id: str) -> List[Dict[str, Any]]:
    """
    Using the SOQL Engine results, build a nested hierarchy of entities from the Product2 entity
    """
    results = engine.results
    all_products_map = {r.get("Id"): r for r in results.get("Product2")}

    # Add all AttributeAssignment records under respective Product2
    aa_per_product: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("AttributeAssignment"):
        aa_product_id = r.get("vlocity_cmt__ObjectId__c")
        if aa_product_id:
            aa_per_product.setdefault(aa_product_id, []).append(r)

    # Add all OverrideDefinition records under respective Product2
    overrides_per_product: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("OverrideDefinition"):
        override_product_id = r.get("vlocity_cmt__ProductId__c")
        if override_product_id:
            overrides_per_product.setdefault(override_product_id, []).append(r)

    # Create Parent -> Child product map from PCIs
    parent_child_product_map: Dict[str, List[str]] = {}
    child_ids_set: Set[str] = set()
    for r in results.get("ProductChildItem"):
        parent_id = r.get("vlocity_cmt__ParentProductId__c")
        child_id = r.get("vlocity_cmt__ChildProductId__c")
        if parent_id and child_id:
            lst = parent_child_product_map.setdefault(parent_id, [])
            if child_id not in lst:
                lst.append(child_id)
            child_ids_set.add(child_id)

    # Create Product Id -> Name map from Product Specification & PCI Parent/Child records
    product_spec_id_name_map: Dict[str, str] = {}
    for r in results.get("Product2"):
        product_spec_id = r.get("vlocity_cmt__ProductSpecId__c")
        product_spec_name = r.get("vlocity_cmt__ProductSpecId__r.Name")
        if product_spec_id and product_spec_name and product_spec_id not in product_spec_id_name_map:
            product_spec_id_name_map[product_spec_id] = product_spec_name
            
    for r in results.get("ProductChildItem"):
        # For PCI Parent
        parent_product_id = r.get("vlocity_cmt__ParentProductId__c")
        parent_product_name = r.get("vlocity_cmt__ParentProductId__r.Name")
        if parent_product_id and parent_product_name and parent_product_id not in product_spec_id_name_map:
            product_spec_id_name_map[parent_product_id] = parent_product_name
        # For PCI Child
        child_product_id = r.get("vlocity_cmt__ChildProductId__c")
        child_product_name = r.get("vlocity_cmt__ChildProductId__r.Name")
        if child_product_id and child_product_name and child_product_id not in product_spec_id_name_map:
            product_spec_id_name_map[child_product_id] = child_product_name


    # Capture details of all Products (in the hierarchy)
    all_products_ids: Set[str] = set(all_products_map.keys())
    all_products_ids.update(child_ids_set)
    all_products_ids.update(parent_child_product_map.keys())
    for r in results.get("Product2"):
        sid = r.get("vlocity_cmt__ProductSpecId__c")
        if sid:
            all_products_ids.add(sid)
    # Missing Product2 Names
    missing_name_ids = [product_id for product_id in all_products_ids if not all_products_map.get(product_id) or not all_products_map.get(product_id, {}).get("Name")]
    if missing_name_ids:
        for missing_name_id_chunk in engine._chunked_set(missing_name_ids, 200):
            ids_csv = ",".join([f"'{i}'" for i in missing_name_id_chunk])
            soql = f"SELECT Id, Name, CreatedDate, LastModifiedDate FROM Product2 WHERE Id IN ({ids_csv})"
            rows = engine.sf_client.query(soql)
            for r in rows:
                fetched_product_id = r.get("Id")
                all_products_map[fetched_product_id] = r

    # Create Product -> ProductRelationship map
    product_relationships_per_product: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ProductRelationship"):
        src = r.get("vlocity_cmt__Product2Id__c")
        if src:
            product_relationships_per_product.setdefault(src, []).append(r)

    # Create Product -> ProductConfigurationProcedure map
    pcp_per_product: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ProductConfigurationProcedure"):
        pcp_product_id = r.get("vlocity_cmt__ProductId__c")
        if pcp_product_id:
            pcp_per_product.setdefault(pcp_product_id, []).append(r)

    # Create RuleId -> RuleVariable map
    id_rule_map = {r.get("Id"): r for r in results.get("Rule")}
    rule_variables_per_rule: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("RuleVariable"):
        rid = r.get("vlocity_cmt__RuleId__c")
        if rid:
            rule_variables_per_rule.setdefault(rid, []).append(r)

    # Create RuleId -> RuleFilter map
    rule_filters_per_rule: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("RuleFilter"):
        rid = r.get("vlocity_cmt__RuleId__c")
        if rid:
            rule_filters_per_rule.setdefault(rid, []).append(r)

    # Create EntityFilterId -> EntityFilter map
    entity_filter_per_id = {r.get("Id"): r for r in results.get("EntityFilter")}
    ef_conditions_per_ef: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("EntityFilterCondition"):
        eid = r.get("vlocity_cmt__EntityFilterId__c")
        if eid:
            ef_conditions_per_ef.setdefault(eid, []).append(r)

    # Create EntityFilterId -> EntityFilterMember map
    ef_members_per_ef: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("EntityFilterMember"):
        eid = r.get("vlocity_cmt__EntityFilterId__c")
        if eid:
            ef_members_per_ef.setdefault(eid, []).append(r)

    # Create FilterConditionId -> EntityFilterConditionArgument map
    ef_args_per_condition: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("EntityFilterConditionArgument"):
        cid = r.get("vlocity_cmt__FilterConditionId__c")
        if cid:
            ef_args_per_condition.setdefault(cid, []).append(r)

    # Create ProductRelationshipId -> RuleAction map, ProductConfigurationProcedureId -> RuleAction map
    ra_per_rel: Dict[str, List[Dict[str, Any]]] = {}
    ra_per_pcp: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("RuleAction"):
        rel_id = r.get("vlocity_cmt__ProductRelationshipId__c")
        pcp_id = r.get("vlocity_cmt__ProductConfigurationProcedureId__c")
        if rel_id:
            ra_per_rel.setdefault(rel_id, []).append(r)
        if pcp_id:
            ra_per_pcp.setdefault(pcp_id, []).append(r)

    # Create AttributeId -> Attribute map, AttributeCategoryId -> AttributeCategory map
    attribute_per_id = {r.get("Id"): r for r in results.get("Attribute")}
    attr_cat_per_id = {r.get("Id"): r for r in results.get("AttributeCategory")}

    # Create ProductId -> PriceListEntry map
    ple_per_product: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("PriceListEntry"):
        ple_product_id = r.get("vlocity_cmt__ProductId__c")
        if ple_product_id:
            ple_per_product.setdefault(ple_product_id, []).append(r)

    # Create PricingElementId -> PricingElement map, PricingVariableId -> PricingVariable map
    pricing_element_per_id = {r.get("Id"): r for r in results.get("PricingElement")}
    pricing_variable_per_id = {r.get("Id"): r for r in results.get("PricingVariable")}
    bindings_per_pricing_var: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("PricingVariableBinding"):
        vid = r.get("vlocity_cmt__PricingVariableId__c")
        if vid:
            bindings_per_pricing_var.setdefault(vid, []).append(r)

    # Create ObjectClassId -> ObjectLayout map, ObjectLayoutId -> ObjectFacet map, ObjectFacetId -> ObjectSection map
    layouts_per_object_class: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ObjectLayout"):
        ocid = r.get("vlocity_cmt__ObjectClassId__c")
        if ocid:
            layouts_per_object_class.setdefault(ocid, []).append(r)
    facets_per_layout: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ObjectFacet"):
        lid = r.get("vlocity_cmt__ObjectLayoutId__c")
        if lid:
            facets_per_layout.setdefault(lid, []).append(r)
    sections_per_facet: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ObjectSection"):
        fid = r.get("vlocity_cmt__ObjectFacetId__c")
        if fid:
            sections_per_facet.setdefault(fid, []).append(r)

    # Create ObjectSectionId -> ObjectElement map
    elements_per_section: Dict[str, List[Dict[str, Any]]] = {}
    for r in results.get("ObjectElement"):
        sid = r.get("vlocity_cmt__ObjectSectionId__c")
        if sid:
            elements_per_section.setdefault(sid, []).append(r)

    # Create UIFacetId -> UIFacet map, UISectionId -> UISection map
    ui_facet_per_id = {r.get("Id"): r for r in results.get("UIFacet")}
    ui_section_per_id = {r.get("Id"): r for r in results.get("UISection")}

    # Track visited products while constructing the hierarchy
    visited: Set[str] = set()

    # Build rule bundle
    def build_rule_bundle(rule_id: Optional[str], explicit_ef_id: Optional[str]) -> Dict[str, Any]:
        '''
        Build a bundle for a RuleAction record
        '''
        bundle: Dict[str, Any] = {}
        if rule_id and rule_id in id_rule_map:
            r = id_rule_map[rule_id]
            bundle["rule"] = r
            bundle["rule_variables"] = rule_variables_per_rule.get(rule_id, [])
            filters = []
            for rf in rule_filters_per_rule.get(rule_id, []):
                ef_id = rf.get("vlocity_cmt__EntityFilterId__c")
                ef = entity_filter_per_id.get(ef_id) if ef_id else None
                filters.append({
                    "record": rf,
                    "entity_filter": {
                        "record": ef,
                        "conditions": ef_conditions_per_ef.get(ef_id, []) if ef_id else [],
                        "members": ef_members_per_ef.get(ef_id, []) if ef_id else [],
                        "arguments_by_condition": {c.get("Id"): ef_args_per_condition.get(c.get("Id"), []) for c in ef_conditions_per_ef.get(ef_id, [])} if ef_id else {},
                    } if ef else None,
                })
            bundle["rule_filters"] = filters
        if explicit_ef_id:
            ef = entity_filter_per_id.get(explicit_ef_id)
            if ef:
                bundle["action_entity_filter"] = {
                    "record": ef,
                    "conditions": ef_conditions_per_ef.get(explicit_ef_id, []),
                    "members": ef_members_per_ef.get(explicit_ef_id, []),
                    "arguments_by_condition": {c.get("Id"): ef_args_per_condition.get(c.get("Id"), []) for c in ef_conditions_per_ef.get(explicit_ef_id, [])},
                }
        return bundle

    # Build layout bundle
    def build_layout_bundle(object_class_id: Optional[str]) -> List[Dict[str, Any]]:
        '''
        Build a bundle for a ObjectLayout record
        '''
        if not object_class_id:
            return []
        results_local: List[Dict[str, Any]] = []
        for layout in layouts_per_object_class.get(object_class_id, []):
            layout_id = layout.get("Id")
            facets = []
            for facet in facets_per_layout.get(layout_id, []):
                ui_facet = ui_facet_per_id.get(facet.get("vlocity_cmt__FacetId__c"))
                sections = []
                for section in sections_per_facet.get(facet.get("Id"), []):
                    ui_sec = ui_section_per_id.get(section.get("vlocity_cmt__SectionId__c"))
                    elements = elements_per_section.get(section.get("Id"), [])
                    sections.append({
                        "entity": "ObjectSection",
                        "record": section,
                        "ui_section": ui_sec,
                        "elements": elements,
                    })
                facets.append({
                    "entity": "ObjectFacet",
                    "record": facet,
                    "ui_facet": ui_facet,
                    "sections": sections,
                })
            results_local.append({
                "entity": "ObjectLayout",
                "record": layout,
                "facets": facets,
            })
        return results_local

    # Build product node
    def build_product_node(product_id: str) -> Dict[str, Any]:
        '''
        Build a node for a Product2 record
        '''
        if product_id in visited:
            rec = all_products_map.get(product_id, {"Id": product_id})
            return {"entity": "Product2", "record": rec, "children": {}}
        visited.add(product_id)
        prod = all_products_map.get(product_id, {"Id": product_id})
        children: Dict[str, Any] = {}

        # Generate ProductSpec or PCI Hierarchy
        spec_id = prod.get("vlocity_cmt__ProductSpecId__c")
        if spec_id:
            # Build full node for the spec so its own details are visible
            spec_node = build_product_node(spec_id)
            children["product_spec"] = spec_node
        else:
            # Nested products directly under this product (dedupe children)
            prod_children = [build_product_node(cid) for cid in sorted(set(parent_child_product_map.get(product_id, [])))]
            if prod_children:
                children["products"] = prod_children

        # Add Attributes to bundle
        attrs = []
        for aa in aa_per_product.get(product_id, []):
            attrs.append({
                "entity": "AttributeAssignment",
                "record": aa,
                "attribute": attribute_per_id.get(aa.get("vlocity_cmt__AttributeId__c")),
                "category": attr_cat_per_id.get(aa.get("vlocity_cmt__AttributeCategoryId__c")),
            })
        if attrs:
            children["attributes"] = attrs

        # Add Overrides to bundle
        if overrides_per_product.get(product_id):
            children["overrides"] = [{"entity": "OverrideDefinition", "record": r} for r in overrides_per_product.get(product_id, [])]

        # Add Relationships with rule actions to bundle
        rels = []
        for rel in product_relationships_per_product.get(product_id, []):
            rel_id = rel.get("Id")
            actions = []
            for ra in ra_per_rel.get(rel_id, []):
                bundle = build_rule_bundle(ra.get("vlocity_cmt__RuleId__c"), ra.get("vlocity_cmt__EntityFilterId__c"))
                actions.append({"entity": "RuleAction", "record": ra, **bundle})
            rels.append({"entity": "ProductRelationship", "record": rel, "rule_actions": actions})
        if rels:
            children["relationships"] = rels

        # Add PCPs with rule actions to bundle
        procs = []
        for pcp in pcp_per_product.get(product_id, []):
            actions = []
            for ra in ra_per_pcp.get(pcp.get("Id"), []):
                bundle = build_rule_bundle(ra.get("vlocity_cmt__RuleId__c"), ra.get("vlocity_cmt__EntityFilterId__c"))
                actions.append({"entity": "RuleAction", "record": ra, **bundle})
            procs.append({"entity": "ProductConfigurationProcedure", "record": pcp, "rule_actions": actions})
        if procs:
            children["procedures"] = procs

        # Add PLEs to bundle
        pricing_items = []
        for ple in ple_per_product.get(product_id, []):
            pe = pricing_element_per_id.get(ple.get("vlocity_cmt__PricingElementId__c"))
            pv_id = ple.get("vlocity_cmt__PricingElementId__r.vlocity_cmt__PricingVariableId__c") or (pe.get("vlocity_cmt__PricingVariableId__c") if pe else None)
            pv = pricing_variable_per_id.get(pv_id) if pv_id else None
            bindings = bindings_per_pricing_var.get(pv_id, []) if pv_id else []
            pricing_items.append({
                "entity": "PriceListEntry",
                "record": ple,
                "pricing_element": pe,
                "pricing_variable": pv,
                "bindings": bindings,
            })
        if pricing_items:
            children["pricing"] = pricing_items

        # Add Layouts/UI by Product2.ObjectTypeId to bundle
        layouts = build_layout_bundle(prod.get("vlocity_cmt__ObjectTypeId__c"))
        if layouts:
            children["layouts"] = layouts

        return {"entity": "Product2", "record": prod, "children": children}

    # Renderer expects a list of product nodes
    return [build_product_node(product_id)]

