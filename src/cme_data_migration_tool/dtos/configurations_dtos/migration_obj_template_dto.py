from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_reference_fields_dto import MigrationObjReferenceFieldDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_child_ref_dto import MigrationObjChildRefDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.utils.nsf import nsf

class MigrationObjTemplateDTO(BaseDTO):

    _describe_field_cache = {}
    _instance_cache = {}

    @staticmethod
    def getsourceinstance(objectname):
        if objectname not in MigrationObjTemplateDTO._instance_cache:
            MigrationObjTemplateDTO._instance_cache[objectname] = MigrationObjTemplateDTO.from_json('object_configurations/'+objectname)
        return MigrationObjTemplateDTO._instance_cache[objectname]

    @staticmethod
    def getdestinationinstance(objectname):
        return MigrationObjTemplateDTO.getsourceinstance(objectname)
    
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
        self.rawfieldtoobject = {}
        self.polymorphicfieldtotypefield = {}
        config_referencefields = kwargs.get("referencefields")

        for config_referencefield in config_referencefields:
            referenceitemdto = MigrationObjReferenceFieldDTO.from_dict(config_referencefield)
            self.referencefields.append(referenceitemdto)
            self.referencefieldtoobject[referenceitemdto.field_ref_obj] = referenceitemdto.fieldobject
            self.referencefieldtoexportability[referenceitemdto.field_ref_obj] = referenceitemdto.export
            self.rawfieldtoobject[referenceitemdto.field] = referenceitemdto.fieldobject

        for config_polymorphicfield in kwargs.get("polymorphicreferencefields", []):
            self.polymorphicfieldtotypefield[config_polymorphicfield["field"]] = config_polymorphicfield["typefield"]

        config_childreferences = kwargs.get("childobjectstomigrate")
        for config_childreference in config_childreferences:
            self.childobjectstomigrate.append( MigrationObjChildRefDTO.from_dict(config_childreference))

    def get_real_org_fields(self, orgconfig):
        unmasked_objectname = nsf.unmask(orgconfig, self.objectname)
        if unmasked_objectname not in MigrationObjTemplateDTO._describe_field_cache:
            describe_result = getattr(orgconfig.org_connector, unmasked_objectname).describe()
            MigrationObjTemplateDTO._describe_field_cache[unmasked_objectname] = {
                field['name'].lower() for field in describe_result['fields']
            }
        return MigrationObjTemplateDTO._describe_field_cache[unmasked_objectname]

    def get_fields_to_query(self, orgconfig):
        masked_fields_to_query = self.datafieldstomigrate.copy()
        masked_fields_to_query.extend(self.readonlyfields.copy())
        masked_fields_to_query.extend(self.createablefields.copy())

        for referencefield in self.referencefields :
            masked_fields_to_query.extend(referencefield.referencekeyslist)

        real_org_fields = self.get_real_org_fields(orgconfig)
        # dotted relationship paths (e.g. "field__r.name") belong to a different
        # object's describe, so only top-level fields are checked against real_org_fields
        dropped_fields = [field for field in masked_fields_to_query
                           if '.' not in field and nsf.unmask(orgconfig, field) not in real_org_fields]
        if dropped_fields:
            print('dropping fields not found in org for {}: {}'.format(self.objectname, dropped_fields))
        masked_fields_to_query = [field for field in masked_fields_to_query if field not in dropped_fields]

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