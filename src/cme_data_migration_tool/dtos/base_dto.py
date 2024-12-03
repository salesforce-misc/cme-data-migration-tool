import json
from alive_progress import alive_bar
from src.cme_data_migration_tool.utils.nsf import nsf
from pathlib import Path

class BaseDTO:

    def to_dict(self):
        return self.__dict__


    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

    @classmethod
    def from_json(cls, json_config):
        config_path = './src/cme_data_migration_tool/configurations/'+json_config+'.json'
        data = BaseDTO.get_json_data(config_path)
        return cls(**data)
    
    @classmethod
    def from_interface_json(cls, json_config):
        config_path = './configurations/'+json_config+'.json'
        data = BaseDTO.get_json_data(config_path)
        return cls(**data)
    
    @classmethod
    def from_results(cls, orgconfig, objectconfig, resultfilepath, info):
        data = BaseDTO.get_json_data(resultfilepath+'.json')
        if data is None:
            return None
        result = {'orgconfig' : orgconfig, 'objectconfig': objectconfig, 'results' : data}
        result.update(info)
        return cls(**result)
    
    @classmethod
    def from_json_file_path(cls, filepath):
        data = BaseDTO.get_json_data(filepath+'.json')
        if data is None:
            return None
        return cls(**data)
        
    @classmethod
    def get_json_data(cls, config_path):
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None
        except Exception:
            print("Invalid Json Configuration for " + config_path)
            return None