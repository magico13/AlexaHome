FROM python:3-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git build-essential

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install git+https://github.com/magico13/pycarwings2.git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=/usr/src/app/CoreAlexa.py

COPY ./container/* ./

CMD ["flask", "run"]
