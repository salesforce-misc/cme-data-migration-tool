from src.cme_data_migration_tool.dtos.base_dto import BaseDTO

class MigrationObjChildRefDTO(BaseDTO):

    def __init__(self, **kwargs):
        self.childsobject = kwargs.get("childsobject")
        self.field = kwargs.get("field")