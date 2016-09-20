FROM dmscid/epics-pcaspy:latest

# Copying these separately from the rest of plankton allows the
# pip install step to be cached until the requirements change.
# Rebuilding is faster and doesn't require an internet connection.
COPY requirements*.txt /plankton/

RUN pip install -r plankton/requirements.txt && \
    pip install -r plankton/requirements-dev.txt

COPY . /plankton

ENTRYPOINT ["/init.sh", "/plankton/simulation.py"]
