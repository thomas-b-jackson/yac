# these can be override from the command line as:
# make image yac_base_version=3.7.1.1

# base version should correspond to the version of python we are using for base image
yac_base_version := 3.7.2
base_image_name := nordstromsets/yac_base
pwd := $(shell pwd)
home := $(HOME)
editor := $(EDITOR)
desktop := true

clean:
	docker rmi \
	-f $(base_image_name):$(yac_base_version)

# default is to build image then push it to the registry
default: image push

# build the yac container base image
image:
	docker build \
	-t $(base_image_name):$(yac_base_version) .

# push the image to docker hub (per version label)
push:
	docker push $(base_image_name):$(yac_base_version)

# run the container locally
# notes: - mount the user's home directory for access to aws and k8s credentials
#     	 - set the DESKTOP env to true to signal that yac is running on a developer desktop
#        - nullify the ~/.docker/config.json file so the py-docker client doesn't try to use
#          the user's registry auth preferences (these are n/a inside the container)
run:
	docker run -it -e HOME=$(home) \
				   -e EDITOR=$(editor) \
	               -v $(home):$(home) \
	               -v /tmp:/tmp \
	               -v /dev/null:$(home)/.docker/config.json \
	               $(base_image_name):$(yac_base_version) bash
