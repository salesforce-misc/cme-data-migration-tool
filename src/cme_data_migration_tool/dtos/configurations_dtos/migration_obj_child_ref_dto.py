from src.cme_data_migration_tool.dtos.base_dto import BaseDTO


class MigrationObjChildRefDTO(BaseDTO):

    def __init__(self, **kwargs):
        self.childsobject = kwargs.get("childsobject")
        self.field = kwargs.get("field")
        self.type = kwargs.get("type")
        self.whereClause = kwargs.get("whereClause")
        self.collectedFields = kwargs.get("collectedFields")
        self.recursiveField = kwargs.get("recursiveField")
        self.polymorphicField = kwargs.get("polymorphicField")
