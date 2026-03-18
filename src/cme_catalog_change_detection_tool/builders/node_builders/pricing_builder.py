from typing import List, Dict, Any


class PricingBuilder:

    def __init__(self, results) -> None:
        self.results = results

    def build_node(self) -> Dict[str, Any]:
        return {"PricingElement": self._build_pricing_element_node()}

    def _build_pricing_element_node(self) -> Dict[str, Any]:
        all_pricing_elements_map = {r.get("Id"): r for r in self.results.get("PricingElement")}
        pricing_element_nodes = []
        for pricing_element in all_pricing_elements_map.values():
            children: Dict[str, Any] = {}
            children["PricingVariable"] = self._build_pricing_variable_node(pricing_element.get("vlocity_cmt__PricingVariableId__c"))
            children["PricingVariableBinding"] = self._build_pricing_variable_binding_node(pricing_element.get("vlocity_cmt__PricingVariableId__c"))
            pricing_element_nodes.append({"entity": "PricingElement", "record": pricing_element, "children": children})
        return pricing_element_nodes

    def _build_pricing_variable_node(self, pricing_variable_id: str) -> Dict[str, Any]:
        all_pricing_variables_map = {r.get("Id"): r for r in self.results.get("PricingVariable")}
        pricing_variable_nodes = []
        for pricing_variable in all_pricing_variables_map.values():
            if pricing_variable.get("Id") == pricing_variable_id:
                pricing_variable_nodes.append({"entity": "PricingVariable", "record": pricing_variable})
        return pricing_variable_nodes

    def _build_pricing_variable_binding_node(self, pricing_variable_id: str) -> Dict[str, Any]:
        all_pricing_variable_bindings_map = {r.get("Id"): r for r in self.results.get("PricingVariableBinding")}
        pricing_variable_binding_nodes = []
        for pricing_variable_binding in all_pricing_variable_bindings_map.values():
            if pricing_variable_binding.get("vlocity_cmt__PricingVariableId__c") == pricing_variable_id:
                pricing_variable_binding_nodes.append({"entity": "PricingVariableBinding", "record": pricing_variable_binding})
        return pricing_variable_binding_nodes   