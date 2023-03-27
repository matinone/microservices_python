import os
import sys
import pika

from notification import send_notification

def main():
    # RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    # callback defined insided of main() so it has access to fs_videos and fs_mp3s
    def consume_callback(channel, method, properties, body):
        err = send_notification(body)
        if err:
            channel.basic_nack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)


    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"),
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
