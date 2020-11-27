import os
from random import randint
import pickle
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import Flask, request, jsonify, send_from_directory
from flask_restx import Api, Resource, abort, fields
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
import geopy as gp
import geopandas as gpd
from shapely.geometry import Point
import open3d as o3d

from assets.communes import ranks


# Init app
app = Flask(__name__)
api = Api(app, version='1.0', title='ImmoEliza API', description='API that return a price prediction for a building in Belgium', default='V1', default_label='first test')
basedir = os.path.abspath(os.path.dirname(__file__))

# Fix the Flask-RESTx https error
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

resource_fields = api.model('Predict', {
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

resource_fields2 = api.model('3D', {
    'lat' : fields.Float,
    'long' : fields.Float,
    'size' : fields.Integer
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
@api.doc(body=resource_fields, description='Enter these parameters to get a price prediction.')
class predict(Resource):
    def post(self):
        infos = request.get_json()

        zip_code = infos['ZIP']
        type_of_property = infos['type_of_property']
        subtype_of_property = infos['subtype_of_property']
        number_of_rooms = infos['number_of_rooms']
        house_area = infos['house_area']
        surface_of_the_land = infos['surface_of_the_land']
        number_of_facades = infos['number_of_facades']
        swimming_pool = infos['swimming_pool']
        state_of_the_building = infos['state_of_the_building']
        road = infos['road']
        number = infos['number']
        rank = ranks[zip_code]

        if type_of_property == 'house' :

            model = pickle.load(open('assets/house_model.sav','rb'))
            params = [number_of_rooms, 
                house_area, 
                surface_of_the_land, 
                swimming_pool,
                rank,
                1 if (subtype_of_property == 'chalet') else 0,
                1 if (subtype_of_property == 'country cottage') else 0,
                1 if (subtype_of_property == 'exceptional property') else 0,
                1 if (subtype_of_property == 'farmhouse') else 0,
                1 if (subtype_of_property == 'house') else 0,
                1 if (subtype_of_property == 'manor house') else 0,
                1 if (subtype_of_property == 'mansion') else 0,
                1 if (subtype_of_property == 'mixed use building') else 0,
                1 if (subtype_of_property == 'other property') else 0,
                1 if (subtype_of_property == 'town house') else 0,
                1 if (subtype_of_property == 'villa') else 0,
                1 if (state_of_the_building == 'good') else 0,
                1 if (state_of_the_building == 'just renovated') else 0,
                1 if (state_of_the_building == 'to be done up') else 0,
                1 if (state_of_the_building == 'to renovate') else 0,
                1 if (state_of_the_building == 'to restore') else 0,
                1 if (state_of_the_building == 'unknown') else 0
                ]

        else :
            model = pickle.load(open('assets/apart_model.sav','rb'))
            params = [number_of_rooms, 
                house_area, 
                surface_of_the_land, 
                number_of_facades,
                swimming_pool,
                rank,
                1 if (subtype_of_property == 'duplex') else 0,
                1 if (subtype_of_property == 'flat studio') else 0,
                1 if (subtype_of_property == 'ground floor') else 0,
                1 if (subtype_of_property == 'kot') else 0,
                1 if (subtype_of_property == 'loft') else 0,
                1 if (subtype_of_property == 'penthouse') else 0,
                1 if (subtype_of_property == 'service flat') else 0,
                1 if (subtype_of_property == 'triplex') else 0,
                1 if (state_of_the_building == 'good') else 0,
                1 if (state_of_the_building == 'just renovated') else 0,
                1 if (state_of_the_building == 'to be done up') else 0,
                1 if (state_of_the_building == 'to renovate') else 0,
                1 if (state_of_the_building == 'to restore') else 0,
                1 if (state_of_the_building == 'unknown') else 0
                ]

        pred = round(model.predict([params])[0], 2)

        google_key = os.environ.get("GOOGLEAPI", None)
        
        address = f"{road}, {number} {zip_code}"

        locator = gp.geocoders.GoogleV3(api_key=google_key)
        try :
            location = locator.geocode(address, timeout=10)
            longitude = location.longitude
            latitude = location.latitude
        except :
            longitude = None
            latitude = None
        
        response = {'prediction' : pred,
                    'coordinates' : {'latitude' : latitude,
                                    'longitude' : longitude},
                    }

        return jsonify(response)


@api.route('/get_file', methods=['POST'])
@api.doc(body=resource_fields2, description='Enter these parameters to get a 3D file of the place.')
class get_file(Resource):
    def post(self):
        infos = request.get_json()

        latitude = infos['lat']
        longitude = infos['long']
        size = infos['size']

        p = gpd.GeoSeries([Point(longitude, latitude)])
        p.crs = 'epsg:4326'
        p = p.to_crs(epsg=31370)

        y = p[0].y
        x = p[0].x
        

        hainaut = pd.read_csv('./assets/hainaut.csv')

        place = hainaut[(hainaut["x"] <= x + size) & 
                    (hainaut["x"] >= x - size) & 
                    (hainaut["y"] <= y + size) & 
                    (hainaut["y"] >= y - size)]

        meanx = place['x'].mean()
        meany = place['y'].mean()
        minz = place['z'].min()

        final = pd.DataFrame()
        final['x'] = place['x'] - meanx
        final['y'] = place['y'] - meany
        final['z'] = place['z'] - minz
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(final.to_numpy())
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug) as cm:
            poisson_mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=8, linear_fit =True)

        densities = np.asarray(densities)
        density_colors = plt.get_cmap('viridis')(
            (densities - densities.min()) / (densities.max() - densities.min()))
        density_colors = density_colors[:, :3]
        density_mesh = o3d.geometry.TriangleMesh()
        density_mesh.vertices = poisson_mesh.vertices
        density_mesh.triangles = poisson_mesh.triangles
        density_mesh.triangle_normals = poisson_mesh.triangle_normals
        density_mesh.vertex_colors = o3d.utility.Vector3dVector(density_colors)

        vertices_to_remove = densities < np.quantile(densities, 0.01)
        density_mesh.remove_vertices_by_mask(vertices_to_remove)

        o3d.io.write_triangle_mesh("./3D/3D_houses.obj", density_mesh)

        return send_from_directory('./3D', '3D_houses.obj', as_attachment=True)


# Run server
if __name__ == '__main__':
    app.run("0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)