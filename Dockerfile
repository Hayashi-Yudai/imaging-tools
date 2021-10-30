FROM python:3.9.5

ARG UID=1000
RUN useradd -m -u ${UID} docker

WORKDIR /home/docker/

COPY requirements.txt .
COPY thorlabs_tsi_camera_python_sdk_package.zip .
COPY bin/64_lib/*.so /usr/local/lib/

RUN pip install -r requirements.txt \
  && pip install thorlabs_tsi_camera_python_sdk_package.zip \
  && rm -rf thorlabs_tsi_camera_python_sdk_package.zip
RUN ldconfig -v \
  && mkdir -p /etc/udev

COPY bin/usb.rules /etc/udev/rules.d

USER ${UID}
