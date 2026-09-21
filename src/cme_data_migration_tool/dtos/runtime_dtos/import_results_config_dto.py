from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf

class ImportResultsConfigDTO(BaseDTO):

    @staticmethod
    def getinstance(resultconfig):
        if resultconfig.endswith('.json'):
            resultconfig = resultconfig[:-len('.json')]
        instance = ImportResultsConfigDTO.from_json_file_path('./results/'+resultconfig)
        if instance is None:
            raise FileNotFoundError('Import results file not found: ./results/{}.json'.format(resultconfig))
        return instance
    
    def __init__(self, **kwargs):
        self.import_configs = kwargs
