from typing import List, Dict, Any


class ObjectLayoutBuilder:

    def __init__(self, results) -> None:
        self.results = results

    def build_node(self) -> Dict[str, Any]:
        return {"ObjectLayout": self._build_object_layout_node(), 
            "ObjectSection": self._build_object_section_node(), 
            "ObjectElement": self._build_object_element_node(), 
            "UIFacet": self._build_ui_facet_node(), 
            "UISection": self._build_ui_section_node()}
    
    def _build_object_layout_node(self) -> Dict[str, Any]:
        all_objectlayouts_map = {r.get("Id"): r for r in self.results.get("ObjectLayout")}
        object_layout_nodes = []
        for object_layout in all_objectlayouts_map.values():
            object_layout_nodes.append({"entity": "ObjectLayout", "record": object_layout})
        return object_layout_nodes

    def _build_object_section_node(self) -> Dict[str, Any]:
        all_objectsections_map = {r.get("Id"): r for r in self.results.get("ObjectSection")}
        object_section_nodes = []
        for object_section in all_objectsections_map.values():
            object_section_nodes.append({"entity": "ObjectSection", "record": object_section})
        return object_section_nodes

    def _build_object_element_node(self) -> Dict[str, Any]:
        all_objectelements_map = {r.get("Id"): r for r in self.results.get("ObjectElement")}
        object_element_nodes = []
        for object_element in all_objectelements_map.values():
            object_element_nodes.append({"entity": "ObjectElement", "record": object_element})
        return object_element_nodes      

    def _build_ui_facet_node(self) -> Dict[str, Any]:
        all_uifacets_map = {r.get("Id"): r for r in self.results.get("UIFacet")}
        ui_facet_nodes = []
        for ui_facet in all_uifacets_map.values():
            ui_facet_nodes.append({"entity": "UIFacet", "record": ui_facet})
        return ui_facet_nodes

    def _build_ui_section_node(self) -> Dict[str, Any]:
        all_uisections_map = {r.get("Id"): r for r in self.results.get("UISection")}
        ui_section_nodes = []
        for ui_section in all_uisections_map.values():
            ui_section_nodes.append({"entity": "UISection", "record": ui_section})
        return ui_section_nodes