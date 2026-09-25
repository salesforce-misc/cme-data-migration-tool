from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.object_matching_keys_dto import ObjectMatchingKeyDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO

from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO

class ObjectResultsDTO(BaseDTO):

    @staticmethod
    def get_reference_target_and_key(objectconfig, field, value):
        if field in objectconfig.polymorphicfieldtotypefield and isinstance(value, str) and '::' in value:
            referencedobject, matchingkeyvalue = value.split('::', 1)
            return referencedobject, matchingkeyvalue
        return objectconfig.rawfieldtoobject.get(field), value

    @staticmethod
    def resolve_reference_values(objectconfig, fielddict):
        resolved = {}
        for field, value in fielddict.items():
            referencedobject, matchingkeyvalue = ObjectResultsDTO.get_reference_target_and_key(objectconfig, field, value)
            if referencedobject is None:
                resolved[field] = value
                continue
            if value is None:
                continue
            resolved_id = GlobalResultsDTO.destination_id_by_matching_key.get(referencedobject, {}).get(matchingkeyvalue)
            if resolved_id is None:
                continue
            resolved[field] = resolved_id
        return resolved

    @staticmethod
    def build_resolved_matching_key(objectconfig, resolved_fielddict):
        matchingkeyfields = MatchingKeysDTO.getinstance().matching_keys[objectconfig.objectname]
        matchingkeyparts = [resolved_fielddict[field] for field in matchingkeyfields
                             if resolved_fielddict.get(field) is not None]
        return '-'.join(matchingkeyparts)

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
                resolved_matchingkeyinfofielddetails = ObjectResultsDTO.resolve_reference_values(objectconfig, matchingkeyinfofielddetails)
                sobject_result_item['resolved_matchingkey'] = ObjectResultsDTO.build_resolved_matching_key(objectconfig, resolved_matchingkeyinfofielddetails)
                if resolved_matchingkeyinfofielddetails:
                    matchingkeyinfolist.append(resolved_matchingkeyinfofielddetails)
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
        self.existing_record_matchingkeys = []
        self.new_record_matchingkeys = []
        self.existing_record_count = 0
        self.new_record_count = 0
        self.update_results(results)

    def update_results(self, results):
        real_org_fields = self.objectconfig.get_real_org_fields(self.orgconfig)
        dropped_fields = set()
        for object_info in results:
            fieldresult = object_info['fieldresult']
            matchingkey = object_info.get('resolved_matchingkey') or object_info['matchingkeyinfo']['matchingkey']
            unmasked_result = {}
            existing = False
            if matchingkey in self.object_matching_key_results.matching_key_results:
                destination_id = self.object_matching_key_results.matching_key_results[matchingkey]
                unmasked_result["id"] = destination_id
                self.existing_records.append(unmasked_result)
                self.existing_record_matchingkeys.append(matchingkey)
                existing = True
                GlobalResultsDTO.destination_id_by_matching_key.setdefault(self.objectconfig.objectname, {})[matchingkey] = destination_id
            else:
                self.new_records.append(unmasked_result)
                self.new_record_matchingkeys.append(matchingkey)

            for field,value in fieldresult.items():
                if(field == "id"):
                    continue
                unmasked_field = nsf.unmask(self.orgconfig, field)
                if '.' not in unmasked_field and unmasked_field not in real_org_fields:
                    dropped_fields.add(field)
                    continue
                referencedobject, matchingkeyvalue = ObjectResultsDTO.get_reference_target_and_key(self.objectconfig, field, value)
                if referencedobject is not None:
                    if value is None:
                        continue
                    resolved_id = GlobalResultsDTO.destination_id_by_matching_key.get(referencedobject, {}).get(matchingkeyvalue)
                    if resolved_id is None:
                        print('unable to resolve reference field {} on {} - matching key "{}" not found in destination org (referenced object may not have been imported yet)'.format(field, self.objectconfig.objectname, matchingkeyvalue))
                        continue
                    value = resolved_id
                if existing and (field not in self.objectconfig.readonlyfields) and (field not in self.objectconfig.createablefields):
                    unmasked_result[unmasked_field] = value
                elif (not existing) and (field not in self.objectconfig.readonlyfields):
                    unmasked_result[unmasked_field] = value

        if dropped_fields:
            print('dropping fields not found in destination org for {}: {}'.format(self.objectconfig.objectname, sorted(dropped_fields)))

        self.existing_record_count = len(self.existing_records)
        self.new_record_count = len(self.new_records)

    def get_results(self):
        results = []
        results.extend(self.existing_records)
        results.extend(self.new_records)
        return results