import json,os,uuid,shutil
from pathlib import Path
from alive_progress import alive_bar
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.services.base_service import BaseService
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.utils.nsf import nsf

class ExportService(BaseService):

    def __init__(self, saveresult, result_name, objectnametoquery, fieldnametoquery, idstoquery):
        MatchingKeysDTO.getinstance()
        self.object_result_filename = uuid.uuid4().hex
        self.objectnametoquery = objectnametoquery
        self.import_sequence = []
        self.test = False
        self.printtest= False
        self.export_records = []
        self.result_name = result_name
        self.saveresult = saveresult
        self.orgconfig = OrgConfigDTO.getsourceorg()
        self.exportobjectconfig = MigrationObjTemplateDTO.getsourceinstance(objectnametoquery)
        self.object_results = QueryUtils.query_by_field(self.exportobjectconfig, self.orgconfig, fieldnametoquery, idstoquery, BaseService.processqueryrecord)
        if self.exportobjectconfig.objectname not in GlobalResultsDTO.file_import_sequence:
            GlobalResultsDTO.file_import_sequence[self.exportobjectconfig.objectname] = []
        
        for key in GlobalResultsDTO.globalids:
            if key in self.object_results:
                self.object_results.pop(key)
        
        if self.exportobjectconfig.objectname not in GlobalResultsDTO.globalobjectmap.keys():
            GlobalResultsDTO.globalobjectmap[self.exportobjectconfig.objectname] = 0
        GlobalResultsDTO.globalobjectmap[self.exportobjectconfig.objectname] = GlobalResultsDTO.globalobjectmap[self.exportobjectconfig.objectname] + len(self.object_results)

        self.results_path = Path('results')
        self.results_root_path = self.results_path / self.result_name
        self.import_sequence_path = self.results_root_path / 'import_sequence.json'
        self.matching_key_results_directory_path = self.results_root_path / 'zmatchingkeys/'
        self.results_directory_path = self.results_root_path / self.exportobjectconfig.objectname
        self.results_directory_path =  self.results_path / self.result_name
        self.object_result_filepath = self.results_directory_path / str(self.object_result_filename + '.json')
        self.base_object_result_filepath = self.results_directory_path / nsf.cleanup(objectnametoquery)
        self.base_object_name = nsf.cleanup(objectnametoquery)
        self.create_directory()

    def export(self):
        references_to_export = {}
        objectids_to_export = []
        
        for object_result_key in self.object_results:
            object_result = self.object_results.get(object_result_key)
            object_result_id = object_result["fieldresult"]["id"]
            if(object_result_id in GlobalResultsDTO.globalids):
                continue
            GlobalResultsDTO.globalids.add(object_result_id)
            objectids_to_export.append(object_result_id)

        GlobalResultsDTO.file_import_sequence[self.exportobjectconfig.objectname].append(self.object_result_filename)
        GlobalResultsDTO.object_import_sequence.append(self.exportobjectconfig.objectname)        

        self.import_sequence.append(self.object_result_filename)
        
        self.save_results()
        return self.import_sequence
    
    def export_by_chunks(self, object, field, objectids_to_export):
        final_objectids_to_export = list(set(objectids_to_export) - GlobalResultsDTO.globalids) if field == "id" else objectids_to_export
        for i in range(0, len(final_objectids_to_export), 500):
            objectids_to_export_chunk = objectids_to_export[i:i + 500]
            exportservice = ExportService(False, self.result_name, object, field, objectids_to_export_chunk)
            object_import_sequence = exportservice.export()
            self.import_sequence.extend(object_import_sequence)

    def save_results(self):
        print("saving results of " + self.base_object_name)
        for key in self.object_results:
            matchingkey = self.object_results[key]["matchingkeyinfo"]["matchingkey"]
            filepathtosave = self.base_object_result_filepath.with_name(self.base_object_result_filepath.stem + "_" + matchingkey + ".json")
            self.savefile(filepathtosave, self.object_results[key], self.exportobjectconfig.objectname)
            if self.objectnametoquery not in GlobalResultsDTO.globalobjectimportfileinfomap.keys():
                GlobalResultsDTO.globalobjectimportfileinfomap[self.objectnametoquery] = []
            GlobalResultsDTO.globalobjectimportfileinfomap[self.objectnametoquery].append(self.base_object_name+"_"+matchingkey+'.json')

    def save_sequence(self, name):
        self.savefile(self.results_path + name + '.json', GlobalResultsDTO.globalobjectmatchingkeyinfomap, 'import configurations')
    

    def create_directory(self): 
        # if(os.path.isdir(self.results_root_path) is True and self.saveresult is True):
        #     shutil.rmtree(self.results_root_path)
        if os.path.exists(self.results_root_path) is not True and self.test is False:
            os.makedirs(self.results_root_path)
        if os.path.exists(self.results_directory_path) is not True and self.test is False:
            os.makedirs(self.results_directory_path)
        # if os.path.isdir(self.matching_key_results_directory_path) is not True and self.test is False:
        #     os.mkdir(self.matching_key_results_directory_path)