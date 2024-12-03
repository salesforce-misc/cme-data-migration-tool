from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.utils.nsf import nsf
class MigrationObjReferenceFieldDTO(BaseDTO):

    def __init__(self, **kwargs):
        matchingkeys = MatchingKeysDTO.getinstance()
        self.field = kwargs.get("field")
        self.fieldobject = kwargs.get("fieldobject")
        self.standard = kwargs.get("standard")
        self.export = kwargs.get("export", False)
        self.field_ref_obj = nsf.robject(self.field)
        self.refmatchingkeys = matchingkeys.matching_keys[self.fieldobject].copy()
        self.referencekeyslist = list(map(lambda field: (self.field_ref_obj + "." + field) , self.refmatchingkeys))
        self.referencekeyslist.append(self.field_ref_obj + ".id")
