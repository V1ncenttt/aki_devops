FROM ubuntu:oracular

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip python3-venv

WORKDIR /aki-system
COPY requirements.txt /aki-system/

RUN python3 -m venv /aki-system
RUN /aki-system/bin/pip3 install -r /aki-system/requirements.txt


COPY main.py /aki-system/
COPY database.py /aki-system/
COPY parser.py /aki-system/
COPY requirements.txt /aki-system/
COPY history.csv /aki-system/
COPY train_model_script.py /aki-system/
COPY expected_columns.json /aki-system/
COPY aki_detection.joblib /aki-system/
COPY pandas_database.py /aki-system/
COPY mllp_listener.py /aki-system/
COPY data_operator.py /aki-system/
COPY model.py /aki-system/
COPY pager.py /aki-system/


EXPOSE 8440
EXPOSE 8441

ENTRYPOINT ["/aki-system/bin/python3", "/aki-system/main.py"]
