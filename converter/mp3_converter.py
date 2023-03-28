import os
import json
import tempfile

import pika
from bson.objectid import ObjectId
from moviepy.editor import VideoFileClip


def start_conversion(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # get video contents from MongoDB and put them in a temp file
    video_content = fs_videos.get(ObjectId(message["video_file_id"]))
    temp_file = tempfile.NamedTemporaryFile()
    temp_file.write(video_content.read())

    # create audio from video file
    audio = VideoFileClip(temp_file.name).audio
    temp_file.close()   # automatically deletes the file as well

    # write audio to a temp file
    temp_file_path = tempfile.gettempdir() + f"/{message['video_file_id']}.mp3"
    audio.write_audiofile(temp_file_path)

    # store audio in MongoDB
    file_handler = open(temp_file_path, "rb")
    audio_data = file_handler.read()
    file_id = fs_mp3s.put(audio_data)
    # not automatically deleted because it wasn't created using the tempfile module
    file_handler.close()
    os.remove(temp_file_path)

    # update message and send it to the MP3 queue
    message["mp3_file_id"] = str(file_id)
    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                # persist the messages in the queue in the event of a pod crash/restart
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except Exception as e:
        print(e)
        # delete the file from the MongoDB, because it will never be processed
        # if the message isn't sent to the queue
        fs_mp3s.delete(file_id)
        return "Failed to publish message"
