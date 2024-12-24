# from src.cme_data_migration_tool.services.export_service import ExportService
import json
import os
import uuid
from src.cme_data_migration_tool.actions.base_action import BaseAction
from prettytable import PrettyTable
from alive_progress import alive_bar

from src.cme_data_migration_tool.services.export_service import ExportService
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.services.export_bundle import ExportBundle
from src.cme_data_migration_tool.services.export_configuration import ExportConfiguration


class ExportAction(BaseAction):

    def __init__(self, args):
        self.orgconfig = OrgConfigDTO.getsourceorg()
        self.ids = args.ids
        self.config = args.config
        self.resultpath = args.resultpath
        self.object = nsf.mask(self.orgconfig, args.object)

    def execute_action(self):
        if self.config == "sobject":
            self.finalexport(self.ids, self.object)
            self.savefile('./results/' + 'epc_import_args_'+str(uuid.uuid4())+'.json',
                          GlobalResultsDTO.globalobjectimportfileinfomap, 'import configurations')
        elif self.object == "product2" or self.object == "vlocity_cmt__promotion__c":
            ExportBundle().export(self.object, self.ids)
        else:
            ExportConfiguration(self.object, self.ids).export()

        table = PrettyTable()
        table.field_names = ["Object Name", "Export Record Count"]
        for globalobjectname in GlobalResultsDTO.globalobjectmap:
            table.add_row(
                [globalobjectname, GlobalResultsDTO.globalobjectmap.get(globalobjectname)])
        print(table)
        return None

    def savefile(self, fpath, result, resultname):
        with alive_bar(1, bar='classic', title="saving results of "+resultname) as bar:
            if os.path.isfile(fpath):
                os.remove(fpath)
            with open(fpath, 'w') as f:
                json.dump(result, f)
            bar()

    def finalexport(self, objectids, objname):
        for i in range(0, len(objectids), 200):
            objectids_to_export_chunk = objectids[i:i + 200]
            exportservice = ExportService(
                True, objname, objname, 'id', objectids_to_export_chunk)
            exportservice.export()
