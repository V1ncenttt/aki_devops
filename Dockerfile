FROM ubuntu:oracular

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip python3-venv

WORKDIR /aki-system
COPY requirements.txt /aki-system/

RUN python3 -m venv /aki-system
RUN /aki-system/bin/pip3 install -r /aki-system/requirements.txt

COPY main.py /aki-system/
COPY src/database.py /aki-system/src/
COPY src/parser.py /aki-system/src/
COPY src/pandas_database.py /aki-system/src/
COPY src/mllp_listener.py /aki-system/src/
COPY src/data_operator.py /aki-system/src
COPY src/model.py /aki-system/src/
COPY src/mysql_database.py /aki-system/src/
COPY src/pager.py /aki-system/src/
COPY src/database_populator.py /aki-system/src/
COPY requirements.txt /aki-system/
COPY data/history.csv /aki-system/data/
COPY aki_detection.joblib /aki-system/

EXPOSE 8440
EXPOSE 8441

ENTRYPOINT ["/aki-system/bin/python3", "/aki-system/main.py"]
