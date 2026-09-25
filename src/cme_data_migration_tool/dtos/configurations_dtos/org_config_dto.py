import requests
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

    @staticmethod
    def exchange_client_credentials_token(consumer_key, consumer_secret, instance_url):
        payload = {
            "grant_type": "client_credentials",
            "client_id": consumer_key,
            "client_secret": consumer_secret
        }
        response = requests.post(instance_url + "/services/oauth2/token", data=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"], token_data.get("instance_url", instance_url)

    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.consumer_key = kwargs.get("consumer_key")
        self.consumer_secret = kwargs.get("consumer_secret")
        self.domain = kwargs.get("domain")
        self.namespace = kwargs.get("namespace")
        self.instance_url = kwargs.get("instance_url")
        self.auth_type = kwargs.get("auth_type", "password")
        self.nsp = self.namespace + "__"

        if self.auth_type == "session":
            access_token, resolved_instance_url = OrgConfigDTO.exchange_client_credentials_token(
                self.consumer_key, self.consumer_secret, self.instance_url
            )
            self.org_connector = Salesforce(session_id=access_token, instance_url=resolved_instance_url)
        else:
            self.org_connector = Salesforce(username=self.username, password=self.password, consumer_key=self.consumer_key, consumer_secret=self.consumer_secret, instance_url = self.instance_url)
