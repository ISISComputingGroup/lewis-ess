FROM dmscid/lewis-depends:latest

# Lewis source is pulled in from current directory (note .dockerignore filters out some files)
COPY . /lewis

# Install any missing PIP requirements, clear PIP cache, and delete all compiled Python objects
RUN pip install -e /lewis/. && \
    rm -rf /root/.cache/pip/* && \
    find \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' +

ENTRYPOINT ["/init.sh", "lewis"]