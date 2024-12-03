import argparse,json,os
from src.cme_data_migration_tool.actions.base_action import BaseAction
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.services.import_service import ImportService

class ImportAction(BaseAction):

    def __init__(self, args):
        self.orgconfig = OrgConfigDTO.getdestinationorg()
        self.importfile = args.importfile

    def execute_action(self):
        imprortservice = ImportService(False, self.importfile)
        imprortservice.import_data()