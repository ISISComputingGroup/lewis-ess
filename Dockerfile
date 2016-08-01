FROM dmscid/epics-pcaspy:latest

COPY . /plankton

RUN pip install -r plankton/requirements.txt && \
    pip install -r plankton/requirements-dev.txt

ENTRYPOINT ["/init.sh", "/plankton/simulation.py"]

