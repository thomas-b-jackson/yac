FROM nordstromsets/yac:2.3.1

MAINTAINER my_team@nordstrom.com

# Switch to root user
USER root

# install the GCP cloudmanager client libraries
# RUN pip install sumpin

# Add my gcp stack engine source
ENV MODULE_PATH=$YAC_INSTALL/yac/lib/stacks/gcp/stack.py
ADD stack.py $MODULE_PATH

# Make the gcp dir a module
RUN touch $YAC_INSTALL/yac/lib/stacks/gcp/__init__.py

# Add tests from my gcp stack engine
ADD tests/*  $YAC_INSTALL/yac/tests/stacks/gcp/

# Add the schema that will validate stack stanzas that leverage my provider
ADD stack.json $YAC_INSTALL/yac/schema/stacks/gcp/stack.json

# Register the engine
RUN ./yac/bin/engine stack gcp-cloudmanager $MODULE_PATH GCPStack

# Add the file that communicates the yac version via the primers
ADD .ver $YAC_INSTALL/yac/cli/.ver

# switch back to yac user
USER yac
