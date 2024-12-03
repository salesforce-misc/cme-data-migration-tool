from alive_progress import alive_bar
from src.cme_data_migration_tool.utils.nsf import nsf
class DMLUtils:

    @classmethod
    def upsert(cls, objectstoupsertresult):
        objname = objectstoupsertresult.objectconfig.objectname
        print(objname)
        records_to_upsert = objectstoupsertresult.existing_records.copy()
        records_to_upsert.extend(objectstoupsertresult.new_records)
        result = objectstoupsertresult.orgconfig.org_connector.bulk.__getattr__(objname).upsert(records_to_upsert,'id',batch_size=1000,use_serial=True)
        print(result)
        return None
    
    @classmethod
    def delete(cls, objectstodeleteresult):
        objname = objectstodeleteresult.objectconfig.objectname
        result = objectstodeleteresult.orgconfig.org_connector.bulk.__getattr__(objname).delete(objectstodeleteresult.existing_records,'id',batch_size=1000,use_serial=True)
        return result
    
