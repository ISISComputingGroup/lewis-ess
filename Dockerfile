FROM dmscid/epics-pcaspy:latest

COPY requirements*.txt /plankton/

RUN pip install -r plankton/requirements.txt && \
    pip install -r plankton/requirements-dev.txt

COPY . /plankton

ENTRYPOINT ["/init.sh", "/plankton/simulation.py"]

