from src.cme_data_migration_tool.dtos.base_dto import BaseDTO

class MatchingKeysDTO(BaseDTO):
    instance = None
    @staticmethod
    def getinstance():
        if MatchingKeysDTO.instance is None:
            MatchingKeysDTO.instance = MatchingKeysDTO.from_json('object_matchingkey_configurations/matchingkeys')
        return MatchingKeysDTO.instance

    def __init__(self, **kwargs):
        self.matching_keys = {}
        for object_name in kwargs:
            org_object_key = kwargs.get(object_name)
            sorted_matching_keys = list(org_object_key.split(','))
            sorted_matching_keys.sort()
            self.matching_keys[object_name] = sorted_matching_keys
