from alive_progress import alive_bar
from src.cme_data_migration_tool.utils.nsf import nsf
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
class DMLUtils:

    @classmethod
    def upsert(cls, objectstoupsertresult):
        maskedobjname = objectstoupsertresult.objectconfig.objectname
        objname = nsf.unmask(objectstoupsertresult.orgconfig, maskedobjname)
        print(objname)
        records_to_upsert = objectstoupsertresult.existing_records.copy()
        records_to_upsert.extend(objectstoupsertresult.new_records)
        matchingkeys_in_order = objectstoupsertresult.existing_record_matchingkeys + objectstoupsertresult.new_record_matchingkeys
        result = objectstoupsertresult.orgconfig.org_connector.bulk.__getattr__(objname).upsert(records_to_upsert,'id',batch_size=1000,use_serial=True)
        print(result)
        for matchingkey, dml_result in zip(matchingkeys_in_order, result):
            if dml_result.get('success') and dml_result.get('id'):
                GlobalResultsDTO.destination_id_by_matching_key.setdefault(maskedobjname, {})[matchingkey] = dml_result['id']
        return None
    
    @classmethod
    def delete(cls, objectstodeleteresult):
        objname = objectstodeleteresult.objectconfig.objectname
        result = objectstodeleteresult.orgconfig.org_connector.bulk.__getattr__(objname).delete(objectstodeleteresult.existing_records,'id',batch_size=1000,use_serial=True)
        return result
    
