FROM ubuntu:18.04

WORKDIR /app
RUN apt-get -y update \
    && apt install -y libjpeg8-dev zlib1g-dev python3-pip python3-pyqt5 wget xdg-utils xz-utils libnss3 \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install --upgrade Pillow
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin
COPY . .
RUN pip3 install -r requirements.txt
CMD ["python3", "main.py"]