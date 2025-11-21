#!/usr/bin/env python3
from __future__ import annotations

"""
CLI entrypoint
- Reads Salesforce credentials and settings from a JSON file
- Connects to the Salesforce org
- Discovers all related Product2 records via recursive traversalof Product Child Items (PCI)
- Reads a YAML config of SOQL queries & retrieves entities 
- Creates HTML report of entities in output directory
"""

import argparse
import json
from pathlib import Path
from typing import List
import sys
import warnings
# Suppress macOS LibreSSL warning from urllib3 before it initializes
warnings.filterwarnings(
    "ignore",
    message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
    category=Warning,
)

import webbrowser
from rich import print
from rich.console import Console
from rich.table import Table
from datetime import datetime, timezone, timedelta
from src.cme_catalog_change_detection_tool.utils.config import AppConfig
from src.cme_catalog_change_detection_tool.utils.salesforce_client import SalesforceClient
from src.cme_catalog_change_detection_tool.engine.soql_engine import SoqlEngine
from src.cme_catalog_change_detection_tool.engine.pci_resolver import PCIResolver
from src.cme_catalog_change_detection_tool.utils.hierarchy_builder import build_product_hierarchy
from src.cme_catalog_change_detection_tool.utils.report_generator import generate_hierarchical_html_report
from src.cme_catalog_change_detection_tool.engine.history_retriever import collect_history_for_recent_changes


# Execute queries in order
execution_order: List[str] = [
    "Product2",
    "ProductChildItem",
    "ObjectClass",
    "ObjectFieldAttribute",
    "AttributeBinding",
    "AttributeAssignment",
    "OverrideDefinition",
    "ProductRelationship",
    "ProductConfigurationProcedure",
    "RuleAction",
    "Rule",
    "RuleVariable",
    "RuleFilter",
    "EntityFilter",
    "EntityFilterCondition",
    "EntityFilterMember",
    "EntityFilterConditionArgument",
    "PriceListEntry",
    "PricingElement",
    "PricingVariable",
    "PricingVariableBinding",
    "ObjectLayout",
    "ObjectFacet",
    "ObjectSection",
    "ObjectElement",
    "UIFacet",
    "UISection",
    "Attribute",
    "AttributeCategory",
    "Picklist",
    "PicklistValue",
    "CalculationMatrix",
    "CalculationMatrixVersion",
    "CalculationMatrixRow",
    "CalculationProcedure",
    "CalculationProcedureVersion",
    "CalculationProcedureStep",
    "CpqConfigurationSetup",
]


def main() -> None:
    """
    Detect EPC catalog changes
    """
    # Read CLI args (only file path; all other settings come from JSON)
    parser = argparse.ArgumentParser(description="Detect EPC catalog changes from Salesforce")
    parser.add_argument("-f", "--file", required=True, help="Input JSON file path")
    args = parser.parse_args()
    cfg = AppConfig.from_file(args.file)

    # Connect to Salesforce Org
    print(f"Connecting to Salesforce Org (domain={cfg.domain}) as {cfg.username}...")
    sf_client = SalesforceClient(
        username=cfg.username,
        password=cfg.password,
        instance_url=cfg.instance_url,
        domain=cfg.domain,
    )
    engine = SoqlEngine(sf_client=sf_client, config=cfg)

    # Get all child products via PCI traversal
    resolver = PCIResolver(sf_client, cfg)
    all_products = resolver.resolve_hierarchy(cfg.product_id)
    for product_id in all_products:
        engine.catalog_map.setdefault("product_ids", set()).add(product_id)

    # Execute queries in order
    print("\nFetching Product bundle & its related entity records")
    total = len(execution_order)
    entity_counts: List[tuple[str, int]] = []
    for idx, entity_name in enumerate(execution_order, start=1):
        rows = engine.process_entity_node(entity_name)
        count = len(rows)
        entity_counts.append((entity_name, count))
        progress = int((idx / total) * 100)
        print(f"Progress: {progress}% ({idx}/{total}) {entity_name}: {count} rows")

    # Save results to JSON files
    out_dir = str(Path(cfg.output_dir) / cfg.timestamp_folder)
    engine.save_results(out_dir)
    print(f"Results written to {out_dir}")

    # Print Console summary
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Entity", style="cyan")
    table.add_column("Rows", justify="right")
    for entity, count in entity_counts:
        table.add_row(entity, str(count))
    Console().print(table)

    # Build hierarchy of objects based on dependencies
    products_tree = build_product_hierarchy(engine, cfg.product_id)
    report_path = str(Path(out_dir) / "epc_changes.html")


    # Prepare cutoff and fetch history in one call
    n = cfg.number_of_days
    cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%SZ")
    history_by_parent = collect_history_for_recent_changes(
        sf_client=sf_client,
        engine=engine,
        execution_order=execution_order,
        cutoff_iso=cutoff_iso,
    )

    # Build HTML report
    title = f"EPC Changes in last {n} days"
    subtitle = f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)"

    # Write HTML report
    generate_hierarchical_html_report(
        products=products_tree,
        output_path=report_path,
        title=title,
        subtitle=subtitle,
        instance_url=cfg.instance_url,
        cutoff_iso=cutoff_iso,
        engine_results=engine.results,
        history_by_parent_id=history_by_parent,
    )
    print(f"HTML report written to {report_path}")

    # Open HTML report in browser
    try:
        webbrowser.open(f"file://{Path(report_path).absolute()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()


