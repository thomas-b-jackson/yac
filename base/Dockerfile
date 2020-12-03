FROM python:3.7

MAINTAINER TECH_DOT_Support@nordstrom.com

# define install dir
ENV YAC_INSTALL  /usr/local/yac

# make sure pip is up to date
RUN pip install --upgrade pip

# Install vi and nano we have at least some editing capability inside container
RUN apt-get update --quiet
RUN apt-get install vim -y
RUN apt-get install nano -y
RUN apt-get install unzip -y

# create a local user called 'yac' with sudo privies
# give it uid 10001 so it can run in our k8s clusters
RUN useradd -c 'local user' -m -d /home/yac -s /bin/bash -u 10001 yac
RUN usermod -aG sudo yac

RUN apt-get -y install awscli

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# install artillery via node.js

RUN curl -sL https://deb.nodesource.com/setup_10.x > /tmp/tmp.sh
RUN chmod 777 /tmp/tmp.sh
RUN /tmp/tmp.sh
RUN apt-get install -y nodejs

# Install artillery
# Notes:
#  using '--ignore-scripts jsonpath' because of deprecated dependancy (nomnom)
#  using specific version of artillery to work around a bug in v1.6.0-24 involving json captures in test flows.
RUN npm install --ignore-scripts jsonpath -g artillery@1.6.0-23

# install kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.10.3/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin/kubectl

# install packer
RUN wget https://releases.hashicorp.com/packer/1.2.5/packer_1.2.5_linux_amd64.zip

RUN unzip packer_1.2.5_linux_amd64.zip -d packer
RUN mv packer/packer /usr/local/bin/.
