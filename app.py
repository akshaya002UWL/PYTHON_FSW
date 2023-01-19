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
import threading
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
    print("Incoming call " + now.time())
    if request.method == 'GET':
        jr_id = request.args.get('jobReqId')
        req_skills = request.args.get('skills')
        experience = request.args.get('experience')
        skill_res = None if req_skills is None else req_skills.split(',')
        exp_inp = None if experience is None else (experience+"+").replace(" ", "")
        print(skill_res)
        print(exp_inp)
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

@app.route('/getJRId', methods=['POST'])
def getJRId():
    print('reac')
    if request.method == 'POST':
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
    
@app.route('/modifyDescComp', methods=['POST'])
def update_JDAndComp():
    if request.method == 'POST':
        input_data = request.get_json()
        key = next(iter(input_data))
        input_josn = input_data[key]
        print(input_josn)
        hiringManager = request.args.get("HiringManager").replace('%20', ' ')
        recruiter = request.args.get("Recruiter").replace('%20', ' ')
        input_josn['hiringManager'] = hiringManager
        input_josn['recruiter'] = recruiter
        print("request.args.get(HiringManager) == " + hiringManager)
        print("request.args.get(Recruiter) == " + recruiter)

        #Job_Requisition = input_josn['Job_Requisition']
        #Job_Requisition = mongo.db.WORecruitmentFlow.find_one( {"jobReqId": jobReqId},{"_id": 0} );
        # print(Job_Requisition)
        #Job_Requisition = request.get_json();
        # print(Job_Requisition)
        #Job_Requisition['jobReqLocale'][0]['jobDescription'] = job_description;
        mongo.db.WORecruitmentFlow.update_one(
            {"jobReqId": input_josn['jobReqId']}, {"$set": input_josn})
        Job_Requisition_JSON = {"Job_Requisition": input_josn}
        json_dumps = json.dumps(Job_Requisition_JSON, default=str)
        print("--------- Job_Requisition_JSON ---------")
        print(Job_Requisition_JSON)
        response = json.loads(json_dumps)
        return response
    
@app.route('/getJobDescription', methods=['GET'])
def getJobDescription():
    if request.method == 'GET':
        response = {}
        jr_id = request.args.get('jobReqId')
        can = mongo.db.WORecruitmentFlow.find({"jobReqId":jr_id}, {'_id': False})
        Job_Requisitions = list(can)
        response['instances'] =  next((el for el in Job_Requisitions if el is not None), {})
        return response

@app.route('/postJOBRequisition', methods=['POST'])
def post_job():
    if request.method == 'POST':
        jobReqId = request.args.get("jobReqId")
        jobProfile = request.args.get("jobProfile")
        channelName = request.args.get("channelName")
        print(jobReqId + " " + jobProfile + " " + channelName)
        print(request.get_json())

        jrs_withoutid = mongo.db.WORecruitmentFlow.find_one(
                {"jobReqId": jobReqId}, {"_id": 0})
        print("post job jrs_withoutid = " + str(jrs_withoutid))
        jrs_withoutid_string = dumps(jrs_withoutid)
        jrs_withoutid_json = json.loads(jrs_withoutid_string)
        jobDesc = jrs_withoutid_json["jobDescription"]
        response_json = {}

        if channelName is not None :
            if channelName == "Linked In" or channelName == "LinkedIn": 
                print("inside if channelName " + channelName)
                url = "https://api.linkedin.com/v2/ugcPosts"

                payload = json.dumps({
                "author": "urn:li:person:Ayyquo2cKD",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": jobDesc + " \n Please send email to 'jobs@woacmecorp.com' for further details."
                    },
                    "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
                }
                })
                headers = {
                'Authorization': 'Bearer AQWRfu3AN9G8-xnxk3cY0JaTTdc4iO-7WUKLl4upLkwcRwckfqvQ9Lw1hrcBYVZpRnQDvVmPiCSLJclDdvj9qoEMZbxloZ8UtEbmx090gltvOkFqhWhd1cp1QODXlfxNF-n9ABCFFlPQ7uQwALKUsRepj6Q87l8_uc5cUmhbqFEz3djX-lHqtmoEB4FVa4SBZ_JFiBDvParG316JaUlZGmwTwHBOk2N_zA4ceQeOcTrdXy7WUmMbXd2Vd7AzKF0Oqtl_Ws_RKwd28HnAbnKKsarzrnidjqZYPIcedK7U_XwMP6xMLxrk9YzbIpLXU8baWbRAuTPUSiwPThycM5cuuaBL48uNcw',
                'Content-Type': 'application/json',
                'Cookie': 'lidc="b=VB51:s=V:r=V:a=V:p=V:g=3284:u=4:x=1:i=1671642348:t=1671646515:v=2:sig=AQHVEdai1Q7Lj8Q0N3KQa7lXThuRe94y"; bcookie="v=2&f4a53cc3-9f87-47d7-8a78-cf544bcd2e41"; lang=v=2&lang=en-us; lidc="b=VB51:s=V:r=V:a=V:p=V:g=3284:u=4:x=1:i=1671642243:t=1671642915:v=2:sig=AQHvcQ2xL0pmGu5QzgdkFrF8rt1CBDV8"'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                print(response.text)

                response_text = "Job posted in LinkedIn. \n Please check this url to view the job posting : https://www.linkedin.com/in/test-account-wo-acme-corp-a9b34725b/recent-activity/"

                response_json["response"] = response_text

                return response_json

            elif None not in (jobReqId, jobProfile, channelName) and channelName == "Internal Posting" :

                response_text = "Posted Job " + jobReqId + " for " + str(jobProfile) + " on the " + str(channelName)
                response_json["response"] = response_text

                return response_json

            else :

                message = jsonify(Error='Invalid channel name')
                return make_response(message, 400)
        else : 

                message = jsonify(Error='Invalid inputs...')
                return make_response(message, 400)
            
@app.route('/getJobDeStatic', methods=['GET'])
def getJobDeStatic():
    if request.method == 'GET':
        response = {}
        response =   {
                        "jobReqId": "JR1234",
                        "jobDescription":"Test job description",
                        "jobProfile":"Devops Engineer"
                    }
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
