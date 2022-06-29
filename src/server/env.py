import os

def load_environment_variables() -> 'None':
    ''' Parses `.env` and adds them to python's `os.environ`. '''

    with open("../../.env", "r") as f:
        
        for line in f.readlines():

            if line[0] == "#":
                continue

            if line == "\n":
                continue

            key, value = line.split(" = ")
            value = value.strip()

            os.environ[key] = value

def auth() -> 'list':
    ''' Returns the auth username and password in a list. '''
    return [os.environ.get("APP_SCRAPER_USERNAME"),os.environ.get("APP_SCRAPER_PASSWORD")]
