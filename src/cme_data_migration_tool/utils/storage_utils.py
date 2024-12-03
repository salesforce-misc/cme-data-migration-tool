from alive_progress import alive_bar

class QueryUtils:
    
    @classmethod
    def query_by_id(cls, objconfig, objectids, orgconfig, queryrecordprocessor):
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in objectids)
        countquery = "SELECT count() FROM {} where id in ({})".format(objconfig.objectname.replace('$namespace$', orgconfig.namespace), objectidsstring)
        dataquery = "SELECT "+ objconfig.get_fields_to_query(orgconfig) +" FROM {} where id in ({})".format(objconfig.objectname.replace('$namespace$', orgconfig.namespace), objectidsstring)
        return QueryUtils.query(objconfig, orgconfig, countquery, dataquery, queryrecordprocessor)
    
    @classmethod
    def query_by_field(cls, objconfig, orgconfig, masked_field_name, field_ids, queryrecordprocessor):
        field_name = masked_field_name.replace('$namespace$', orgconfig.namespace)
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in field_ids)
        countquery = "SELECT count() FROM {} where {} in ({})".format(objconfig.objectname.replace('$namespace$', orgconfig.namespace), field_name, objectidsstring)
        dataquery = "SELECT "+ objconfig.get_fields_to_query(orgconfig) +" FROM {} where {} in ({})".format(objconfig.objectname.replace('$namespace$', orgconfig.namespace), field_name, objectidsstring)
        return QueryUtils.query(objconfig, orgconfig, countquery, dataquery, queryrecordprocessor)

    @classmethod
    def query(cls, objconfig, orgconfig, countquery, dataquery, queryrecordprocessor):
        data = orgconfig.org_connector.query(countquery)
        total_query_result_size = (data["totalSize"])
        query_result_iterator = orgconfig.org_connector.query_all_iter(dataquery)
        results = {}
        with alive_bar(total_query_result_size, bar = 'classic', title="querying "+objconfig.objectname.replace('$namespace$', orgconfig.namespace)) as bar:
            for query_record in query_result_iterator:
                processedqueryrecord = queryrecordprocessor(query_record, orgconfig, False)
                processedqueryrecordid = processedqueryrecord["fieldresult"]["id"]
                results[processedqueryrecordid] = processedqueryrecord
                bar()
        return results