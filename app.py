from flask import Flask, request
from .Nexus import Nexus
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)
CORS(app)

################################ Model Manager #################################
manager = Nexus()

@app.route('/load_model', methods=['POST'])
def load_model_request():
    model_name = request.json['model_name']
    model_type = request.json['model_type']
    task = request.json['task']
    core = request.json['core']

    # Pass parameters as keyword arguments
    manager.load_model(model_name=model_name, model_type=model_type, task=task, core=core)


    return {'message': 'Model loaded'}

@app.route('/unload_model', methods=['POST'])
def unload_model_request():
    model_name = request.json['model_name']
    core = request.json['core']

    manager.unload_model(model_name, core)

    return {'message': 'Model unloaded'}


@app.route('/activate_model', methods=['POST'])
def activate_model_request():
    model_name = request.json['model_name']
    core = request.json['core']

    manager.activate_model(model_name, core)

    return {'message': 'Model activated'}

@app.route('/deactivate_model', methods=['POST'])
def deactivate_model_request():
    model_name = request.json['model_name']
    core = request.json['core']

    manager.deactivate_model(model_name, core)

    return {'message': 'Model deactivated'}

@app.route('/model_list', methods=['GET'])
def get_model_list_request():
    print("Getting model list...")
    core = request.args.get('core', default='true') == 'true'
    model_list = Nexus.get_model_list(core=core)
    print(f"Model list: {model_list}")
    return jsonify(model_list)

@app.route('/model_names', methods=['GET'])
def get_model_names_request():
    print("Getting model names...")
    core = request.args.get('core', default='true') == 'true'
    model_list = Nexus.get_model_names(core=core)
    print(f"Model list: {model_list}")
    return jsonify(model_list)

################################################################################




if __name__ == '__main__':
    app.run(debug=True)