from typing import List, Dict, Any


class RuleBuilder:

    def __init__(self, results) -> None:
        self.results = results

    def build_node(self) -> Dict[str, Any]:
        return {"ProductRelationship": self._build_product_relationship_node(),
            "ProductConfigurationProcedure": self._build_product_configuration_procedure_node(),
            "Rule": self._build_rule_node()}

    def _build_product_relationship_node(self) -> Dict[str, Any]:
        all_product_relationships_map = {r.get("Id"): r for r in self.results.get("ProductRelationship")}
        product_relationship_nodes = []
        for product_relationship in all_product_relationships_map.values():
            children: Dict[str, Any] = {}
            children["RuleAction"] = self._build_rule_action_node(product_relationship.get("Id"))
            product_relationship_nodes.append({"entity": "ProductRelationship", "record": product_relationship, "children": children})
        return product_relationship_nodes

    def _build_rule_action_node(self, parent_id: str) -> Dict[str, Any]:
        all_rule_actions_map = {r.get("Id"): r for r in self.results.get("RuleAction")}
        rule_action_nodes = []
        for rule_action in all_rule_actions_map.values():
            if rule_action.get("vlocity_cmt__ProductRelationshipId__c") == parent_id or rule_action.get("vlocity_cmt__ProductConfigurationProcedureId__c") == parent_id:
                rule_action_nodes.append({"entity": "RuleAction", "record": rule_action})
        return rule_action_nodes
    
    def _build_product_configuration_procedure_node(self) -> Dict[str, Any]:
        all_product_configuration_procedures_map = {r.get("Id"): r for r in self.results.get("ProductConfigurationProcedure")}
        product_configuration_procedure_nodes = []
        for product_configuration_procedure in all_product_configuration_procedures_map.values():
            children: Dict[str, Any] = {}
            children["RuleAction"] = self._build_rule_action_node(product_configuration_procedure.get("Id"))
            product_configuration_procedure_nodes.append({"entity": "ProductConfigurationProcedure", "record": product_configuration_procedure, "children": children})
        return product_configuration_procedure_nodes

    def _build_rule_node(self) -> Dict[str, Any]:
        all_rules_map = {r.get("Id"): r for r in self.results.get("Rule")}
        rule_nodes = []
        for rule in all_rules_map.values():
            children: Dict[str, Any] = {}
            children["RuleVariable"] = self._build_rule_variable_node(rule.get("Id"))
            children["RuleFilter"] = self._build_rule_filter_node(rule.get("Id"))
            rule_nodes.append({"entity": "Rule", "record": rule, "children": children, })
        return rule_nodes

    def _build_rule_variable_node(self, rule_id: str) -> Dict[str, Any]:
        all_rule_variables_map = {r.get("Id"): r for r in self.results.get("RuleVariable")}
        rule_variable_nodes = []
        for rule_variable in all_rule_variables_map.values():
            if rule_variable.get("vlocity_cmt__RuleId__c") == rule_id:
                rule_variable_nodes.append({"entity": "RuleVariable", "record": rule_variable})
        return rule_variable_nodes

    def _build_rule_filter_node(self, rule_id: str) -> Dict[str, Any]:
        all_rule_filters_map = {r.get("Id"): r for r in self.results.get("RuleFilter")}
        rule_filter_nodes = []
        for rule_filter in all_rule_filters_map.values():
            children: Dict[str, Any] = {}
            if rule_filter.get("vlocity_cmt__RuleId__c") == rule_id:
                children["EntityFilter"] = self._build_entity_filter_node(rule_filter.get("Id"))
                rule_filter_nodes.append({"entity": "RuleFilter", "record": rule_filter, "children": children})
        return rule_filter_nodes

    def _build_entity_filter_node(self, rule_filter_id: str) -> Dict[str, Any]:
        all_entity_filters_map = {r.get("Id"): r for r in self.results.get("EntityFilter")}
        entity_filter_nodes = []
        for entity_filter in all_entity_filters_map.values():
            if entity_filter.get("vlocity_cmt__RuleFilterId__c") == rule_filter_id:
                children: Dict[str, Any] = {}
                children["EntityFilterCondition"] = self._build_entity_filter_condition_node(entity_filter.get("Id"))
                children["EntityFilterMember"] = self._build_entity_filter_member_node(entity_filter.get("Id"))
                entity_filter_nodes.append({"entity": "EntityFilter", "record": entity_filter, "children": children})
        return entity_filter_nodes

    def _build_entity_filter_condition_node(self, entity_filter_id: str) -> Dict[str, Any]:
        all_entity_filter_conditions_map = {r.get("Id"): r for r in self.results.get("EntityFilterCondition")}
        entity_filter_condition_nodes = []
        for entity_filter_condition in all_entity_filter_conditions_map.values():
            if entity_filter_condition.get("vlocity_cmt__EntityFilterId__c") == entity_filter_id:
                children: Dict[str, Any] = {}
                children["EntityFilterConditionArgument"] = self._build_entity_filter_condition_argument_node(entity_filter_condition.get("Id"))
                entity_filter_condition_nodes.append({"entity": "EntityFilterCondition", "record": entity_filter_condition, "children": children})
        return entity_filter_condition_nodes

    def _build_entity_filter_member_node(self, entity_filter_id: str) -> Dict[str, Any]:
        all_entity_filter_members_map = {r.get("Id"): r for r in self.results.get("EntityFilterMember")}
        entity_filter_member_nodes = []
        for entity_filter_member in all_entity_filter_members_map.values():
            if entity_filter_member.get("vlocity_cmt__EntityFilterId__c") == entity_filter_id:
                entity_filter_member_nodes.append({"entity": "EntityFilterMember", "record": entity_filter_member})
        return entity_filter_member_nodes

    def _build_entity_filter_condition_argument_node(self, entity_filter_condition_id: str) -> Dict[str, Any]:
        all_entity_filter_condition_arguments_map = {r.get("Id"): r for r in self.results.get("EntityFilterConditionArgument")}
        entity_filter_condition_argument_nodes = []
        for entity_filter_condition_argument in all_entity_filter_condition_arguments_map.values():
            if entity_filter_condition_argument.get("vlocity_cmt__FilterConditionId__c") == entity_filter_condition_id:
                entity_filter_condition_argument_nodes.append({"entity": "EntityFilterConditionArgument", "record": entity_filter_condition_argument})
        return entity_filter_condition_argument_nodes