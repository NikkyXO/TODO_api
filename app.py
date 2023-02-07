from flask import render_template
import connexion
from settings.config import Config
from settings.database import Base, engine
from jwt_manager import jwt
import os

options = {'swagger_ui': True,
           'strict_validation': True,
           'validate_responses': True}

connexion_app = connexion.App(__name__,
                              specification_dir="./", options=options)

connexion_app.add_api("swagger.yml")
app = connexion_app.app

app.config.from_object(Config)

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_ADD_STATUS'] = True
app.config['JSON_STATUS_FIELD_NAME'] = 'status'


jwt.init_app(app)

Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
