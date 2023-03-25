import os
from datetime import datetime, timedelta

import jwt
from flask import Flask, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization    # grabs Authentication header
    if not auth:
        return "Missing credentials", 401

    # check DB for username and password
    # (passwords shouldn't be stored in plaint text :) )
    cur = mysql.connection.cursor()
    # this is vulnerable to SQL injection
    query = f"SELECT email, password FROM users WHERE email='{auth.username}'"
    res = cur.execute(query)
    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "Invalid credentials", 401

        return create_jwt(auth.username, os.environ.get("JWT_SECRET"), True)

    return "Invalid credentials", 401


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]
    if not encoded_jwt:
        return "Missing credentials", 401

    encoded_jwt = encoded_jwt.split(" ")[1]
    try:
        decoded_jwt = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithm="HS256"
        )
    except:
        return "Not authorized", 403

    return decoded_jwt, 200


def create_jwt(username, secret, admin=False):
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "admin": admin,
    }

    return jwt.encode(payload, secret, algorithm="HS256")


if __name__ == "__main__":
    # host="0.0.0.0" to make it externally visible
    # otherwise it would be accessible only from localhost,
    # and not from a network when running it using Docker
    server.run(host="0.0.0.0", port=5000)
