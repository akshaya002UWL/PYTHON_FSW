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
import requests



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
        response['Job_Requisition'] =  next((el for el in Job_Requisitions if el is not None), {})
        return response

@app.route('/postJOBRequisition', methods=['POST'])
def post_job():
    if request.method == 'POST':
        try:
            jobReqId = request.args.get("jobReqId")
            jobProfile = request.args.get("jobProfile")
            channelName = request.args.get("channelName")
            print(request.args)
            print(jobReqId + " " + jobProfile + " " + channelName)

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

                    response_text = "https://www.linkedin.com/in/test-account-wo-acme-corp-a9b34725b/recent-activity/"

                    response_json["response"] = response_text

                    return response_json

                elif None not in (jobReqId, jobProfile, channelName) and channelName == "Internal Posting" :

                    response_text = "Posted Job " + jobReqId + " for " + str(jobProfile) + " on the " + str(channelName)
                    response_json["response"] = response_text

                    return response_json

                else :

                    response["message"] = "Invalid channel name"
                    return response
            else : 
                    
                    response["message"] = "Invalid inputs..."
                    return response
        except Exception as e:
            response = {"errorCode": "ER101",
                        "errorMessage": e}
            return response
            
@app.route('/createNewJobRequisition', methods=['POST'])
def create_new_job_requisition():
    if request.method == 'POST':
        response = {}
        existing_jr = request.get_json()
        key = next(iter(existing_jr))
        input_josn = existing_jr[key]
        print(input_josn)
        print("type(existing_jr) = " + str(type(existing_jr)))
        print("---existing_jr---")
        print(existing_jr)
        new_jr = existing_jr[key]
        print("---new_jr----- BEFORE ----")
        print(new_jr)
        print("type(new_jr) = " + str(type(new_jr)))
        new_jrID = ""
        if existing_jr is not None and "jobReqId" in existing_jr[key]:
            existing_jrID = existing_jr[key]["jobReqId"]
            lastExistingJR = mongo.db.WORecruitmentFlow.find_one(
                {}, sort=[('jobReqId', -1)])
            if existing_jrID or lastExistingJR is not None:
                lastExistingJRId = lastExistingJR["jobReqId"]
                existing_JRId = ""
                if lastExistingJRId:
                    existing_JRId = lastExistingJRId
                else:
                    existing_JRId = existing_jrID
                print("existing_JRId[-4:] = " + existing_JRId[-4:])
                last_four_chars = existing_JRId[-4:]
                print(last_four_chars.isnumeric())
                if (last_four_chars and last_four_chars.isnumeric()):
                    new_jrID = f'{"JR"}{int(last_four_chars)+1:04d}'
                if not new_jrID:
                    new_jrID = "JR" + str(random.randint(1000, 9999))
                print("new jr id = " + new_jrID)
            else:
                new_jrID = "JR" + str(random.randint(1000, 9999))
            new_jr["jobReqId"] = new_jrID
            jrs = mongo.db.WORecruitmentFlow.insert_one(new_jr)
        if new_jr is not None:
            #response["message"] = "Added new Job requisition with ID = " + new_jrID
            #response = json.dumps(new_jr, indent = 4)
            # print(new_jr)
            #response = jsonify(new_jr)
            #jrs_json = dumps(jrs)
            #response = json.loads(jrs_json)
            #response["message"] = "New JR created!!! New JR ID is : " + new_jrID
            print("---jrs_withoutid----- AFTER ----")
            jrs_withoutid = mongo.db.WORecruitmentFlow.find_one(
                {"jobReqId": new_jrID}, {"_id": 0})
            print(jrs_withoutid)
            jrs_withoutid_string = dumps(jrs_withoutid)
            jrs_withoutid_json = json.loads(jrs_withoutid_string)
            response["JobRequisitionResponse"] = jrs_withoutid_json
            response["jobReqId"] = new_jrID


            response_string = json.dumps(response, default=str)
            response_json = json.loads(response_string)
            print(response_json)
            return response_json
            #return response
        else:
            response["message"] = "Error in adding new JR"
            return response


