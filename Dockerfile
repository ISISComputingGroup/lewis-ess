FROM dmscid/lewis-depends:latest

# Copying these separately from the rest of lewis allows the
# pip install step to be cached until the requirements change.
# Rebuilding is faster and doesn't require an internet connection.
COPY requirements*.txt /lewis/

# Install any missing PIP requirements, clear PIP cache, and delete all compiled Python objects
RUN pip install -r lewis/requirements.txt && \
    pip install -r lewis/requirements-dev.txt && \
    rm -rf /root/.cache/pip/* && \
    find \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' +

# lewis source is pulled in from current directory (note .dockerignore filters out some files)
COPY . /lewis

ENTRYPOINT ["/init.sh", "/lewis/lewis.py"]

