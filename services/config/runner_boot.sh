#!/bin/bash

# *****************************************************************
# For booting a new yac runner host.
# *****************************************************************

# generate format date and time
echo_with_time () {
  echo $(date "+%m-%d-%Y %H:%M:%S") $1
}

# log stdout and stderr from this script to a boot log
# You can troubleshoot boot issues by inspecting this log file.
logfile=/tmp/boot.log
exec > $logfile 2>&1

# set time zone to Pacific
sudo timedatectl set-timezone America/Los_Angeles

# install the runner correspoonding the the GitLab version specified
# in the service
sudo apt-get -y install gitlab-runner={{yac-ref:gitlab-version}}

# add the ubuntu and gitlab-runner users to the docker group such that they can make
# docker engine calls w/out sudo
sudo usermod -aG docker ubuntu
sudo usermod -aG docker gitlab-runner

# create the cache directories under the gitlab-runner home that yac
# writes to
sudo touch /home/gitlab-runner/.kubeloginrc.yaml

sudo mkdir -p /home/gitlab-runner/.yac \
              /home/gitlab-runner/.cache \
              /home/gitlab-runner/.kube \
              /home/gitlab-runner/.aws
sudo chown gitlab-runner:gitlab-runner \
              /home/gitlab-runner/.yac \
              /home/gitlab-runner/.cache \
              /home/gitlab-runner/.kube \
              /home/gitlab-runner/.aws \
              /home/gitlab-runner/.kubeloginrc.yaml
sudo chmod -R 777 /home/gitlab-runner/.yac \
              /home/gitlab-runner/.cache \
              /home/gitlab-runner/.kube \
              /home/gitlab-runner/.aws \
              /home/gitlab-runner/.kubeloginrc.yaml

# default write permissions on files cloned by runner
sudo echo "umask 000" >> /home/gitlab-runner/.profile

# fire up the runner, in shell mode
sudo gitlab-runner register -n \
  --url {{yac-ref:gitlab-url}}/ \
  --registration-token {{yac-ref:registration-token}} \
  --executor shell \
  --tag-list yac \
  --description "yac gitlab runner"

echo_with_time "startup complete"