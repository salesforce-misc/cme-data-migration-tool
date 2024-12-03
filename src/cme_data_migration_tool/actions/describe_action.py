import requests,json,os
from src.cme_data_migration_tool.actions.base_action import BaseAction
from src.cme_data_migration_tool.dtos.configurations_dtos.migration_obj_template_dto import MigrationObjTemplateDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.matching_keys_dto import MatchingKeysDTO
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.utils.query_utils import QueryUtils
from src.cme_data_migration_tool.utils.nsf import nsf

session = requests.Session()
standard_fields_to_exclude = {"createddate", "lastmodifieddate", "createdbyid", "lastmodifiedbyid", "ownerid", "usagemodeltype"}

class DescribeAction(BaseAction):

    def __init__(self, args):
        self.source_auth_headers, self.source_session, self.source_url = self.get_auth_headers(OrgConfigDTO.getsourceorg())
        self.destination_auth_headers, self.destination_session, self.destination_url = self.get_auth_headers(OrgConfigDTO.getdestinationorg())
    
    def get_auth_headers(self, orgconfig):
        payload = {
          "grant_type": "password",
          "client_id": orgconfig.consumer_key,
          "client_secret": orgconfig.consumer_secret,
          "username": orgconfig.username,
          "password": orgconfig.password
        }

        login_endpoint = orgconfig.instance_url+"/services/oauth2/token"
        headers = { "Content-Type": "application/x-www-form-urlencoded" }
        response = session.post(login_endpoint, headers=headers, data=payload)
        access_token = json.loads(response.text).get("access_token")
        instance_url = json.loads(response.text).get("instance_url")

        headers = {
          "Content-Type": "application/json; charset=UTF-8",
          "Accept": "application/json",
          "Authorization": "Bearer "+ access_token
        }
        return headers, session, instance_url
    
    def populateDescribeForObjects(self, org_type, objectname, describedObjects, auth_headers, session, instance_url, namespace):
      if objectname in describedObjects: 
        return

      fmatchkeys = MatchingKeysDTO.getinstance().matching_keys
      mainobjectsToDescribe = fmatchkeys.keys()

      url = instance_url + "/services/data/v62.0/sobjects/"+objectname+"/describe/"
      print("describing " + objectname)
      response = session.get(url, headers=auth_headers)
      data = response.json()
      dont_process_further = False
      if isinstance(data, list):
        for data_node in data:
          print(data_node)
          if "errorCode" in data_node.keys() and data_node["errorCode"] == "NOT_FOUND":
            dont_process_further = True
      if dont_process_further:
        return
      
      childs = []
      for childRelationship in data['childRelationships']:
        csobject = childRelationship['childSObject'].lower()
        csobjectfield = childRelationship['field']
        childreferencefieldobject = csobject.lower().replace(namespace, "$namespace$")
        childMap = {
          'childsobject' : childreferencefieldobject,
          'field' : csobjectfield.lower().replace(namespace, "$namespace$")
        }
        if childreferencefieldobject in mainobjectsToDescribe and csobject != objectname:
          childs.append(childMap)
      
      relatedParentFields = []
      for field in data["fields"]:
        for parentReferenceField in field['referenceTo']:
          nsRemovedParentReference = parentReferenceField.lower().replace(namespace, "$namespace$")
          if nsRemovedParentReference in mainobjectsToDescribe and csobject != objectname: 
            relatedParentFields.append(nsRemovedParentReference)

      fields = []
      createablefields = []
      readonlyfields = []
      maskedobjname = objectname.replace(namespace, "$namespace$")
      referencefields = []
      referencetofieldmapping = {}
      for fieldMetadata in data['fields']:
        fname = fieldMetadata["name"].lower().replace(namespace, "$namespace$")
        if fname not in standard_fields_to_exclude:      
          ftype = fieldMetadata["type"]
          creatable = fieldMetadata["createable"]
          updateable = fieldMetadata["updateable"]
          if(ftype == "reference"):
            referenceTo = fieldMetadata["referenceTo"]
            referencefieldobject = referenceTo[0].lower().replace(namespace, "$namespace$")
            fieldMap = {
              'field' : fname,
              'fieldobject' : referencefieldobject,
              'standard' : (not fname.endswith("__c")),
              'export' : False
            }
            referencetofieldmapping[nsf.robject(fname)] = fname
            if referencefieldobject in mainobjectsToDescribe:
              referencefields.append(fieldMap)
          elif(creatable and updateable):
            fields.append(fname)
          elif(creatable):
            createablefields.append(fname)
          else:
            readonlyfields.append(fname)
          # if fname in fmatchkeys[maskedobjname] and fname not in fields:
          #   print(True)
            
        mobjectname = objectname.replace(namespace, "$namespace$")
        result = {
          "objectname" : mobjectname,
          "datafieldstomigrate" : fields,
          "readonlyfields" : readonlyfields,
          "createablefields" : createablefields,
          "referencefields" : referencefields,
          "referencetofieldmapping" : referencetofieldmapping,
          "childobjectstomigrate" : childs
        }
      filePath  = './src/cme_data_migration_tool/configurations/'+ org_type +'/'+ mobjectname +'.json'
      if(os.path.isfile(filePath)):
        os.remove(filePath)

      with open(filePath, 'w+') as f:
        json.dump(result, f, indent=4)
      
      describedObjects.add(objectname)
      for child in childs:
        nsAddedChild = child['childsobject'].replace("$namespace$", namespace)
        self.populateDescribeForObjects(org_type, nsAddedChild, describedObjects, auth_headers, session, instance_url, namespace)
      
      for parentField in relatedParentFields:
        self.populateDescribeForObjects(org_type, parentField.replace("$namespace$", namespace), describedObjects, auth_headers, session, instance_url, namespace)


    def execute_action(self):
        describedObjects = set()
        self.populateDescribeForObjects('object_configurations', "product2", describedObjects, self.source_auth_headers, self.source_session, self.source_url, OrgConfigDTO.getsourceorg().namespace)