from src.cme_data_migration_tool.simple_salesforce_dmt.api import Salesforce
from src.cme_data_migration_tool.dtos.base_dto import BaseDTO

class OrgConfigDTO(BaseDTO):
    source_org_instance = None
    destination_org_instance = None

    @staticmethod
    def getsourceorg():
        if OrgConfigDTO.source_org_instance is None:
            OrgConfigDTO.source_org_instance = OrgConfigDTO.from_interface_json('source_org')
        return OrgConfigDTO.source_org_instance
    
    @staticmethod
    def getdestinationorg():
        if OrgConfigDTO.destination_org_instance is None:
            OrgConfigDTO.destination_org_instance = OrgConfigDTO.from_interface_json('destination_org')
        return OrgConfigDTO.destination_org_instance

    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.consumer_key = kwargs.get("consumer_key")
        self.consumer_secret = kwargs.get("consumer_secret")
        self.domain = kwargs.get("domain")
        self.namespace = kwargs.get("namespace")
        self.instance_url = kwargs.get("instance_url")
        self.nsp = self.namespace + "__"
        self.org_connector = Salesforce(username=self.username, password=self.password, consumer_key=self.consumer_key, consumer_secret=self.consumer_secret, instance_url = self.instance_url)
