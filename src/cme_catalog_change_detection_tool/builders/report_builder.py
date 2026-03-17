from __future__ import annotations

from typing import List, Dict, Any

from src.cme_catalog_change_detection_tool.builders.node_builders.rule_builder import RuleBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.pricing_builder import PricingBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.attribute_builder import AttributeBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.calculation_builder import CalculationBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.objectlayout_builder import ObjectLayoutBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.objectclass_builder import ObjectClassBuilder
from src.cme_catalog_change_detection_tool.utils.config import AppConfig
from src.cme_catalog_change_detection_tool.builders.html_builder import HtmlBuilder
from src.cme_catalog_change_detection_tool.builders.node_builders.product_builder import ProductBuilder

"""
Hierarchy of report:
--------------------
Product2
    - AttributeAssignment
    - RuleAssignment
    - OverrideDefinition
    - PriceListEntry
        - RuleAssignment
    - ProductSpec
        - ProductChildItem
            - Product2
    - ProductChildItem
            - Product2
                - ProductChildItem
                    - Product2

ObjectClass
    - ObjectFieldAttribute
    - AttributeBinding

ObjectLayout
    - ObjectFacet
    - ObjectSection
    - ObjectElement
    - UIFacet
    - UISection

AttributeCategories
    - Attributes
        - Picklists
            - PicklistValues

PricingElement
    - PricingVariable
        - PricingVariableBinding

ProductRelationship
    - RuleAction

ProductConfigurationProcedure

Rule
    - RuleVariable
    - RuleFilter
    - EntityFilter
    - EntityFilterCondition
    - EntityFilterMember
    - EntityFilterConditionArgument

CalculationMatrix
    - CalculationMatrixVersion
        - CalculationMatrixRows

CalculationProcedure
    - CalculationProcedureVersion
        - CalculationProcedureStep

CpqConfigurationSetup

"""

class ReportBuilder:
    '''
    Report Builder
    '''
    def __init__(self, cfg: AppConfig, results: Dict[str, List[Dict[str, Any]]], history_by_parent: Dict[str, List[Dict[str, Any]]]) -> None:
        self.results = results
        self.html_builder = HtmlBuilder(cfg, history_by_parent)

    def build_hierarchy_report(self, root_product_id: str):
        self._build_product_node(root_product_id)
        self._build_object_class_node()
        self._build_object_layout_node()
        self._build_attribute_category_node()
        self._build_pricing_element_node()
        self._build_rule_node()
        self._build_calculation_node()
        self.html_builder.write_html()

        
    def _build_product_node(self, product_id: str):
        product_node = ProductBuilder(self.results).build_node(product_id)
        self.html_builder.traverse_nodes(product_node, 0)
        
    def _build_object_class_node(self):
        object_class_nodes = ObjectClassBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(object_class_nodes, 0)

    def _build_object_layout_node(self):
        object_layout_nodes = ObjectLayoutBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(object_layout_nodes, 0)

    def _build_attribute_category_node(self):
        attribute_category_nodes = AttributeBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(attribute_category_nodes, 0)

    def _build_pricing_element_node(self):
        pricing_element_nodes = PricingBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(pricing_element_nodes, 0)
    
    def _build_rule_node(self):
        rule_nodes = RuleBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(rule_nodes, 0)

    def _build_calculation_node(self):
        calculation_nodes = CalculationBuilder(self.results).build_node()
        self.html_builder.traverse_nodes(calculation_nodes, 0)
