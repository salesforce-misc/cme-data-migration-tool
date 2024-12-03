from alive_progress import alive_bar
import json
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.simple_salesforce_dmt.format import format_soql
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
class QueryUtils:
    
    @classmethod
    def query_by_id(cls, objconfig, objectids, orgconfig, queryrecordprocessor):
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in objectids)
        countquery = "SELECT count() FROM {} where id in ({})".format(nsf.unmask(orgconfig, objconfig.objectname), objectidsstring)
        dataquery = "SELECT "+ objconfig.get_fields_to_query(orgconfig) +" FROM {} where id in ({})".format(nsf.unmask(orgconfig, objconfig.objectname), objectidsstring)
        return QueryUtils.query(objconfig, orgconfig, countquery, dataquery, queryrecordprocessor)
    
    @classmethod
    def query_by_field(cls, objconfig, orgconfig, masked_field_name, field_ids, queryrecordprocessor):
        field_name = nsf.unmask(orgconfig, masked_field_name)
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in field_ids)
        countquery = "SELECT count() FROM {} where {} in ({})".format(nsf.unmask(orgconfig, objconfig.objectname), field_name, objectidsstring)
        dataquery = "SELECT "+ objconfig.get_fields_to_query(orgconfig) +" FROM {} where {} in ({})".format(nsf.unmask(orgconfig, objconfig.objectname), field_name, objectidsstring)
        return QueryUtils.query(objconfig, orgconfig, countquery, dataquery, queryrecordprocessor)

    @classmethod
    def query_by_matching_keys(cls, objconfig, orgconfig, matchingkeyrecords, queryrecordprocessor):
        for i in range(0, len(matchingkeyrecords), 500):
            matchingkeys_to_query_chunk = matchingkeyrecords[i:i + 500]
            all_matching_key_conditions = []
            for matchingkeydetails in matchingkeys_to_query_chunk:
                matching_key_conditions = []
                for masked_field_name,value in matchingkeydetails.items():
                    field_name = nsf.unmask(orgconfig, masked_field_name)
                    matching_key_conditions.append("{} = {}".format(field_name, "'" + value + "'"))
                all_matching_key_conditions.append( "(" + ( " ) AND ( ".join(matching_key_conditions) ) + ")" )
            final_matching_key_condition = "(" + (" ) OR ( ".join(all_matching_key_conditions))  + ")"
            countquery = "SELECT count() FROM {} where {}".format(nsf.unmask(orgconfig, objconfig.objectname), final_matching_key_condition)
            dataquery = "SELECT "+ objconfig.getmatchingfieldsstring(orgconfig) +" FROM {} where {}".format(nsf.unmask(orgconfig, objconfig.objectname), final_matching_key_condition)
            return QueryUtils.query(objconfig, orgconfig, countquery, dataquery, queryrecordprocessor)
    
    @classmethod
    def query(cls, objconfig, orgconfig, countquery, dataquery, queryrecordprocessor):
        data = orgconfig.org_connector.query(countquery)
        total_query_result_size = (data["totalSize"])
        query_result_iterator = orgconfig.org_connector.query_all_iter(dataquery)
        results = {}
        with alive_bar(total_query_result_size, bar = 'classic', title="querying "+nsf.unmask(orgconfig, objconfig.objectname)) as bar:
            for query_record in query_result_iterator:
                processedqueryrecord = queryrecordprocessor(objconfig.objectname, query_record, orgconfig, False)
                if processedqueryrecord is not None:
                    processedqueryrecordid = processedqueryrecord["fieldresult"]["id"]
                    results[processedqueryrecordid] = processedqueryrecord
                bar()
        return results
    
    @classmethod
    def generatematchingkeyinfo(cls, objectname, datafields):
        objectmatchingkeysmap = MatchingKeysDTO.getinstance()
        matchingkeyfields = objectmatchingkeysmap.matching_keys[objectname]
        matchingkey = ''
        matchingkeyqueryfieldswithdata = {}
        for matchingkeyfield in matchingkeyfields:
            if matchingkeyfield in datafields.keys():
                if matchingkeyfield not in datafields.keys() or datafields[matchingkeyfield] == None:
                    print('matching key missing for object  {} and matching key is {} with complete data fields as {}'.format(objectname, matchingkeyfield, json.dumps(datafields)))
                matchingkey = datafields[matchingkeyfield] if matchingkey == '' else matchingkey + '-' + datafields[matchingkeyfield]
                matchingkeyqueryfieldswithdata[matchingkeyfield] = datafields[matchingkeyfield]
            else:
                raise KeyError("Matching keys not found for object = {} with id = {} and relevant matching key field is {}".format(objectname, datafields["id"], matchingkeyfield))
        matchingkeymap = {
            'matchingkey' : matchingkey,
            'matchingkeyqueryfieldswithdata' : matchingkeyqueryfieldswithdata,
            'object' : objectname
        }
        return matchingkeymap
    
