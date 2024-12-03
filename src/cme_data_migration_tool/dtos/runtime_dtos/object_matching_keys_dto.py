from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf

class ObjectMatchingKeyDTO(BaseDTO):

    def __init__(self, orgconfig, objectconfig, matchingkeys):
        self.matching_keys = matchingkeys
        self.objectconfig = objectconfig
        self.orgconfig = orgconfig
        self.matching_key_results = {}
        QueryUtils.query_by_matching_keys(self.objectconfig, self.orgconfig, list(self.matching_keys), self.matching_key_pecord_processor)

    def matching_key_pecord_processor(self, objectname, record, orgconfig, referencefield):
        results = {}
        for recordfieldname,recordfielddata in record.items():
            key = nsf.mask(orgconfig, recordfieldname)
            value = recordfielddata
            if isinstance(recordfielddata, OrderedDict):
                pass
            else:
                results[key] = value
        matchingkeymap = QueryUtils.generatematchingkeyinfo(self.objectconfig.objectname, results)    
        self.matching_key_results[matchingkeymap['matchingkey']] = results['id']
        return None
