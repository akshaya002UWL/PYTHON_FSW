import random
import re
from typing import Dict, List
import uuid
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from enum import Enum

import json



UPLOAD_FOLDER = 'templates'
ALLOWED_EXTENSIONS = set(['json'])
app = Flask(__name__)
CORS(app)

app.config['MONGO_URI'] = 'mongodb://admin:admin@adapt-mongo-adapt.cp4ba-mission-16bf47a9dc965a843455de9f2aef2035-0000.eu-de.containers.appdomain.cloud:32535/LTI?authSource=admin'
app.config['CORS_Headers'] = 'Content-Type'
mongo = PyMongo(app)

@app.route('/api/swagger.json')
def swagger_json():
    # Read before use: http://flask.pocoo.org/docs/0.12/api/#flask.send_file
    return send_file('swagger.json')


SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'
# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={  # Swagger UI config overrides
    'app_name': "Add/update JD"
},)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

@app.route('/filterAppliedCandidates', methods=['POST'])
def filterAppliedCandidates():
    candidateList =[]
    response={}
    req_candidates = request.get_json()
    key = next(iter(req_candidates))
    candidate =req_candidates[key]
    if request.method == 'POST':
        jr_id = request.args.get('jobReqId')
        if jr_id is not None:
            jr_id=jr_id.lower()
            for data in candidate:
                match = bool(jr_id) if jr_id in data["jobReqId"].lower() else bool()
                if(match is True):
                    candidateList.append(data)
            response['instances'] = candidateList
            return response
    if jr_id is None:
        response["message"] = "Job requisition id is null"
        return response

@app.route('/filterProfiles', methods=['POST'])
def filterProfiles():
    response={}
    candidate = []
    if request.method == 'POST':
        organization = request.args.get('organization')
        location = request.args.get('location')
        req_candidates = request.get_json()
        key = next(iter(req_candidates))
        input_candidates =req_candidates[key]
    if organization is None and location is None:
        response = input_candidates
        return response
    if organization is not None and location is not None:
        organization = organization.lower()
        location = location.lower()
        org_present = bool()
        loca_match = bool()
        for data in input_candidates:
            for exp in data["workExperience"]:
                employer = exp["employer"].lower()
                org_present = bool(employer) if organization in employer else bool()
            loca_match = bool(location) if location in data["city"].lower()  or location in data["country"].lower() else bool()
            if(loca_match is True and org_present is True):
                candidate.append(data)
        response['instances'] = candidate
        return response
    else:
        if organization is not None :
            organization = organization.lower()
            org_present = bool()
            for data in input_candidates:
                for exp in data["workExperience"]:
                    employer = exp["employer"].lower()
                    org_present = bool(employer) if organization in employer else bool()
                    print(org_present)
                    if(org_present is True):
                        candidate.append(data)
            response['instances'] = candidate
            return response
        elif location is not None:
            loca_match = bool()
            location = location.lower()
            for data in input_candidates:
                loca_match = bool(location) if location in data["city"].lower()  or location in data["country"].lower() else bool()
                if(loca_match is True):
                    candidate.append(data)
            response['instances'] = candidate
            return response


@app.route('/getByJR', methods=['GET'])
def getByJR():
    response = {}
    candidateList = []
    can = mongo.db.Candidate_Details.find({}, {'_id': False})
    candidate = list(can)
    if request.method == 'GET':
        jr_id = request.args.get('jobReqId')
        req_skills = request.args.get('skills')
        experience = request.args.get('experience')
        skill_res = None if req_skills is None else req_skills.split(',')
        exp_inp = None if experience is None else (experience+"+").replace(" ", "")
        if jr_id is not None :
            if skill_res is not None:
                skills = [x.lower() for x in skill_res]
                for data in candidate:
                    canSkills = data["skills"].split(",")
                    test = bool()
                    print(skills)
                    for i in canSkills:
                        if i.lower() in skills:
                            test = bool(i)
                    print(test)
                    if(test is True):
                        print(exp_inp)
                        if(exp_inp is not None):
                            for exp in data["workExperience"]:
                                exp_present = bool(exp_inp) if exp_inp in exp["duration"] else bool()
                            if(exp_present):
                                data["jobReqId"] = jr_id
                        candidateList.append(data)
                response['instances'] = candidateList
                return response
            elif exp_inp is not None:
                print("exp-")
                for data in candidate:
                    for exp in data["workExperience"]:
                        exp_present = bool(exp_inp) if exp_inp in exp["duration"] else bool()
                    if(exp_present):
                        data["jobReqId"] = jr_id
                        candidateList.append(data)
                response['instances'] = candidateList
                return response
            else:
                for data in candidate:
                    data["jobReqId"] = jr_id
                response['instances'] = candidate
                return response
        if jr_id is None:
            response["message"] = "Job requisition id is null"
            return response
        
@app.route('/changeCandStatus', methods=['PUT'])
def changeCandStatus():
    class interviewStages(Enum):
        TECH1 = "Tech-Round-1"
        TECH2 = "Tech-Round-2"
        FINAL = "Final-Round"
    req_candidates = request.get_json()
    key = next(iter(req_candidates))
    candidate = req_candidates[key]
    if request.method == 'PUT':
        for i in candidate:
            if i["interview_stage"] is not None:
                def switch_example(stage):
                    if stage == interviewStages.TECH1.value:
                        i["interview_stage"] = interviewStages.TECH2.value
                        return
                    elif stage == interviewStages.TECH2.value:
                        i["interview_stage"] = interviewStages.FINAL.value
                        return
                    else:
                        i["interview_stage"] = interviewStages.FINAL.value
                switch_example(i["interview_stage"])
        return candidate

@app.route('/getJRId', methods=['GET'])
def getJRId():
    print('reac')
    if request.method == 'GET':
        print('start')
        input_data = request.get_json()
        key = next(iter(input_data))
        existing_jr = input_data[key]
        print(existing_jr)
        response = {}
        if existing_jr is not None and "jobReqId" in existing_jr:
            response["jobReqId"] = existing_jr["jobReqId"]
        else:
            response["message"] = "No JR ID found"
        response_string = json.dumps(response, default=str)
        response_json = json.loads(response_string)
        print(response_json)
        return response_json
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
