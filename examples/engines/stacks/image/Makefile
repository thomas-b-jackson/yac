# these can be override from the command line as:
# make image yac_version=2.0

yac_version := 2.3
minor_version := 1.gcp
# change 'mygroup' to the a legit group in gitlab
# create a 'yac' project in you group before pushing the image
image_name := gitlab-registry.nordstrom.com/mygroup/yac
pwd := $(shell pwd)
home := $(HOME)
editor := $(EDITOR)
desktop := true
module := examples

# default is to build image then push it to the registry
default: image test push

# 'release' an image by building and pushing the the image with 'latest' label
release: image-release push-release

# rebuild image from scratch (starting from first line in Dockerfile)
scratch:
	docker build --no-cache  \
	-t $(image_name):$(yac_version).$(minor_version) .

ver:
	# create file used by yac primer functions to display the installed version
	echo $(yac_version).$(minor_version) > .ver

	# create the .yac file with the correct yac version and image label
	sed 's/{{YACVER}}/$(yac_version).$(minor_version)/' .yac.tmpl > /tmp/.yac
	sed 's#{{IMAGE_NAME}}#$(image_name)#g' /tmp/.yac > .yac

# run all unit tests
test:
	docker run $(image_name):$(yac_version).$(minor_version) python -m unittest discover yac/tests/stacks/gcp

# build the yac docker image
image-release: ver test

	# build an image with the 'latest' label
	docker build -t $(image_name):latest .

# build the yac docker image
image: ver
	# build an image with the version in the label
	docker build \
	-t $(image_name):$(yac_version).$(minor_version) .

# push the image to docker hub (per version label)
push:
	docker push $(image_name):$(yac_version).$(minor_version)

# push the image to docker hub ('latest' label)
push-release:
	docker push $(image_name):latest

# run the container locally
# notes: - mount the user's home directory for access to aws and k8s credentials
#     	 - set the DESKTOP env to true to signal that yac is running on a developer desktop
#        - nullify the ~/.docker/config.json file so the py-docker client doesn't try to use
#          the user's registry auth preferences (these are n/a inside the container)
run:
	docker run -it -e HOME=$(home) \
				   -e DESKTOP=$(desktop) \
				   -e EDITOR=$(editor) \
	               -v $(home):$(home) \
	               $(image_name):$(yac_version).$(minor_version) bash

# develop your sources via a container
# notes:
#        - mount the local sources on top of the sources in the container
#     	 - mount the user's home directory for access to aws and k8s credentials
#        - set the DESKTOP env to true to signal that yac is running on a developer desktop
#          the user's registry auth preferences (these are n/a inside the container)
#        - use any existing, recent, yac container image (must at least include the same
#            setup.py file so it includes the same python packages)

local:
	docker run -it -e HOME=$(home) \
	               -e DESKTOP=$(desktop) \
				   -e EDITOR=$(editor) \
	               -v $(home):$(home) \
	               -v $(pwd)/stack.py:/usr/local/yac/yac/lib/stacks/gcp/stack.py \
	               -v $(pwd)/stack.json:/usr/local/yac/yac/schema/stacks/gcp/stack.json \
	               -v $(pwd)/engines.json:/usr/local/yac/yac/configs/engines.json \
	               $(image_name):$(yac_version).$(minor_version) bash
