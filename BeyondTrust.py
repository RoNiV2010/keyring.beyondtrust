import json
from typing import Tuple
from keyring.backend import KeyringBackend
from keyring import credentials
import requests
from collections import defaultdict

class BTPasswordSafe(KeyringBackend):
    """Retrive password from BeyondTrust Password Safe"""

    def __init__(self, BaseURL: str, credentials: credentials):
        #Connect to BeyondTrust and initiate a session
        self.BaseURL = BaseURL
        self.session, self._last_api_status = self.__class__.APILogin(BaseURL,credentials.username, credentials.password)
        self._keyring_dict = None

    def set_password(self, servicename, username, password):
        #No password assignment for managed accounts
        pass

    def get_password(self, servicename, username):
        """Get password of the username for the service
        Username may be provided in following formats:
        <username> or <domain\username>"""
        uname = username.split('\\')[-1]
        result = self._get_entry(self._keyring, servicename, uname)
        if result:
            if not ("password" in result.keys()):
                self._read_password(servicename, uname)
                result = self._get_entry(self._keyring, servicename, uname)
            result = result["password"]
        return result

    @property
    def _keyring(self):
        if self._keyring_dict is None:
            self._keyring_dict, self._last_api_status = self._read()
        return self._keyring_dict

    def _get_entry(self, keyring_dict, service, username):
        #returns an account dict or None
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
        self._keyring[servicename][username]["password"],self._last_request,self._last_api_status = self.__class__.APIGetPassword(self.BaseURL, account, self.session)


    def delete_password(self, servicename, username):
        #No account removal
        pass

    @staticmethod
    def APILogin(BaseURL: str, username: str, key: str) -> Tuple[requests.Session, int]:
        #Create a session to BeyondTrust.
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
        #read a list of available managed accounts and convert into dictionary
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
        #Create a request to PasswordSafe and get a password based on the request.
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
        #Path concatination
        result = '/'.join(s.strip('/') for s in args)
        return result
        
 
