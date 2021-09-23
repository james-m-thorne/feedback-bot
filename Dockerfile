FROM python:3.9-slim-buster

LABEL owner="james.thorne@xero.com"
LABEL product="SRE Platform"
LABEL portfolio="ps"
LABEL maintainer="james.thorne@xero.com"

COPY . /app
WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install -r ./requirements.txt

ENTRYPOINT ["python3", "src/app.py"]
