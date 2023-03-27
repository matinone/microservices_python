import json
import gridfs

import pika
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

from auth_service import auth_login, validate_token
from storage import upload_video

server = Flask(__name__)

mongo_video = PyMongo(
    server,
    uri="mongodb://mongo-service:27017/videos",
)

mongo_mp3 = PyMongo(
    server,
    uri="mongodb://mongo-service:27017/mp3s",
)

# for storing and retrieving files that exceed the BSON-document size limit of 16 MB
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

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
        err = upload_video(file_to_upload, fs_videos, channel, access, server)

        if err:
            return err
    
    return "Success", 200


@server.route("/download", methods=["GET"])
def download():
    access, err = validate_token(request)
    if err:
        return err

    access = json.loads(access)
    if not access.get("admin"):
        return "Not authorized", 403

    file_id_str = request.args.get("fid")
    if not file_id_str:
        return "Missing file ID", 400

    try:
        mp3_file = fs_mp3s.get(ObjectId(file_id_str))
        return send_file(mp3_file, download_name=f"{file_id_str}.mp3")
    except Exception as e:
        server.logger.info(e)
        return "Internal server error", 500


if __name__ == "__main__":
    # host="0.0.0.0" to make it externally visible
    # otherwise it would be accessible only from localhost,
    # and not from a network when running it using Docker
    server.run(host="0.0.0.0", port=8080, debug=True)
