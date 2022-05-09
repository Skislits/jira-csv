"""Parse or create configuration file"""
import os
import configparser


class Credential:
    """Jira host and user credentials"""
    username: str
    password: str
    server_url: str

    def __init__(self):
        """Constructor"""
        pass


def init_config():
    """Main method"""
    credential = Credential()
    if os.path.isfile('./credentials.ini'):
        read_config(credential)
    else:
        _create_config(credential)
    return credential


def read_config(credential: Credential):
    config = configparser.ConfigParser()
    config.sections()
    config.read('credentials.ini')
    credential.username = config['DEFAULT']['Username']
    credential.password = config['DEFAULT']['Password']
    credential.server_url = config['DEFAULT']['Server']


def _create_config(credential: Credential):
    print('Enter Jira login:')
    credential.username = input()
    print('Enter Jira password:')
    credential.password = input()
    print('Enter Jira host (https://jira.com):')
    credential.server_url = input()

    config = configparser.ConfigParser()
    config['DEFAULT'] = {'Username': credential.username,
                         'Password': credential.password,
                         'Server': credential.server_url}
    
    with open('credentials.ini', 'w') as configfile:
        config.write(configfile)
