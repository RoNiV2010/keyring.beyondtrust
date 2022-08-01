import json
from typing import Tuple
from keyring.backend import KeyringBackend
from keyring import credentials
import requests
from collections import defaultdict

class BTPasswordSafe(KeyringBackend):
    """Retrive password from BeyondTrust Password Safe"""

    def __init__(self, BaseURL: str, credentials: credentials):
        self.BaseURL = BaseURL
        self.session, status = self.__class__.APILogin(BaseURL,credentials.username, credentials.password)
        self._keyring_dict = None

    def set_password(self, servicename, username, password):
        pass

    def get_password(self, servicename, username):
        """Get password of the username for the service"""
        result = self._get_entry(self._keyring, servicename, username)
        if result:
            if not ("password" in result.keys()):
                self._read_password(servicename, username)
                result = self._get_entry(self._keyring, servicename, username)
            result = result["password"]
        return result

    @property
    def _keyring(self):
        if self._keyring_dict is None:
            self._keyring_dict, self._last_api_status = self._read()
        return self._keyring_dict

    def _get_entry(self, keyring_dict, service, username):
        result = None
        service_entries = keyring_dict.get(service)
        if service_entries:
            result = service_entries.get(username)
        return result

    def _read(self):
        accounts_dict, status_code = self.__class__.APIGetAccounts(self.BaseURL, self.session)
        return accounts_dict, status_code

    def _read_password(self, servicename, username):
        account = self._keyring[servicename][username]
        self._keyring[servicename][username]["password"],request,stauscode = self.__class__.APIGetPassword(self.BaseURL, account, self.session)


    def delete_password(self, servicename, username):
        pass

    @staticmethod
    def APILogin(BaseURL: str, username: str, key: str) -> Tuple[requests.Session, int]:
        try:
            targetURL = __class__.URLJoin(BaseURL, "/Auth/SignAppin") 
            header = {'Authorization': f'PS-Auth key={key}; runas={username}', 'Content-Type':'application/json'}
            session = requests.Session()
            session.headers.update(header)
            response = session.post(targetURL)
            response.raise_for_status
            return session, response
        except Exception as e:
            print(e)

    @staticmethod
    def APIGetAccounts(BaseURL: str, session: requests.Session) -> Tuple[dict, int]:
        try:
            targetURL = __class__.URLJoin(BaseURL, "/ManagedAccounts")
            accounts = session.get(targetURL)
            accounts.raise_for_status()
            accdict = defaultdict(dict)
            {accdict[item["SystemName"]].update({item["AccountName"]: item}) for item in accounts.json()}
            accdict = dict(accdict)
            return accdict, accounts.status_code
        except Exception as e:
            print(e)
    
    @staticmethod
    def APIGetPassword(BaseURL: str, account, session: requests.Session) -> Tuple[str, requests.models.Response, int]:
        try:
            targetURL = __class__.URLJoin(BaseURL, "/Requests")
            reqdata = {"AccountId": account["AccountId"], "SystemId": account["SystemId"], "DurationMinutes": 120, "Reason": "Python keyring", "ConflictOption": "reuse"}
            jsondata = json.dumps(reqdata)
            wreq = requests.Request(method = "POST", url = targetURL, data = jsondata)
            wreq = session.prepare_request(wreq)
            request = session.send(wreq)
            request.raise_for_status()
            requestID = request.json()
            targetURL = __class__.URLJoin(BaseURL, "Credentials/", str(requestID))
            pwddata = {"AccountId": account["AccountId"], "RequestI d": requestID}
            result = session.get(targetURL, data=pwddata)
            result.raise_for_status()
            return result.json(), request, result.status_code
        except Exception as e:
            print(e.with_traceback(None))

    @staticmethod
    def URLJoin(*args: str) -> str:
        result = '/'.join(s.strip('/') for s in args)
        return result
        
 
