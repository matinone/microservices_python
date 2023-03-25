# start from the official Python 3.10 image
FROM python:3.11

# set current working directory to /app
WORKDIR /app

# copy only the requirements files (to take advantage of Docker cache)
COPY ./requirements.txt /app/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

CMD ["python3", "consumer.py"]
