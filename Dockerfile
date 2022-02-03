FROM linuxserver/calibre:latest

WORKDIR /app
RUN apt-get -y update \
    && apt -y install python3-pip
COPY . .
RUN pip3 install -r requirements.txt
CMD ["python3", "main.py"]