FROM qgis/qgis:latest AS base
LABEL authors="chen"

RUN apt-get update && apt-get install -y python3 python3-pip python3-numpy  python3-pyproj python3-pandas python3-pydantic xvfb wget unzip

ENV QGIS_PREFIX_PATH=/usr
ENV QT_QPA_PLATFORM=offscreen
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

FROM base AS setup

WORKDIR /app
ENV SUBMODULE_DIRECTORY=/app/submodules

COPY mi_sync/ $SUBMODULE_DIRECTORY/mi_sync
COPY midf/ $SUBMODULE_DIRECTORY/midf
COPY svaguely/ $SUBMODULE_DIRECTORY/svaguely
COPY caddy/ $SUBMODULE_DIRECTORY/caddy

COPY mi_companion/requirements.txt requirements.txt
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

FROM setup AS display

RUN Xvfb :1 -screen 0 1024x768x16 &> xvfb.log  &
RUN ps aux | grep X
RUN DISPLAY=:1.0
RUN export DISPLAY


FROM setup AS run

#RUN python create_resourcefiles.py
COPY mi_companion/ mi_companion/
COPY tests/ tests/

#ENTRYPOINT ["pytest","--cov","mi_companion","--cov-report","term-missing","tests"]
ENTRYPOINT ["pytest", "tests"]
