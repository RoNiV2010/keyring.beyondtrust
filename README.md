# keyring.beyondtrust
Python keyring ext. 


Usage example:

>>> import keyring
>>> from BeyondTrust import BTPasswordSafe
>>> creds = keyring.credentials.SimpleCredential("<API account>", "<LongAPIKey goes here>")
>>> keyring.set_keyring(BTPasswordSafe("<API url goes here>", creds))
>>> password = keyring.get_password("<system name>","<account name>")