import json,os,uuid,shutil
from pathlib import Path
from alive_progress import alive_bar
from collections import OrderedDict
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO

class BaseService:
    @classmethod
    def filter_sobject_fields(cls, pair):
        unwanted_keys = {'attributes'}
        key, value = pair
        if key in unwanted_keys:
            return False  # filter pair out of the dictionary
        else:
            return True  # keep pair in the filtered dictionary

    @classmethod
    def processqueryrecord(cls, objectname, record, orgconfig, referencefield):
        fieldresult = {}
        referenceresult = {}
        recordresult = {
            "fieldresult" : fieldresult
        }
        
        if objectname not in GlobalResultsDTO.globalobjectmatchingkeyinfomap.keys():
            GlobalResultsDTO.globalobjectmatchingkeyinfomap[objectname] = {}
        matchingkeyinfomap = GlobalResultsDTO.globalobjectmatchingkeyinfomap[objectname]

        if not referencefield:
            recordresult["referenceresult"] = referenceresult
        record_dict = dict(filter(BaseService.filter_sobject_fields, record.items()))
        
        for recordfieldname,recordfielddata in record_dict.items():
            key = nsf.mask(orgconfig, recordfieldname)
            value = recordfielddata
            if isinstance(recordfielddata, OrderedDict):
                maskedrefobject = nsf.mask(orgconfig, recordfielddata.get("attributes").get("type"))
                referenceresult[key] = BaseService.processqueryrecord(maskedrefobject, recordfielddata, orgconfig, True)
            else:
                fieldresult[key] = value

        matchingkeydetails = QueryUtils.generatematchingkeyinfo(objectname, fieldresult)
        matchingkeyinfomap[matchingkeydetails['matchingkey']] = matchingkeydetails['matchingkeyqueryfieldswithdata']
        recordresult["matchingkeyinfo"] = matchingkeydetails
        return recordresult
    
    def savefile(self, fpath, result, resultname):
        # with alive_bar(1, bar = 'classic', title="saving results of "+resultname) as bar:
        if self.test is False:
            if os.path.isfile(fpath) :
                os.remove(fpath)
            with open(fpath, 'w') as f:
                json.dump(result, f)
        elif self.printtest is True:
            print("Testing mode, files will not be saved")
            print(json.dumps(result))
            # bar()
