from src.cme_data_migration_tool.dtos.base_dto import BaseDTO

class MigrationConfigItemDTO(BaseDTO):

    def __init__(self, **kwargs):
        self.object = kwargs.get("object")
        self.object_selection_filter = kwargs.get("object_selection_filter")

    def validate(self):
        if not (self.object == "product2" or self.object == "$namespace$__promotion__c"):
            raise Exception("Currently Product2 or Promotion migration only is supported") 