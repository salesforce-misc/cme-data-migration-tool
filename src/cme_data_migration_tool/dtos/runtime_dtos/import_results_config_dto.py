from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf

class ImportResultsConfigDTO(BaseDTO):

    @staticmethod
    def getinstance(resultconfig):    
        return ImportResultsConfigDTO.from_json_file_path('./results/'+resultconfig)
    
    def __init__(self, **kwargs):
        self.import_configs = kwargs
