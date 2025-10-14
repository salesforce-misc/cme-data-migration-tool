from __future__ import annotations
from typing import Any, Dict, List, Optional
from simple_salesforce import Salesforce, SalesforceMalformedRequest, SalesforceLogin, SalesforceAuthenticationFailed
from tenacity import retry, stop_after_attempt, wait_exponential


class SalesforceClient:
    def __init__(
        self,
        username: str,
        password: str,
        domain: str = "login",
        instance_url: Optional[str] = None,
    ) -> None:
        try:
            session_id, instance = SalesforceLogin(
                username=username,
                password=password,
                security_token=None,
                domain=domain,
            )
            self._sf = Salesforce(instance=instance, session_id=session_id)
        except SalesforceAuthenticationFailed as e:
            raise e

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def query(self, soql: str) -> List[Dict[str, Any]]:
        '''
        Execute a SOQL query & fetch all records
        '''
        results: List[Dict[str, Any]] = []
        res = self._sf.query(soql)
        results.extend(res.get("records", []))
        while not res.get("done", True):
            res = self._sf.query_more(res.get("nextRecordsUrl"))
            results.extend(res.get("records", []))
        return results


