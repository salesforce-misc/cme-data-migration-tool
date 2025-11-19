from __future__ import annotations
import json
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set
import yaml
from src.cme_catalog_change_detection_tool.utils.salesforce_client import SalesforceClient
from src.cme_catalog_change_detection_tool.utils.config import AppConfig



@dataclass
class QueryDefinition:
    name: str
    api_name: str
    base: str
    where: Optional[str] = None
    where_any_of: List[Dict[str, str]] = field(default_factory=list)
    fields_to_collect: List[str] = field(default_factory=list)
    output_set: Optional[str] = None


class SoqlEngine:
    '''
    SOQL Engine
    '''
    def __init__(self, sf_client: SalesforceClient, config: AppConfig) -> None:
        self.sf_client = sf_client
        self.config = config
        self.catalog_map: Dict[str, Set[str]] = {}
        self.results: Dict[str, List[Dict[str, Any]]] = {}
        # Load query definitions
        self.query_defs = self._load_query_defs('src/cme_catalog_change_detection_tool/queries/epc.yaml')
        # Add product_id to catalog_map
        self.catalog_map.setdefault("product_ids", set()).add(config.product_id)

    def _load_query_defs(self, path: str) -> Dict[str, QueryDefinition]:
        '''
        Load epc.yaml & Queries
        '''
        nodes: Dict[str, QueryDefinition] = {}
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        
        for name, spec in raw.get("queries", {}).items():
            nodes[name] = QueryDefinition(
                name=name,
                base=spec["base"],
                api_name=spec["api_name"] if "api_name" in spec else None,
                where=spec.get("where"),
                where_any_of=spec.get("where_any_of", spec.get("any_of_sets", [])),
                fields_to_collect=spec.get("fields_to_collect", []),
                output_set=spec.get("output_set"),
            )
        return nodes


    def process_entity_node(self, entity_name: str) -> List[Dict[str, Any]]:
        '''
        Run single Query definition
        '''
        node = self.query_defs[entity_name]
        # Run SOQL
        soqls = self._prepare_soqls(node)
        all_rows: List[Dict[str, Any]] = []
        for soql in soqls:
            rows = self.sf_client.query(soql)
            all_rows.extend(rows)

        # De-dupe rows
        if all_rows:
            seen_ids: Set[str] = set()
            deduped_rows: List[Dict[str, Any]] = []
            for r in all_rows:
                rid = r.get("Id")
                if rid:
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                deduped_rows.append(r)
            all_rows = deduped_rows

        self.results[entity_name] = all_rows

        # Collect Id & fields
        self._collect_fields(node, all_rows)
        return all_rows


    def _prepare_soqls(self, node: QueryDefinition) -> List[str]:
        '''
        Prepare SOQLs for the node, chunk it if it is a large query
        '''
        soqls: List[str] = []
        dynamic_where: str = None
        if node.where_any_of:
            for entry in node.where_any_of:
                dependency_set = entry.get("if_set")
                dependency_set_values = self.catalog_map.get(dependency_set)
                if dependency_set_values:
                    for dependency_chunk in (list(self._chunked_set(dependency_set_values, 200))):
                        where_clause_tmpl = entry.get("where")
                        in_list = ",".join([f"'{v}'" for v in dependency_chunk])
                        where_clause = where_clause_tmpl.replace(f"${{{dependency_set}}}", in_list)
                        full_soql = self._build_soql(node, where_clause)
                        soqls.append(full_soql)

        else:
            if node.where:
                # De-dupe dependencies
                dep_names = re.findall(r"\$\{([a-zA-Z0-9_]+)\}", node.where)
                unique_dep_names: List[str] = []
                for name in dep_names:
                    if name not in unique_dep_names:
                        unique_dep_names.append(name)

                for dependency_set in unique_dep_names:
                    dependency_set_values = self.catalog_map.get(dependency_set)
                    if dependency_set_values:
                        for dependency_chunk in (list(self._chunked_set(dependency_set_values, 200))):
                            where_clause_tmpl = node.where
                            in_list = ",".join([f"'{v}'" for v in dependency_chunk])
                            where_clause = where_clause_tmpl.replace(f"${{{dependency_set}}}", in_list)
                            full_soql = self._build_soql(node, where_clause)
                            soqls.append(full_soql)
            else:
                soqls.append(node.base)

        return soqls


    def _chunked_set(self, iterable: Iterable[str], size: int) -> Iterable[List[str]]:
        '''
        Split an iterable into chunks of a given size
        '''
        chunk: List[str] = []
        for item in iterable:
            chunk.append(item)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
            
    def _build_soql(self, node: QueryDefinition, where: str) -> str:
        '''
        Base SOQL + Where clause
        '''               
        full_soql = node.base
        if where:
            full_soql = f"{full_soql} WHERE {where}"

        return full_soql


    def _collect_fields(self, node: QueryDefinition, rows: List[Dict[str, Any]]) -> None:
        '''
        Collect fields from the rows
        '''
        if node.output_set:
            target = self.catalog_map.setdefault(node.output_set, set())
            target.update(r["Id"] for r in rows)
                
        for f in node.fields_to_collect:
            set_name, field_name = f.split(":", 1)
            target = self.catalog_map.setdefault(set_name, set())
            for r in rows:
                value = r
                for part in field_name.split("."):
                    if value is None:
                        break
                    value = value.get(part)
                if value is not None:
                    target.add(value)


    def save_results(self, output_dir: str) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for name, rows in self.results.items():
            with open(Path(output_dir) / f"{name}.json", "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2)


    def build_history_soql(self, hist_sobj: str, parent_field: str, ids_csv: str, cutoff_iso: str) -> Optional[str]:
        """
        Build the SOQL query for History object
        """
        HISTORY_DEFAULT_BASE: str = (
            "SELECT Id, ${parent_field}, Field, OldValue, NewValue, CreatedDate, CreatedById FROM ${history_sobject}"
        )
        HISTORY_DEFAULT_WHERE: str = (
            "${parent_field} IN (${ids}) AND CreatedDate >= ${cutoff_iso}"
        )
        base_query = HISTORY_DEFAULT_BASE.replace("${history_sobject}", hist_sobj).replace("${parent_field}", parent_field)
        where_clause = HISTORY_DEFAULT_WHERE.replace("${parent_field}", parent_field).replace("${ids}", ids_csv).replace("${cutoff_iso}", cutoff_iso)
        full = f"{base_query} WHERE {where_clause}"
        return full
