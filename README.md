# Microservices with Python

Microservices architecture for learning purposes, using Kubernetes, RabbitMQ, Python (Flask), MongoDB and MySQL. It is a modified version of the implementation from [this FreeCodeCamp YouTube course](https://youtu.be/hmkF77F9TLw).

## Architecture

The application converts videos into MP3 files.

![Top Level Architecture](diagram.png "Top Level Architecture")
(diagram taken from the video mentioned above)

1. The user sends a request to the API gateway to log in to the application. The API gateway sends an HTTP request to the Auth service, which checks the credentials in a MySQL database ("auth DB" in the diagram) and returns an access token.
2. The user uploads a video to be converted. The request hits the API gateway, which uploads the video to MongoDB ("storage DB" in the diagram) and places a message in the RabbitMQ queue, letting the downstream services know that there is a video to be processed.
3. The Video-to-MP3 service consumes messages from the queue, getting from there the ID of the video to pull from MongoDB, in order to convert it to MP3 and store it again in MongoDB. It then puts a message in the RabbitMQ queue, informing that the conversion is done.
4. The notification service consumes those messages and sends an email to the client, informing that the conversion is ready.
5. The user then requests to the API gateway the converted file.

## Setup

Some of the existing Kubernetes manifests must be updated before running the application.

- Update the deployment YAML files in the `auth`, `converter`, `gateway` and `notification` to use images from your Docker Hub repositories. This requires building each image and pushing them to Docker Hub.
- Create a `video` and an `mp3` queue in RabbitMQ (once the service is started). To do that, access the RabbitMQ management plugin (the URL/port can be obtained running `$ minikube service rabbitmq`).

## Run the App

1. Start the minikube cluster.
   ```
   $ minikube start
   ```
2. For each service, apply all the files in the Kubernetes directory.
   ```
   $ kubectl apply -f <service>/kubernetes
   ```
3. Once done using the application, stop and delete everything.
   ```
   $ minikube delete --all
   ```
