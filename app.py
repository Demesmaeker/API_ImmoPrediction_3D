import os
from random import randint
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, abort, fields
from werkzeug.middleware.proxy_fix import ProxyFix


# Init app
app = Flask(__name__)
api = Api(app, version='1.0', title='ImmoEliza API', description='API that return a price prediction for a building in Belgium', default='V1', default_label='first test')
basedir = os.path.abspath(os.path.dirname(__file__))

# Fix the Flask-RESTx https error
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

resource_fields = api.model('Resource', {
    'ZIP': fields.Integer,
    'type_of_property' : fields.String,
    'subtype_of_property' : fields.String,
    'number_of_rooms' : fields.Integer,
    'house_area' : fields.Integer,
    'surface_of_the_land' : fields.Integer,
    'number_of_facades' : fields.Integer,
    'swimming_pool' : fields.Integer,
    'state_of_the_building' : fields.String,
    'road' : fields.String,
    'number' : fields.Integer
})


@api.route('/status', methods=['GET'])
@api.doc(description='This API is alive !')
class status(Resource):
    def get(self):
        result = {
            'status' : True,
            'message' : 'The server is alive! Please, don\'t kill it...'
        }
        return jsonify(result)


@api.route('/predict', methods=['POST'])
@api.doc(body=resource_fields, description='Enter these parameters to get a price prediction')
class predict(Resource):
    def post(self):
        infos = request.get_json()
        response = {'prediction' : randint(100000, 500000)}
        return jsonify(response)


# Run server
if __name__ == '__main__':
    app.run("0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)