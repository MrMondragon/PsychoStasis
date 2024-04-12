from flask import Flask, request
from .Nexus import Nexus
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)
CORS(app)

################################ Model Manager #################################
manager = Nexus()

@app.route('/LoadModel', methods=['POST'])
def LoadModel_request():
    modelName = request.json['modelName']
    model_type = request.json['model_type']
    task = request.json['task']
    core = request.json['core']

    # Pass parameters as keyword arguments
    manager.LoadModel(modelName=modelName, model_type=model_type, task=task, core=core)


    return {'message': 'Model loaded'}

@app.route('/UnloadModel', methods=['POST'])
def UnloadModel_request():
    modelName = request.json['modelName']
    core = request.json['core']

    manager.UnloadModel(modelName, core)

    return {'message': 'Model unloaded'}


@app.route('/ActivateModel', methods=['POST'])
def ActivateModel_request():
    modelName = request.json['modelName']
    core = request.json['core']

    manager.ActivateModel(modelName, core)

    return {'message': 'Model activated'}

@app.route('/DeactivateModel', methods=['POST'])
def DeactivateModel_request():
    modelName = request.json['modelName']
    core = request.json['core']

    manager.DeactivateModel(modelName, core)

    return {'message': 'Model deactivated'}

@app.route('/model_list', methods=['GET'])
def GetModelList_request():
    print("Getting model list...")
    core = request.args.get('core', default='true') == 'true'
    model_list = Nexus.GetModelList(core=core)
    print(f"Model list: {model_list}")
    return jsonify(model_list)

@app.route('/modelNames', methods=['GET'])
def get_modelNames_request():
    print("Getting model names...")
    core = request.args.get('core', default='true') == 'true'
    model_list = Nexus.get_modelNames(core=core)
    print(f"Model list: {model_list}")
    return jsonify(model_list)

################################################################################




if __name__ == '__main__':
    app.run(debug=True)