@app.route('/wrapJobRequisition', methods=['POST'])
def wrapJobRequisition():
    if request.method == 'POST':
        print("starting api..")
        response = {}
        try :
            if request.get_json() is not None :
                input_data = request.get_json()
                key = next(iter(input_data))
                jr = input_data[key]
                print(jr)
                response["Job_Requisition"] = jr
            else:
                response["message"] = "No Job_Requisition "
        except :
            response["message"] = "Invalid data"
        response_string = json.dumps(response, default=str)
        response_json = json.loads(response_string)
        print(response_json)
        return response_json

@app.route('/getAllJobRequisitions', methods=['GET'])
def get_all_job_requisitions():
    if request.method == 'GET':
        department = ''
        jobProfile = request.args.get('jobProfile')
        location = request.args.get('location')
        status = request.args.get('status')

        try:
            # The below line of code is used to extract JRs inside instances field. Now we don't have instances field in Mongo DB
            # We have each JR as an individual document in MOngo DB collection so below query is not needed.
            # jrs = mongo.db.WORecruitmentFlow.find({}, {"instances": 0, "_id": 0})
            jrs = mongo.db.WORecruitmentFlow.find(
                {"jobReqId": {"$exists": True}}, {"_id": 0})
            jrs_string = dumps(jrs)
            jrs_response = []
            print(jrs_response)
            if None not in ( location, jobProfile, status):
                jobProfile = jobProfile.replace('%20', ' ')
                location = location.replace('%20', ' ')
                print('Query string department = ' + department)
                print('Query string location = ' + location)
                print('Query string status = ' + status)
                print('Query string jobProfile = ' + jobProfile)
                jrs_json = json.loads(jrs_string)
               # jrs_json = ''
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if ("city" in i or "country" in i or "state" in i or "location" in i) and "department" in i and "status" in i and "jobProfile" in i:
                        _city = i["city"].lower()
                        _country = i["country"].lower()
                        _state = i["state"].lower()
                        _department = i["department"].lower()
                        _location = i["location"].lower()
                        _status = i["status"].lower()
                        _jobProfile = i["jobProfile"].lower()
                        print(type(i))
                        if (((_city is not None and _city and location.lower() in _city) or (_country is not None and _country and location.lower() in _country)
                             or (_state is not None and _state and location.lower() in _state)
                             or (_location is not None and _location and location.lower() in _location))
                                and (_status is not None and _status and status.lower() in _status)
                                and (_jobProfile is not None and _jobProfile and jobProfile.lower() in _jobProfile)):
                                        jrs_response.append(i)
                                        print("------------worked")
                                        # print(jrs_response)
                                        print("_city" + _city)
                                        print("_country" + _country)
                                        print("_state" + _state)
                                        print("_location" + _location)
                                        print("_department" + _department)
                                        print("_status" + _status)
                                        print("_jobProfile" + _jobProfile)
                                        
                        # print(jrs_response)
            elif None not in (location, status):
                location = location.replace('%20', ' ')
                print('Query string status = ' + status)
                print('Query string location = ' + location)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if ("city" in i or "country" in i or "state" in i or "location" in i) and "status" in i:
                        _city = i["city"].lower()
                        _country = i["country"].lower()
                        _state = i["state"].lower()
                        _location = i["location"].lower()
                        _status = i["status"].lower()
                        if (((_city is not None and _city and location.lower() in _city)
                        or (_country is not None and _country and location.lower() in _country)
                        or (_state is not None and _state and location.lower() in _state)
                        or (_location is not None and _location and location.lower() in _location))
                                and (_status is not None and _status and status.lower() in _status)):
                            print("_city" + _city)
                            print("_country" + _country)
                            print("_state" + _state)
                            print("_location" + _location)
                            print("_status" + _status)
                            jrs_response.append(i)
            elif None not in (location, jobProfile):
                jobProfile = jobProfile.replace('%20', ' ')
                location = location.replace('%20', ' ')
                print('Query string location = ' + location)
                print('Query string jobProfile = ' + jobProfile)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if ("city" in i or "country" in i or "state" in i or "location" in i) and "jobProfile" in i:
                        _city = i["city"].lower()
                        _country = i["country"].lower()
                        _state = i["state"].lower()
                        _location = i["location"].lower()
                        _jobProfile = i["jobProfile"].lower()
                        if (((_city is not None and _city and location.lower() in _city)
                        or (_country is not None and _country and location.lower() in _country)
                        or (_state is not None and _state and location.lower() in _state)
                        or (_location is not None and _location and location.lower() in _location))
                                and (_jobProfile is not None and _jobProfile and jobProfile.lower() in _jobProfile)):
                            print("_city" + _city)
                            print("_country" + _country)
                            print("_state" + _state)
                            print("_jobProfile" + _jobProfile)
                            jrs_response.append(i)
            elif None not in (jobProfile, status):
                jobProfile = jobProfile.replace('%20', ' ')
                print('Query string status = ' + status)
                print('Query string jobProfile = ' + jobProfile)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if "jobProfile" in i and "status" in i:
                        _jobProfile = i["jobProfile"].lower()
                        _status = i["status"].lower()
                        if ((_status is not None and _status and status.lower() in _status)
                                and (_jobProfile is not None and _jobProfile and jobProfile.lower() in _jobProfile)):
                            print("_jobProfile" + _jobProfile)
                            print("_department" + _status)
                            jrs_response.append(i)
            elif jobProfile is not None:
                jobProfile = jobProfile.replace('%20', ' ')
                print('Query string jobProfile = ' + jobProfile)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if "jobProfile" in i:
                        _jobProfile = i["jobProfile"].lower()
                        if ((_jobProfile is not None and _jobProfile and jobProfile.lower() in _jobProfile)):
                            print("_jobProfile" + _jobProfile)
                            jrs_response.append(i)
            elif location is not None:
                location = location.replace('%20', ' ')
                print('Query string location = ' + location)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if ("city" in i or "country" in i or "state" in i or "location" in i):
                        _city = i["city"].lower()
                        _country = i["country"].lower()
                        _state = i["state"].lower()
                        _location = i["location"].lower()
                        _status = i["status"].lower()
                        if (((_city is not None and _city and location.lower() in _city)
                        or (_country is not None and _country and location.lower() in _country)
                        or (_state is not None and _state and location.lower() in _state)
                        or (_location is not None and _location and location.lower() in _location))):
                            print("_city" + _city)
                            print("_country" + _country)
                            print("_state" + _state)
                            print("_location" + _location)
                            print("_status" + _status)
                            jrs_response.append(i)
            elif status is not None:
                print('Query string status = ' + status)
                jrs_json = json.loads(jrs_string)
                # print('type(jrs_json = ' + str(type(jrs_json)))
                for i in jrs_json:
                    if "status" in i:
                        _status = i["status"].lower()
                        if ((_status is not None and _status and status.lower() in _status)):
                            print("_status" + _status)
                            jrs_response.append(i)

            if not jrs_string or not jrs_response :
                jrs_response = json.loads(jrs_string)
                response = {}
                response['instances'] = jrs_response
                # print("response - if " + str(response))
                return response
            elif jrs_response:
                # jrs_response_json = jsonify(jrs_response)
                response = {}
                response['instances'] = jrs_response
                # print("response - else " + str(jrs_response))
                # print("response - else " + str(response))
                return response
            else:
                response = {"errorCode": "ER102",
                            "errorMessage": "Could not find the JRs"}
                return response

        except Exception as e:

            response = {"errorCode": "ER101",
                        "errorMessage": e}
            return response
        
@app.get('/common-assets')
def commonassets():
    url = "https://cpd-ibm-cloudpaks.cp4ba-mission-16bf47a9dc965a843455de9f2aef2035-0000.eu-de.containers.appdomain.cloud/bas/dba/studio/platform/common-assets"
    payload={}
    headers = {
    'Authorization': 'Basic Y2VhZG1pbjpjZWFkbWluMTIz'
    }
    response = requests.request("GET", url, headers=headers, data=payload,verify=False)
    return (response.text)

@app.get('/detail')
def detail():
    url = "https://cpd-ibm-cloudpaks.cp4ba-mission-16bf47a9dc965a843455de9f2aef2035-0000.eu-de.containers.appdomain.cloud/bas/dba/studio/platform/common-assets/2051.835cfdf1-4319-4b8d-87a7-60d320258a67/versions?optional_parts=operations%2Corigin"
    payload={}
    headers = {
    'Authorization': 'Basic Y2VhZG1pbjpjZWFkbWluMTIz'
    }
    response = requests.request("GET", url, headers=headers, data=payload,verify=False)
    return (response.text)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
