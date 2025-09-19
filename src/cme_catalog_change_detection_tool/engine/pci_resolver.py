from __future__ import annotations

from typing import Dict, List, Set

from src.cme_catalog_change_detection_tool.utils.salesforce_client import SalesforceClient
from src.cme_catalog_change_detection_tool.utils.config import AppConfig


class PCIResolver:
    '''
    Resolves child products from PCIs recursively
    '''
    
    def __init__(self, sf_client: SalesforceClient, config: AppConfig) -> None:
        self.sf_client = sf_client
        self.config = config

    def resolve_hierarchy(self, root_product_id: str) -> Set[str]:
        '''
        Resolve all child products from PCIs recursively starting from a single root product Id.
        '''
        all_product_ids: Set[str] = {root_product_id}
        current_level_product_ids: Set[str] = {root_product_id}
        while current_level_product_ids:

            ids_join = ",".join([f"'{i}'" for i in sorted(current_level_product_ids)])
            where = f"vlocity_cmt__ParentProductId__c IN ({ids_join})"
            soql_pci = (
                "SELECT Id, Name, CreatedDate, LastModifiedDate, "
                "vlocity_cmt__ChildProductId__c FROM vlocity_cmt__ProductChildItem__c WHERE "
                + where
            )
            pci_rows = self.sf_client.query(soql_pci)

            # Store all child product ids for next iteration
            new_child_product_ids: Set[str] = set()
            for row in pci_rows:
                child_id = row.get("vlocity_cmt__ChildProductId__c")
                if child_id and child_id not in all_product_ids:
                    new_child_product_ids.add(child_id)
                    all_product_ids.add(child_id)
            current_level_product_ids = new_child_product_ids

        return all_product_ids


