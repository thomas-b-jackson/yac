# Base image has python 3, python packages, and all
# supporting cli utilities (kubectl, artillery, etc)
FROM nordstromsets/yac_base:3.7.2

MAINTAINER TECH_DOT_Support@nordstrom.com

# define install dir
ENV YAC_INSTALL  /usr/local/yac

# Create install directory and make it writeable to all
RUN mkdir -p  $YAC_INSTALL && \
    chmod -R 777 $YAC_INSTALL

# Add sources
ADD yac/         $YAC_INSTALL/yac/
ADD examples/    $YAC_INSTALL/examples/

# Add the yac cli shell script
ADD yac/bin/yac  /usr/bin/yac

# Set path so yac shell script can find yac sources
ENV PYTHONPATH=$YAC_INSTALL

# Disable the creation of pyc files in __pycache__ directories.
# This prevent runners from cleaning builds up after themselves.
ENV PYTHONDONTWRITEBYTECODE=true

WORKDIR $YAC_INSTALL

# switch to yac user
USER yac
