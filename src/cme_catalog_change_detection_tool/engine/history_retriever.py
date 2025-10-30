from __future__ import annotations

from rich.table import Table
from rich.console import Console
from dateutil import parser as date_parser
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from src.cme_catalog_change_detection_tool.utils.salesforce_client import SalesforceClient


HISTORY_DEFAULT_BASE: str = (
    "SELECT Id, ${parent_field}, Field, OldValue, NewValue, CreatedDate, CreatedById FROM ${history_sobject}"
)
HISTORY_DEFAULT_WHERE: str = (
    "${parent_field} IN (${ids}) AND CreatedDate >= ${cutoff_iso}"
)


def _chunked(items: Iterable[str], size: int) -> Iterable[List[str]]:
    '''
    Return a chunk of items based on the input size
    '''
    chunk: List[str] = []
    for i in items:
        chunk.append(i)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def derive_history_sobject_name(object_api_name: str) -> str:
    """
    Derive the History SObject API name from SObject API name.
    - Standard: Product2 -> Product2History
    - Custom: vlocity_cmt__ProductRelationship__c -> vlocity_cmt__ProductRelationship__History
    """
    if object_api_name.endswith("__c"):
        return object_api_name[:-3] + "__History"
    return object_api_name + "History"


def history_parent_field(object_api_name: str) -> str:
    """
    Determine the Parent lookup field name for History object
    - Standard objects: eg: Product2 -> Product2Id
    - Custom objects: Use ParentId
    """
    if object_api_name.endswith("__c"):
        return "ParentId"
    return f"{object_api_name}Id"


def _build_history_soql(hist_sobj: str, parent_field: str, ids_csv: str, cutoff_iso: str) -> Optional[str]:
    """
    Build the SOQL query for History object
    """
    base_query = HISTORY_DEFAULT_BASE.replace("${history_sobject}", hist_sobj).replace("${parent_field}", parent_field)
    where_clause = HISTORY_DEFAULT_WHERE.replace("${parent_field}", parent_field).replace("${ids}", ids_csv).replace("${cutoff_iso}", cutoff_iso)
    full = f"{base_query} WHERE {where_clause}"
    return full


def fetch_history_map(
    sf_client: SalesforceClient,
    ids: Set[str],
    hist_sobj: str,
    parent_field: str,
    cutoff_iso: str,
    chunk_size: int = 200,
) -> List[Dict[str, Any]]:
    """
    Fetch History records for the given IDs
    """

    entity_rows = []
    for chunk in _chunked(sorted(ids), chunk_size):
        ids_csv = ",".join([f"'{i}'" for i in chunk])
        soql = _build_history_soql(hist_sobj, parent_field, ids_csv, cutoff_iso)
        rows = sf_client.query(soql)
        entity_rows.extend(rows)

    return entity_rows


def collect_history_for_recent_changes(
    sf_client: SalesforceClient,
    engine: Any,
    execution_order: List[str],
    cutoff_iso: str,
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, int]]:
    """
    - Fetch History entities from org
    - Fetch all modified record Ids since cutoff date
    - Fetch History records for the modified records
    - Return map of parent Id to History records
    """

    cutoff_dt = date_parser.parse(cutoff_iso)
    if cutoff_dt.tzinfo is None:
        cutoff_dt = cutoff_dt.replace(tzinfo=timezone.utc)

    # Get all Enitities with Field History Tracking enabled
    print("\nFetching Entities with Field History Tracking enabled")
    available_sobjects = sf_client.list_sobject_names()
    history_table = Table(show_header=True, header_style="bold magenta")
    history_table.add_column("Entity", style="cyan")
    history_table.add_column("History SObject")
    history_table.add_column("Parent Field")

    history_name_api_map: Dict[str, str] = {}
    parent_field_map: Dict[str, str] = {}

    # Fetch Entity Name -> API Name mapping
    for name, qd in getattr(engine, "query_defs", {}).items():
        if(qd.api_name):
            hist_sobj = derive_history_sobject_name(qd.api_name)
            if hist_sobj in available_sobjects:
                history_name_api_map[name] = hist_sobj
                parent_field_map[name] = history_parent_field(qd.api_name)
                history_table.add_row(name, hist_sobj, history_parent_field(qd.api_name))

    if history_name_api_map:
        Console().print(history_table)
    else:
        print("Field History Tracking is not enabled for any of the configured entities!")

    # Get all modified record Ids by Entity name since cutoff date
    print(f"\nFetching Field History for entities")    
    history_by_parent: Dict[str, List[Dict[str, Any]]] = {}
    history_counts: Dict[str, int] = {}
    entity_index = 0
    for entity_name, rows in getattr(engine, "results", {}).items():
        ids: Set[str] = set()
        for r in rows or []:
            lm = date_parser.parse(r.get("LastModifiedDate")) if r.get("LastModifiedDate") else None
            if lm and lm.tzinfo is None:
                lm = lm.replace(tzinfo=timezone.utc)
            if lm and lm >= cutoff_dt:
                rid = r.get("Id")
                if rid:
                    ids.add(rid)

        # Only fetch if this entity has history enabled and mappings are available
        if ids and (entity_name in history_name_api_map) and (entity_name in parent_field_map):
            hist_sobj = history_name_api_map[entity_name]
            parent_field = parent_field_map[entity_name]
            history_rows = fetch_history_map(sf_client, ids, hist_sobj, parent_field, cutoff_iso)
            # Group rows by the parent Id field so report_generator can access by record Id
            for h in history_rows or []:
                pid = (h or {}).get(parent_field)
                history_by_parent.setdefault(pid, []).append(h)
            history_counts[entity_name] = len(history_rows)
            entity_index += 1
            print(f"Progress: ({entity_index}) {entity_name}: {len(history_rows)} rows")

    # Print History summary table
    if history_counts:
        htable = Table(show_header=True, header_style="bold magenta")
        htable.add_column("History Entity", style="cyan")
        htable.add_column("Rows", justify="right")
        for entity in execution_order:
            if entity in history_counts:
                htable.add_row(f"{entity}History", str(history_counts[entity]))
        Console().print(htable)

    return history_by_parent
