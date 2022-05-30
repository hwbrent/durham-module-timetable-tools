import os
import json

import flask
from flask_cors import CORS #, cross_origin

from scraper import Scraper
from env import load_environment_variables

# ============================================================

def server():
    '''
    # Routes:

    ---

    #### /
    - The index. Does nothing essentially.

    ---

    #### /validate/<username>/<password>
    - Accessed in the `<LoginPage/>` component.
    - Passes the `username` and `password` to the `Scraper.user_credentials_are_valid` method and returns a `bool` based on if the credentials indicate that the user is valid or not.

    ---
    '''
    app = flask.Flask(__name__)
    CORS(app)

    load_environment_variables()

    scraper = Scraper(
        os.environ.get("APP_SCRAPER_USERNAME"),
        os.environ.get("APP_SCRAPER_PASSWORD"),
    )


    # ------------------------------

    @app.route("/")
    def index():
        return flask.jsonify("Welcome to my Flask server. Make yourself at home :)")

    # ------------------------------

    @app.route("/validate/<username>/<password>")
    def validate(username:str, password:str) -> bool:
        data = scraper.user_credentials_are_valid(username, password)
        return flask.jsonify(data)

    # ------------------------------

    @app.route("/get/modulenames")
    def get_modulenames() -> list:

        all_params = scraper.get_module_timetable_url_parameters()
        module_names = [sublist[0] for sublist in all_params["Select Module(s) to View:"]]
        
        data = module_names
        return flask.jsonify(data)

    # ------------------------------

    @app.route("/getmoduletimetables", methods=["POST"])
    def getmoduletimetables() -> list:

        body_data = flask.request.get_json()
        # print()
        # print("body_data:", body_data)
        # print()
        
        data = body_data
        return flask.jsonify(data)

    # ------------------------------

    @app.route("/test")
    def test():
        var = os.environ.get("PASSWORD")
        json_ed = json.loads(var)
        return flask.jsonify(json_ed)

    # ------------------------------
    
    return app

# ============================================================

if __name__ == "__main__":
    server().run(debug=True)
