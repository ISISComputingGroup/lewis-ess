FROM dmscid/plankton-depends:latest

# Copying these separately from the rest of plankton allows the
# pip install step to be cached until the requirements change.
# Rebuilding is faster and doesn't require an internet connection.
COPY requirements*.txt /plankton/

# Install any missing PIP requirements, clear PIP cache, and delete all compiled Python objects
RUN pip install -r plankton/requirements.txt && \
    pip install -r plankton/requirements-dev.txt && \
    rm -rf /root/.cache/pip/* && \
    find \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' +

# Plankton source is pulled in from current directory (note .dockerignore filters out some files)
COPY . /plankton

ENTRYPOINT ["/init.sh", "/plankton/bin/plankton"]

