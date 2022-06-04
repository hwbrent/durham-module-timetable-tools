import os

def load_environment_variables() -> None:
    ''' Loads the environment variables from `.env` and adds then to python's `os.environ`. '''

    with open("../../.env", "r") as f:
        
        for line in f.readlines():

            if line[0] == "#":
                continue

            if line == "\n":
                continue

            key, value = line.split(" = ")
            value = value.strip()
            # value.replace("\"", "")

            os.environ[key] = value
