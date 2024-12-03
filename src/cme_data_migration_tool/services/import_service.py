import uuid
from prettytable import PrettyTable
from os import walk

from src.cme_data_migration_tool.dtos.configurations_dtos.import_sequence_dto import ImportSequenceDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.import_sequence_dto import ImportSequenceDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_matching_keys_dto import ObjectMatchingKeyDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_results_dto import ObjectResultsDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.import_results_config_dto import ImportResultsConfigDTO
from src.cme_data_migration_tool.utils.nsf import nsf

from src.cme_data_migration_tool.services.base_service import BaseService

from src.cme_data_migration_tool.utils.dml_utils import DMLUtils


class ImportService(BaseService):

    def __init__(self, saveresult, result_filename):
        self.test = False
        self.printtest= False
        self.saveresult = saveresult
        self.orgconfig = OrgConfigDTO.getdestinationorg()
        self.results_config = ImportResultsConfigDTO.getinstance(result_filename)

    def import_data(self):
        table = PrettyTable()
        table.field_names = ["Object Name", "Import Existing Records Count", "Import New Records Count"]
        importsequencedto = ImportSequenceDTO.getinstance()
        for sequenceobject in importsequencedto.import_sequence:
            print('preparing objects to upsert')
            objectstoupsertresult = ObjectResultsDTO.getinstance(self.results_config, sequenceobject)
            if(objectstoupsertresult is None):
                continue
            print('upserting objects')
            DMLUtils.upsert(objectstoupsertresult)
            self.savefile('./import_results/'+sequenceobject+'.json', objectstoupsertresult.get_results(), sequenceobject)
            table.add_row([sequenceobject, objectstoupsertresult.existing_record_count, objectstoupsertresult.new_record_count])
        print(table)
        return None
    
    