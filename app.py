from flask import render_template
import connexion
from config import Config
from database import Base, engine
from jwt_manager import jwt

options = {'swagger_ui': True,
           'strict_validation': True,
           'validate_responses': True}

# 'JWT_DECODE_HANDLER': bearer_info_func}

connexion_app = connexion.App(__name__,
                              specification_dir="./", options=options)

connexion_app.add_api("swagger.yml")
# security_handlers={'bearerAuth': decodetoken}

app = connexion_app.app

app.config.from_object(Config)

app.config['SECRET_KEY'] = "d8548793446a4d1f9b369f9d6f1b722f"
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_STORE'] = 'database'
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']

jwt.init_app(app)


@app.route("/")
def home():
    return render_template("home.html")


Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
