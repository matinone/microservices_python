import os
import sys

import gridfs
import pika
from pymongo import MongoClient

from mp3_converter import start_conversion


def consume_callback(channel, method, properties, body):
    err = start_conversion(body, fs_videos, fs_mp3s, channel)
    if err:
        channel.basic_nack(delivery_tag=method.delivery_tag)
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    # MongoDB
    client = MongoClient("host.minikube.internal", 27017)
    db_videos = client.videos
    db_mp3s = client.mp3s

    # GridFS
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=consume_callback,
    )

    print("Waiting for messages...")
    print("To exit press CTRL + C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
