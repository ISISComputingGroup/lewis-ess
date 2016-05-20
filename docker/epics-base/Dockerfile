FROM alpine:latest

# Runtime dependencies
RUN apk --no-cache add \
    libstdc++ \
    readline

# Get EPICS source
RUN mkdir /EPICS \
    && cd /EPICS \
    && wget http://www.aps.anl.gov/epics/download/base/baseR3.14.12.5.tar.gz -O EPICS.tar.gz \
    && tar xzf EPICS.tar.gz \
    && mv base-*/ base/ \
    && rm EPICS.tar.gz

# Environment setup
RUN PROFILE_SCRIPT=/etc/profile.d/epics.sh \
    && echo "ETH0_IP=\`ifconfig eth0 | awk '/inet addr/{print substr(\$2,6)}'\`" > $PROFILE_SCRIPT \
    && echo "export EPICS_HOST_ARCH=linux-x86_64" >> $PROFILE_SCRIPT \
    && echo "export EPICS_BASE=/EPICS/base" >> $PROFILE_SCRIPT \
    && echo "export EPICS_CA_ADDR_LIST=localhost" >> $PROFILE_SCRIPT \
    && echo "export EPICS_CA_AUTO_ADDR_LIST=NO" >> $PROFILE_SCRIPT \
    && echo "export EPICS_CAS_INTF_ADDR_LIST=\"localhost \$ETH0_IP\"" >> $PROFILE_SCRIPT \
    && echo "export PATH=/EPICS/base/bin/linux-x86_64:\${PATH}" >> $PROFILE_SCRIPT 

# Build and cleanup
RUN apk --no-cache add --virtual build-dependencies g++ make perl-dev readline-dev \
    && cd /EPICS/base \
    && make CFLAGS="-DIPPORT_USERRESERVED=5000 -fPIC" CXXFLAGS="-DIPPORT_USERRESERVED=5000 -fPIC" \
    && make clean \
    && apk del build-dependencies

