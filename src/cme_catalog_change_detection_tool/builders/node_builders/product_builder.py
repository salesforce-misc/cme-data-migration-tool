from typing import List, Dict, Any


class ProductBuilder:

    def __init__(self, results) -> None:
        self.results = results
        self.visited_products = set[str]() 
        self.all_products_map = {r.get("Id"): r for r in self.results.get("Product2")}

    def build_node(self, product_id: str) -> Dict[str, Any]:
        return {"Product2": [self._build_product_node(product_id)]}

    def _build_product_node(self, product_id: str) -> Dict[str, Any]: 
        self.visited_products.add(product_id)
        prod = self.all_products_map.get(product_id, {})
        children: Dict[str, Any] = {}

        # AttributeAssignment
        children["AttributeAssignment"] = self._build_attribute_assignment_node(product_id)
        # RuleAssignment
        children["RuleAssignment"] = self._build_rule_assignment_node(product_id)
        # OverrideDefinition
        children["OverrideDefinition"] = self._build_override_definition_node(product_id)
        # PriceListEntry
        children["PriceListEntry"] = self._build_price_list_entry_node(product_id)
        # ProductSpec
        spec_id = prod.get("vlocity_cmt__ProductSpecId__c")
        if spec_id:
            children["ProductSpecification"] = self._build_product_node(spec_id)
        # ProductChildItem 
        children["ProductChildItem"] = self._build_pci_node(product_id)

        return {"entity": "Product2", "record": prod, "children": children}

    def _build_pci_node(self, product_id: str) -> Dict[str, Any]:
        children = []

        for pci in self.results.get("ProductChildItem"):
            parent_id = pci.get("vlocity_cmt__ParentProductId__c")
            if parent_id and parent_id == product_id:
                child_product_nodes = []
                if pci["vlocity_cmt__ChildProductId__c"]:
                    child_product_node = self._build_product_node(pci["vlocity_cmt__ChildProductId__c"])
                    child_product_nodes.append(child_product_node)
                children.append({"entity": "ProductChildItem", "record": pci, "children": {"Product2": child_product_nodes}})
        return children

    def _build_attribute_assignment_node(self, product_id: str) -> Dict[str, Any]:        
        attribute_assignments = []
        for attr_assignment in self.results.get("AttributeAssignment"):
            object_id = attr_assignment.get("vlocity_cmt__ObjectId__c")
            if object_id and object_id == product_id:
                attribute_assignments.append({"entity": "AttributeAssignment", "record": attr_assignment})
        return attribute_assignments

    def _build_rule_assignment_node(self, product_id: str) -> Dict[str, Any]:
        rule_assignments = []
        for rule_assignment in self.results.get("RuleAssignment"):
            object_id = rule_assignment.get("vlocity_cmt__ObjectId__c")
            if object_id and object_id == product_id:
                rule_assignments.append({"entity": "RuleAssignment", "record": rule_assignment})
        return rule_assignments

    def _build_override_definition_node(self, product_id: str) -> Dict[str, Any]:
        override_definitions = []
        for override_definition in self.results.get("OverrideDefinition"):
            override_product_id = override_definition.get("vlocity_cmt__ProductId__c")
            if override_product_id and override_product_id == product_id:
                override_definitions.append({"entity": "OverrideDefinition", "record": override_definition})
        return override_definitions

    def _build_price_list_entry_node(self, product_id: str) -> Dict[str, Any]:
        price_list_entries = []
        for ple in self.results.get("PriceListEntry"):
            object_id = ple.get("vlocity_cmt__ProductId__c")
            if object_id and object_id == product_id:
                children = self._build_rule_assignment_node(ple["Id"])
                price_list_entries.append({"entity": "PriceListEntry", "record": ple, "children": children})
        return price_list_entries
        
