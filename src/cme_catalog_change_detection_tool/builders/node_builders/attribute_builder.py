from typing import List, Dict, Any


class AttributeBuilder:

    def __init__(self, results) -> None:
        self.results = results

    def build_node(self) -> Dict[str, Any]:
        return {"AttributeCategory": self._build_attribute_category_node(),
            "Attribute": self._build_attribute_node(),
            "Picklist": self._build_picklist_node(),
            "PicklistValue": self._build_picklist_value_node()}

    def _build_attribute_category_node(self) -> Dict[str, Any]:
        all_attribute_categories_map = {r.get("Id"): r for r in self.results.get("AttributeCategory")}
        attribute_category_nodes = []
        for attribute_category in all_attribute_categories_map.values():
            attribute_category_nodes.append({"entity": "AttributeCategory", "record": attribute_category})
        return attribute_category_nodes

    def _build_attribute_node(self) -> Dict[str, Any]:
        all_attributes_map = {r.get("Id"): r for r in self.results.get("Attribute")}
        attribute_nodes = []
        for attribute in all_attributes_map.values():
            attribute_nodes.append({"entity": "Attribute", "record": attribute})
        return attribute_nodes

    def _build_picklist_node(self) -> Dict[str, Any]:
        all_picklists_map = {r.get("Id"): r for r in self.results.get("Picklist")}
        picklist_nodes = []
        for picklist in all_picklists_map.values():
            picklist_nodes.append({"entity": "Picklist", "record": picklist})
        return picklist_nodes

    def _build_picklist_value_node(self) -> Dict[str, Any]:
        all_picklist_values_map = {r.get("Id"): r for r in self.results.get("PicklistValue")}
        picklist_value_nodes = []
        for picklist_value in all_picklist_values_map.values():
            picklist_value_nodes.append({"entity": "PicklistValue", "record": picklist_value})
        return picklist_value_nodes