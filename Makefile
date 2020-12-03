# these can be override from the command line as:
# make image yac_version=2.0

yac_version := 2.4
minor_version := 2
image_name := nordstromsets/yac
pwd := $(shell pwd)
home := $(HOME)
editor := $(EDITOR)
desktop := true
module := examples

# default is to build image then push it to the registry
default: image push

# 'release' an image by building and pushing the the image with 'latest' label
release: image-release push-release

clean:
	find . -name "*.pyc" -exec rm -f {} \;

# rebuild image from scratch (starting from first line in Dockerfile)
scratch:
	docker build --no-cache  \
	-t $(image_name):$(yac_version).$(minor_version) .

ver:
	# create file used by yac primer functions to display the installed version
	echo $(yac_version).$(minor_version) > yac/cli/.ver

	# create the .yac file with the correct yac version and image name
	sed 's/{{YACVER}}/$(yac_version).$(minor_version)/' yac/.yac.tmpl > /tmp/.yac
	sed 's#{{IMAGE_NAME}}#$(image_name)#g' /tmp/.yac > .yac

# build an image with the 'latest' label
image-release: ver

	docker build \
	-t $(image_name):latest .

# build the yac container image
image: ver
	# build an image with the version in the label
	docker build \
	-t $(image_name):$(yac_version).$(minor_version) .

	# run unit tests
	docker run $(image_name):$(yac_version).$(minor_version) python -m unittest discover yac/tests

	@echo "image successfully built and unit tests passed"

# push the image to docker hub (per version label)
push:
	docker push $(image_name):$(yac_version).$(minor_version)

# push the image to docker hub ('latest' label)
push-release:
	docker push $(image_name):latest

# develop yac via a container
# notes: - mount the user's home directory for access to aws and k8s credentials
#        - set the DESKTOP env to true to signal that yac is running on a developer desktop
#        - nullify the ~/.docker/config.json file so the py-docker client doesn't try to use
#          the user's registry auth preferences (these are n/a inside the container)
#        - mount a minimal .bash_profile under home that provides a git-friendly prompt
#        - use the yac container image associated with current major/minor version
#        - mount the local ./yac directory on top of the ./yac directory in the container
#          such that the yac exec uses local yac sources
local:
	docker run -it -e HOME=$(home) \
	               -e DESKTOP=$(desktop) \
				   -e EDITOR=$(editor) \
	               -v $(home):$(home) \
	               -v /tmp:/tmp \
	               -v /dev/null:$(home)/.docker/config.json \
	               -v $(pwd)/yac/config/.bash_profile:$(home)/.bash_profile \
	               -v $(pwd):/usr/local/yac \
	               $(image_name):$(yac_version).$(minor_version) bash
