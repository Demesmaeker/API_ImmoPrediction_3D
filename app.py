import os
from random import randint
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, abort


# Init app
app = Flask(__name__)
api = Api(app, version='1.0', title='ImmoEliza API', description='API that return a price prediction for a building in Belgium', default='V1', default_label='first test')
basedir = os.path.abspath(os.path.dirname(__file__))


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
@api.doc(params={
    'ZIP': 'Int : Postal Code',
    'type_of_property' : 'house or apart',
    'subtype_of_property' : 'house, apartment, villa, duplex, ground floor, penthouse, mixed use building, flat studio, mansion, exceptional property, town house, service flat, country cottage, bungalow, loft, chalet, farmhouse, triplex, manor house, kot, other property',
    'house_area' : 'Int : m2',
    'surface_of_the_land' : 'Int : m2',
    'state_of_the_building' : 'New, ...'
}, description='Enter these parameters to get a price prediction')
class predict(Resource):
    def post(self):
        building = request.get_json()
        number = randint(100000, 500000)
        return number



# Run server
if __name__ == '__main__':
    app.run(port=5000)