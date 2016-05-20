FROM dmscid/epics-pcaspy:latest

ADD . /plankton

RUN pip install -r plankton/requirements.txt && \
    pip install -r plankton/requirements-dev.txt

ENTRYPOINT ["sh", "-lc", "python $@", "python", "/plankton/simulation.py"]

