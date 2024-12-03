from collections import OrderedDict

class GlobalResultsDTO():
    globalids = set()
    globalobjectmap = {}
    globalobjectidsmap = {}
    globalobjectmatchingkeyinfomap = {}
    object_import_sequence = []
    file_import_sequence = {}
    existing_record_count = {}
    new_record_count = {}
    globalobjectimportfileinfomap = {}
    
    @staticmethod
    def get_import_sequence():
        return {'object_import_sequence' : GlobalResultsDTO.file_import_sequence, 'file_import_sequence' : GlobalResultsDTO.file_import_sequence}
        
        