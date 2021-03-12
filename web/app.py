from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import spacy

app = Flask(__name__)
bcrypt = Bcrypt(app)
api = Api(app)

mongoClient = MongoClient("mongodb://db:27017")
db = mongoClient.SimilarityDB
users = db['Users']

class mongoOps:
    def findOne(filter = {}):
        return users.find_one(filter)
    def find(filter = {}):
        return users.find(filter)
    def insertOne(data):
        return users.insert_one(data)
    def insertMany(data):
        return users.insert(data)
    def updateOne(filter,data):
        return users.update_one(filter,{"$set":data})
    def updateMany(filter,data):
        return users.update(filter,{"$set":data})
    def deleteOne(filter,data):
        return users.delete_one(filter)
    def deleteMany(filter,data):
        return users.delete_many(filter)

def UserExists(username):
    return mongoOps.findOne({"Username":username})

def UserValidity(data):
    findresp = UserExists(data["Username"])
    if findresp is None:
        return {
            "status":302,
            "Message":"User is not registered"
        }
    findobj = mongoOps.findOne({"Username":data["Username"]})
    if bcrypt.check_password_hash(findobj["Password"],data["Password"].encode('utf8')):
        return True
    else:
        return False

def numOfTokens(username):
    return mongoOps.findOne({"Username":username})["Tokens"]

class Register(Resource):
    def post(self):
        data = request.get_json()
        findresp = UserExists(data["Username"])
        if findresp is not None:
            return {
                "status":302,
                "Message":"Username already present"
            }
        data["Password"] = bcrypt.generate_password_hash(data["Password"].encode('utf8'))
        data["Tokens"] = 6
        insertresp = mongoOps.insertOne(data)
        if insertresp.inserted_id is not None:
            return {
                "status":200,
                "Message":"Succesfully Registered"
            }
        else:
            return {
                "status":500,
                "Message":"Not Registered"
            }

class Refill(Resource):
    def post(self):
        data = request.get_json()
        isUserValid = UserValidity(data)
        if isUserValid:
            tokens = numOfTokens(data["Username"])
            if tokens > 10 :
                return {
                    "status":302,
                    "Message":"You have enough tokens in your bucket"
                }
            else:
                mongoOps.updateOne({"Username":data["Username"]},{"Tokens":tokens + data["Tokens"]})
                findobj1 = mongoOps.findOne({"Username":data["Username"]})
                return {
                    "Username" : findobj1["Username"],
                    "OldTokens": tokens,
                    "LatestToken":findobj1["Tokens"]
                }
        else:
            return {
                "status":500,
                "Message":"Unable to refill"
            }

class Detect(Resource):
    def post(self):
        data = request.get_json()
        txt1=data["Text1"]
        txt2=data["Text2"]
        isUserValid = UserValidity(data)
        if isUserValid:
            if numOfTokens(data["Username"]) <= 1:
                return {
                    "status":303,
                    "Message":"Out of tokens, please refill"
                }
            else:
                nlp = spacy.load('en_core_web_sm')
                txt1 = nlp(txt1)
                txt2 = nlp(txt2)

                ratio = txt1.similarity(txt2)
                currentTokens = numOfTokens(data["Username"])
                mongoOps.updateOne({"Username":data["Username"]},{"Tokens":currentTokens-1})
                return {
                    "status":200,
                    "Simmilarity":ratio,
                    "Message":"Simmilarity calculated Succesfully"
                }
        else:
            {
                "Status":304,
                "Message":"Password is invalid"
            }

api.add_resource(Register,"/register")
api.add_resource(Detect,"/detect")
api.add_resource(Refill,"/refill")

app.run(host="0.0.0.0")
