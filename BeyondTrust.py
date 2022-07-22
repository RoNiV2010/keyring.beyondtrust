from keyring.backend import KeyringBackend
import requests

class BTPasswordSafe(KeyringBackend):
    """Retrive password from BeyondTrust Password Safe"""

    def set_password(self, servicename, username, password):
        pass

    def get_password(self, servicename, username):
        """Get password of the username for the service"""
        result = self._get_entry(self._keyring, service, username)
        if result:
            result = self._decrypt(result)
        return result

    @property
    def _keyring(self):
        if self._keyring_dict is None:
            self.docs_entry, self._keyring_dict = self._read()
        return self._keyring_dict

    def _read(self):
        pass

    def delete_password(self, servicename, username):
        pass

    @staticmethod
    def APILogin(BaseURL: str, username: str, key: str) -> requests.Session:
        pass
 
