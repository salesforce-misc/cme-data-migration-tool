from src.cme_data_migration_tool.dtos.base_dto import BaseDTO

class ImportSequenceDTO(BaseDTO):

    @staticmethod
    def getinstance():
        return ImportSequenceDTO.from_json('import_configurations/import_sequence_configuration')

    def __init__(self, **kwargs):
        self.import_sequence = kwargs['sequence']
        