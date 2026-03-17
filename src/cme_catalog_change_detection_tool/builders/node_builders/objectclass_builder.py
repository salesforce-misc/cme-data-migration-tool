from typing import List, Dict, Any


class ObjectClassBuilder:

    def __init__(self, results) -> None:
        self.results = results
        

    def build_node(self) -> Dict[str, Any]:
        object_class_nodes = []
        all_objectclasses_map = {r.get("Id"): r for r in self.results.get("ObjectClass")}
        for object_class in all_objectclasses_map.values():
            object_class_nodes.append(self._build_object_class_node(object_class))
        return {"ObjectClass": object_class_nodes}

    def _build_object_class_node(self, object_class: Any) -> Dict[str, Any]:
        children: Dict[str, Any] = {}
        # ObjectFieldAttribute
        children["ObjectFieldAttribute"] = self._build_object_field_attribute_node(object_class.get("Id"))
        # AttributeBindings
        children["AttributeBindings"] = self._build_attribute_bindings_node(object_class.get("Id"))

        return {"entity": "ObjectClass", "record": object_class, "children": children}

    def _build_object_field_attribute_node(self, object_class_id: str) -> Dict[str, Any]:
        object_field_attribute_nodes = []
        for object_field_attribute in self.results.get("ObjectFieldAttribute"):
            ocid = object_field_attribute.get("vlocity_cmt__ObjectClassId__c")
            if ocid and ocid == object_class_id:
                object_field_attribute_nodes.append({"entity": "ObjectFieldAttribute", "record": object_field_attribute})
        return object_field_attribute_nodes

    def _build_attribute_bindings_node(self, object_class_id: str) -> Dict[str, Any]:
        attribute_binding_nodes = []
        for attribute_binding in self.results.get("AttributeBinding"):
            ocid = attribute_binding.get("vlocity_cmt__ObjectClassId__c")
            if ocid and ocid == object_class_id:
                attribute_binding_nodes.append({"entity": "AttributeBinding", "record": attribute_binding})   
        return attribute_binding_nodes
