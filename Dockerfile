FROM dmscid/lewis-depends:latest

# Copying this separately from the rest of lewis allows the
# pip install step to be cached until the requirements change.
# Rebuilding is faster and doesn't require an internet connection.
COPY requirements.txt /lewis/

# Install any missing PIP requirements, clear PIP cache, and delete all compiled Python objects
RUN pip install -r /lewis/requirements.txt && \
    rm -rf /root/.cache/pip/* && \
    find \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' +

# Lewis source is pulled in from current directory (note .dockerignore filters out some files)
COPY . /lewis

# Install lewis in-place and remove compiled Python objects
RUN pip install -e /lewis && \
    rm -rf /root/.cache/pip/* && \
    find \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' +

ENTRYPOINT ["/init.sh", "lewis"]