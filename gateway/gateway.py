import os
import json
import gridfs

import pika
from flask import Flask, request
from flask_pymongo import PyMongo

from auth_service import auth_login, validate_token
from storage import upload_video

server = Flask(__name__)
server.config["MONGO_URI"] = "mongodb://mongo-service:27017/videos"

mongo = PyMongo(server)

# for storing and retrieving files that exceed the BSON-document size limit of 16 MB
fs = gridfs.GridFS(mongo.db)

# RabbitMQ connection (synchronous)
# parameters based on https://pika.readthedocs.io/en/stable/examples/heartbeat_and_blocked_timeouts.html
rabbitmq_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq", heartbeat=600, blocked_connection_timeout=300)
)
channel = rabbitmq_connection.channel()

@server.route("/login", methods=["POST"])
def login():
    # synchronous communication with the auth service
    token, err = auth_login(request)
    if not err:
        return token

    return err


@server.route("/upload", methods=["POST"])
def upload():
    # synchronous communication with the auth service
    access, err = validate_token(request)
    if err:
        return err

    access = json.loads(access)
    if not access.get("admin"):
        return "Not authorized", 403

    if len(request.files) != 1:
        return "Exactly 1 file required", 400

    for _, file_to_upload in request.files.items():
        # upload file to MongoDB +
        # async communication with the converter service
        err = upload_video(file_to_upload, fs, channel, access, server)

        if err:
            return err
    
    return "Success", 200


@server.route("/download", methods=["GET"])
def download():
    pass


if __name__ == "__main__":
    # host="0.0.0.0" to make it externally visible
    # otherwise it would be accessible only from localhost,
    # and not from a network when running it using Docker
    server.run(host="0.0.0.0", port=8080, debug=True)
