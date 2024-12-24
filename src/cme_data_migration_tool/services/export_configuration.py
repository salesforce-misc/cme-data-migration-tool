import json
import os
from pathlib import Path
from typing import List
from alive_progress import alive_bar
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.services.base_service import BaseService
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from src.cme_data_migration_tool.utils.nsf import nsf


class ExportConfiguration(BaseService):

    def __init__(self, objectNameToQuery: str, idsToQuery: List[str]):
        MatchingKeysDTO.getinstance()
        self.objectIds = idsToQuery
        self.objectType = objectNameToQuery
        self.objectNameToQuery = objectNameToQuery
        self.orgConfig = OrgConfigDTO.getsourceorg()
        self.exportObjectConfig = MigrationObjTemplateDTO.getsourceinstance(
            objectNameToQuery)
        self.collected_objectIds = {self.removeNamespace(
            objectNameToQuery): set(idsToQuery)}
        self.collected_objects = dict()
        self.results_path = Path('results')

    def export(self):
        self.fetchIdsOfChildObjects()
        self.fetchIdsOfRelatedObjects()
        self.fetchRecordsOfExtractedId()
        self.saveResultsToJsonFile()

    def saveResultsToJsonFile(self):
        currFileNames = dict()
        for objectName, data in self.collected_objects.items():
            maskedObject = nsf.mask(self.orgConfig, objectName)
            objectTypeResult = self.results_path / maskedObject
            self.create_directory(objectTypeResult)
            currFileNames.setdefault(maskedObject, list())
            GlobalResultsDTO.globalobjectmap[objectName] = len(data)
            for _, row in data.items():
                fileName = row['matchingkeyinfo']['matchingkey'] + ".json"
                currFileNames[maskedObject].append(fileName)
                self.saveFile(self.results_path / maskedObject /
                              fileName, row, fileName)

        allFileNames = self.readJson('results/epc_import_args.json')
        mergedFileNames = self.merge_dicts(allFileNames, currFileNames)
        self.saveFile(self.results_path / "epc_import_args.json",
                      mergedFileNames, "File Names")

    def fetchRecordsOfExtractedId(self):
        for object, objectSetIds in self.collected_objectIds.items():
            if len(objectSetIds) > 0:
                objectConfig = MigrationObjTemplateDTO.getsourceinstance(
                    nsf.mask(self.orgConfig, object))
                # EPC objects presented by describe will be not null
                if objectConfig:
                    objectListIds = list(objectSetIds)
                    # resultsList = []
                    for i in range(0, len(objectListIds), 200):
                        objectids_to_export_chunk = objectListIds[i:i + 200]
                        results = QueryUtils.query_by_id(
                            objectConfig, objectids_to_export_chunk, self.orgConfig, BaseService.processqueryrecord)
                        # resultsList.append(results)
                        self.collected_objects[object] = results

    def fetchIdsOfChildObjects(self):
        for child_object in self.exportObjectConfig.childobjectstomigrate:
            if child_object.type == 'recursive':
                self.getRecursiveCollectedField(self.objectIds, child_object.childsobject, child_object.whereClause,
                                                child_object.collectedFields, child_object.recursiveField, self.collected_objectIds, self.objectType)
            elif child_object.type == 'polymorphic':
                self.getPolymorphicFields(child_object.childsobject, child_object.whereClause,
                                          child_object.polymorphicField, child_object.collectedFields, self.collected_objectIds)
            elif child_object.type == "more":
                self.getMoreFields(self.objectType, child_object.childsobject,
                                   child_object.whereClause, child_object.collectedFields, self.collected_objectIds)
            else:
                self.getDefaultCollector(
                    self.objectType, child_object.childsobject, child_object.field, self.collected_objectIds)

    def fetchIdsOfRelatedObjects(self):
        nsReplaceObjectType = self.removeNamespace(self.objectType)
        objectIds = self.collected_objectIds[nsReplaceObjectType]
        objectIdsString = ",".join(f"'{objectid}'" for objectid in objectIds)
        fieldsToQuery = ",".join(
            f"{reference_object.field}" for reference_object in self.exportObjectConfig.referencefields)
        queryString = f"SELECT Id, {fieldsToQuery} FROM {
            nsReplaceObjectType} WHERE Id in ({objectIdsString})"
        queryString = self.removeNamespace(queryString)
        fetch_results = self.orgConfig.org_connector.bulk.__getattr__(
            nsReplaceObjectType).query(queryString, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results:
                for reference_object in self.exportObjectConfig.referencefields:
                    nsReplacedField = self.removeNamespace(
                        reference_object.field)
                    nsReplaceObject = self.removeNamespace(
                        reference_object.fieldobject)
                    self.collected_objectIds.setdefault(nsReplaceObject, set())
                    for key, val in result.items():
                        if key.lower() == nsReplacedField.lower() and val != None:
                            self.collected_objectIds[nsReplaceObject].add(
                                val)
                            break

    def removeNamespace(self, stringData: str):
        return stringData.replace("$namespace$", self.orgConfig.namespace)

    def get_case_insensitive_from_dict(self, d, key: str):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.lower() == self.removeNamespace(key.lower()):
                    return v
        return None

    def merge_dicts(self, dict1, dict2):
        merged_dict = {}
        for key in set(dict1.keys()).union(dict2.keys()):
            merged_dict[key] = list(
                set(dict1.get(key, [])) | set(dict2.get(key, [])))
        return merged_dict

    def build_query_string(self, childObject, whereClause, objectIds, collectedFieldsStr):
        objectIdsString = ",".join(f"'{objectid}'" for objectid in objectIds)
        whereClauseNsRemoved = self.removeNamespace(whereClause)
        childObject = self.removeNamespace(childObject)
        queryString = f"SELECT {collectedFieldsStr}, Id FROM {
            childObject} WHERE {whereClauseNsRemoved} IN ({objectIdsString})"
        return self.removeNamespace(queryString), childObject

    def fetch_and_collect_results(self, childObject, queryString, collectedFields, id_collector):
        fetch_results = self.orgConfig.org_connector.bulk.__getattr__(
            childObject).query(queryString, lazy_operation=True)
        id_collector.setdefault(childObject, set())

        for list_results in fetch_results:
            for result in list_results:
                id_collector[childObject].add(result['Id'])

                # Collect and process each field in collectedFields
                for collectingField, relatedFieldPath in collectedFields.items():
                    current_level = result
                    for field in self.removeNamespace(relatedFieldPath).split("."):
                        current_level = self.get_case_insensitive_from_dict(
                            current_level, field)
                        if current_level is None:
                            break

                    if current_level is not None:
                        collectedFieldReplacedNs = self.removeNamespace(
                            collectingField)
                        id_collector.setdefault(
                            collectedFieldReplacedNs, set()).add(current_level)

    def getMoreFields(self, parentSObject, childObject, whereClause, collectedFields, id_collector):
        parentSObjectNsRemoved = self.removeNamespace(parentSObject)
        objectIds = id_collector.get(parentSObjectNsRemoved, [])
        collectedFieldsStr = ",".join(self.removeNamespace(v)
                                      for v in collectedFields.values())
        if len(objectIds) > 0:
            queryString, childObject = self.build_query_string(
                childObject, whereClause, objectIds, collectedFieldsStr)
            self.fetch_and_collect_results(
                childObject, queryString, collectedFields, id_collector)

    def getPolymorphicFields(self, childSObject, whereClause, polymorphicField, collectedFields, id_collector):
        polymorphicFieldNsRemoved = self.removeNamespace(polymorphicField)
        objectIds = id_collector.get(polymorphicFieldNsRemoved, [])
        collectedFieldsStr = ",".join(self.removeNamespace(v)
                                      for v in collectedFields.values())
        if len(objectIds) > 0:
            queryString, childObject = self.build_query_string(
                childSObject, whereClause, objectIds, collectedFieldsStr)
            self.fetch_and_collect_results(
                childObject, queryString, collectedFields, id_collector)

    def getRecursiveCollectedField(self, objectIds, childObject, whereClause, collectedFields, recursiveField, id_collector, parentSObject):
        collectedFieldsStr = ",".join(self.removeNamespace(
            v) for v in collectedFields.values()) + f",{recursiveField}"
        queryString, childObject = self.build_query_string(
            childObject, whereClause, objectIds, collectedFieldsStr)
        fetch_results = []
        if len(objectIds) > 0:
            fetch_results = self.orgConfig.org_connector.bulk.__getattr__(
                childObject).query(queryString, lazy_operation=True)
        id_collector.setdefault(childObject, set())
        recursiveObjectIds = set()

        for list_results in fetch_results:
            for result in list_results:
                id_collector[childObject].add(result['Id'])
                # Check for recursive field
                for k, v in result.items():
                    if v != None:
                        if k.lower() == self.removeNamespace(recursiveField):
                            recursiveObjectIds.add(v)

                # Process collected fields
                for collectingField, relatedFieldPath in collectedFields.items():
                    current_level = result
                    for field in self.removeNamespace(relatedFieldPath).split("."):
                        current_level = self.get_case_insensitive_from_dict(
                            current_level, field)
                        if current_level is None:
                            break

                    if current_level is not None:
                        collectedFieldReplacedNs = self.removeNamespace(
                            collectingField)
                        id_collector.setdefault(
                            collectedFieldReplacedNs, set()).add(current_level)

        # Recursive call
        recursiveObjectIds = list(recursiveObjectIds)
        id_collector.setdefault(
            parentSObject, set()).update(recursiveObjectIds)

        if recursiveObjectIds:
            self.getRecursiveCollectedField(
                recursiveObjectIds, childObject, whereClause, collectedFields, recursiveField, id_collector, parentSObject)

    def getDefaultCollector(self, parentSObject, childSObject, whereClause, id_collector):
        parentSObjectNsRemoved = self.removeNamespace(parentSObject)
        objectIds = id_collector.get(parentSObjectNsRemoved, [])
        if len(objectIds) > 0:
            objectIdsString = ",".join(
                f"'{objectid}'" for objectid in objectIds)
            childObject = self.removeNamespace(childSObject)
            whereClauseNsRemoved = self.removeNamespace(whereClause)
            queryString = f"SELECT Id FROM {childObject} WHERE {
                whereClauseNsRemoved} IN ({objectIdsString})"
            queryString = self.removeNamespace(queryString)
            self.fetch_and_collect_results(
                childObject, queryString, {}, id_collector)

    def saveFile(self, fpath, result, resultName):
        with alive_bar(1, bar='classic', title="saving results of  " + resultName) as bar:
            if os.path.isfile(fpath):
                os.remove(fpath)
            with open(fpath, 'w') as f:
                json.dump(result, f)
            bar()

    def create_directory(self, path_create):
        if os.path.exists(path_create) is not True:
            os.makedirs(path_create)

    def readJson(self, filePath):
        try:
            with open(filePath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Warning: The file at {filePath} contains invalid JSON.")
            return {}
