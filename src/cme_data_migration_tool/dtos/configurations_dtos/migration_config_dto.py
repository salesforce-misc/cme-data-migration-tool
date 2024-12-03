from src.cme_data_migration_tool.dtos.base_dto import BaseDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_configitem_dto import MigrationConfigItemDTO

class MigrationConfigDTO(BaseDTO):

    def __init__(self, **kwargs):
        self.migration_config_items = []
        config_items = kwargs.get("config_items")
        for config_item in config_items:
            self.migration_config_items.append( MigrationConfigItemDTO.from_dict(config_item))