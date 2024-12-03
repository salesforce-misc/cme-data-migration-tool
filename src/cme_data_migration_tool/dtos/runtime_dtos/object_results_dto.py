from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_matching_keys_dto import ObjectMatchingKeyDTO

from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO

class ObjectResultsDTO(BaseDTO):

    @staticmethod
    def getinstance(results_config, object):
        sobject_results = results_config.import_configs.get(object, None)
        results_instance = None
       
        if sobject_results is not None:
            objectconfig = MigrationObjTemplateDTO.getdestinationinstance(object)
            results = []
            matchingkeyinfolist = []
            for sobject_result in sobject_results:
                sobject_result_item = BaseDTO.get_json_data('./results/'+object+'/'+sobject_result)
                results.append(sobject_result_item)
                matchingkeyinfo = sobject_result_item.get("matchingkeyinfo", None)
                if(matchingkeyinfo is None):
                    raise Exception("Invalid Matching Key Info")
                matchingkeyinfofielddetails = matchingkeyinfo.get("matchingkeyqueryfieldswithdata", None)
                if(matchingkeyinfofielddetails is None):
                    raise Exception("Invalid Matching Key Info")
                matchingkeyinfolist.append(matchingkeyinfofielddetails)    
            print('pre validation')
            matchingkeyresults = ObjectMatchingKeyDTO(OrgConfigDTO.getdestinationorg(), objectconfig, matchingkeyinfolist)
            print('validation')
            results_instance = ObjectResultsDTO(objectconfig, matchingkeyresults, results)
        return results_instance

    def __init__(self, objectconfig, matchingkeyresults, results):
        self.objectconfig = objectconfig
        self.orgconfig = OrgConfigDTO.getdestinationorg()
        self.object_matching_key_results = matchingkeyresults
        self.existing_records = []
        self.new_records = []
        self.existing_record_count = 0
        self.new_record_count = 0
        self.update_results(results)

    def update_results(self, results):
        for object_info in results:
            fieldresult = object_info['fieldresult']
            matchingkey = object_info['matchingkeyinfo']['matchingkey']
            unmasked_result = {}
            existing = False
            if matchingkey in self.object_matching_key_results.matching_key_results:
                unmasked_result["id"] = self.object_matching_key_results.matching_key_results[matchingkey]
                self.existing_records.append(unmasked_result)
                existing = True
            else:
                self.new_records.append(unmasked_result)
            
            for field,value in fieldresult.items():
                if(field == "id"):
                    continue
                referencefield = self.objectconfig.referencetofieldmapping.get(field, None)
                if(referencefield != None):
                    field = referencefield
                if existing and (field not in self.objectconfig.readonlyfields) and (field not in self.objectconfig.createablefields):
                    unmasked_result[nsf.unmask(self.orgconfig, field)] = value
                elif (not existing) and (field not in self.objectconfig.readonlyfields):
                    unmasked_result[nsf.unmask(self.orgconfig, field)] = value
        
        self.existing_record_count = len(self.existing_records)
        self.new_record_count = len(self.new_records)

    def get_results(self):
        results = []
        results.extend(self.existing_records)
        results.extend(self.new_records)
        return results