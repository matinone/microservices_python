import json
import pika


def upload_video(file_to_upload, fs, channel, access):
    try:
        file_id = fs.put(file_to_upload)
    except:
        return "Internal server error", 500

    # put a message in the queue so the downstream converter service
    # can then consume that message
    message = {
        "video_file_id": str(file_id),
        "mp3_file_id": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                # persist the messages in the queue in the event of a pod crash/restart
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except:
        # delete the file from the DB, because if the message
        # fails to be sent to the queue, the file will never be
        # processed and we would end up we lots of stalled files
        fs.delete(file_id)
        return "Internal server error", 500
