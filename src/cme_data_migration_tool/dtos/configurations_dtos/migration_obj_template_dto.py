from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_reference_fields_dto import MigrationObjReferenceFieldDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_child_ref_dto import MigrationObjChildRefDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.utils.nsf import nsf

class MigrationObjTemplateDTO(BaseDTO):
   
    @staticmethod
    def getsourceinstance(objectname):
        return MigrationObjTemplateDTO.from_json('object_configurations/'+objectname)
    
    @staticmethod
    def getdestinationinstance(objectname):
        return MigrationObjTemplateDTO.from_json('object_configurations/'+objectname)
    
    def __init__(self, **kwargs):
        self.referencefields = []
        self.childobjectstomigrate = []
        self.objectname = kwargs.get("objectname")
        self.datafieldstomigrate = kwargs.get("datafieldstomigrate")
        self.readonlyfields = kwargs.get("readonlyfields")
        self.createablefields = kwargs.get("createablefields")
        self.referencefieldtoobject = {}
        self.referencetofieldmapping = kwargs.get("referencetofieldmapping")
        self.referencefieldtoexportability = {}
        config_referencefields = kwargs.get("referencefields")
        
        for config_referencefield in config_referencefields:
            referenceitemdto = MigrationObjReferenceFieldDTO.from_dict(config_referencefield)
            self.referencefields.append(referenceitemdto)
            self.referencefieldtoobject[referenceitemdto.field_ref_obj] = referenceitemdto.fieldobject
            self.referencefieldtoexportability[referenceitemdto.field_ref_obj] = referenceitemdto.export

        config_childreferences = kwargs.get("childobjectstomigrate")
        for config_childreference in config_childreferences:
            self.childobjectstomigrate.append( MigrationObjChildRefDTO.from_dict(config_childreference))

    def get_fields_to_query(self, orgconfig):
        masked_fields_to_query = self.datafieldstomigrate.copy()
        masked_fields_to_query.extend(self.readonlyfields.copy())
        masked_fields_to_query.extend(self.createablefields.copy())

        for referencefield in self.referencefields :
            masked_fields_to_query.extend(referencefield.referencekeyslist)
        fields_to_query = ",".join(field for field in masked_fields_to_query)
        fields_to_query = nsf.unmask(orgconfig,fields_to_query)
        return fields_to_query
    
    def get_reference_fields_to_query(self, orgconfig):
        masked_fields_to_query = []
        masked_fields_to_query.append('id')
        for referencefield in self.referencefields :
            masked_fields_to_query.extend(referencefield.referencekeyslist)
        fields_to_query = ",".join(field for field in masked_fields_to_query)
        return fields_to_query
    
    def getmatchingfieldsstring(self, orgconfig):
        matchingkeyfields = MatchingKeysDTO.getinstance().matching_keys[self.objectname].copy()
        matchingkeyfields.append('id')
        queryfields = ",".join(matchingkeyfields)
        return nsf.unmask(orgconfig, queryfields)