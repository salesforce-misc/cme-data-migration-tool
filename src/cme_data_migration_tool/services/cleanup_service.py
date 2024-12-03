import uuid
from prettytable import PrettyTable

from src.cme_data_migration_tool.dtos.configurations_dtos.import_sequence_dto import ImportSequenceDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.import_sequence_dto import ImportSequenceDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_matching_keys_dto import ObjectMatchingKeyDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_results_dto import ObjectResultsDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO

from src.cme_data_migration_tool.services.base_service import BaseService

from src.cme_data_migration_tool.utils.dml_utils import DMLUtils


class CleanupService(BaseService):

    def __init__(self, saveresult, result_name):
        self.import_result_filename = uuid.uuid4().hex
        self.test = False
        self.printtest= False
        self.result_name = result_name
        self.saveresult = saveresult
        self.orgconfig = OrgConfigDTO.getdestinationorg()
        
        self.results_root_path = './results/'+self.result_name+'/'
        self.matching_key_results_directory_path = self.results_root_path + 'zmatchingkeys/'

    def import_data(self):
        table = PrettyTable()
        table.field_names = ["Object Name", "Deleted Records Count"]
        importsequencedto = ImportSequenceDTO.getinstance()
        for sequenceobject in importsequencedto.import_sequence:
            results_directory_path = self.results_root_path+sequenceobject + '/'
            object_result_filepath = results_directory_path + '/' + '76fc095130244957b88237923e9fb2ad'
            objectconfig = MigrationObjTemplateDTO.getdestinationinstance(sequenceobject)
            objectmatchingkeyresult = ObjectMatchingKeyDTO.from_results(self.orgconfig, objectconfig, self.matching_key_results_directory_path+sequenceobject, {})
            if objectmatchingkeyresult is None:
                continue
            objectstoupsertresult = ObjectResultsDTO.from_results(self.orgconfig, objectconfig, object_result_filepath, {'matchingkeyresults' : objectmatchingkeyresult})
            DMLUtils.delete(objectstoupsertresult)
            table.add_row([sequenceobject, GlobalResultsDTO.existing_record_count.get(sequenceobject)])

        print(table)
        return None