FROM ubuntu:oracular

# Environment variables
ENV MLLP_ADDRESS=8440
ENV PAGER_ADDRESS=8441 

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip python3-venv

COPY main.py /aki-system/
COPY parser.py /aki-system/
COPY controller.py /aki-system/
COPY model.py /aki-system/
WORKDIR /aki-system

RUN python3 -m venv /aki-system

EXPOSE 8440
EXPOSE 8441

ENTRYPOINT ["/aki-system/bin/python3", "/aki-system/main.py"]
