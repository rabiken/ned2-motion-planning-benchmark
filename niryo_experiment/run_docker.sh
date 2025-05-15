#!/bin/bash

# Image name
IMAGE_NAME="ned-ros-noetic"

# Container name
CONTAINER_NAME="ned-ros-container"

# # Connection via WiFi
# ROBOT_IP=10.10.10.10
# HOST_IP=10.10.10.62

# # Connection via Ethernet
# ROBOT_IP=169.254.200.200
# HOST_IP=169.254.133.162

# # Docker simulation (WITHOUT real robot)
# ROBOT_IP=172.17.0.1    # This is the IP of the host machine in the Docker network
# HOST_IP=172.17.0.1   # This is the IP of the host machine in the Docker network

# Docker simulation (without robot hardware)
ROBOT_IP=localhost
HOST_IP=localhost

echo "Using ROS_MASTER_URI=http://$ROBOT_IP:11311 and ROS_IP=$HOST_IP"

TEST_SCENE_DIR=test_scenes

xhost +local:docker # Allow local docker connections to X server (for RViz GUI)

docker run -it --rm \
    --network host \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e ROS_MASTER_URI="http://$ROBOT_IP:11311" \
    -e ROS_IP="$HOST_IP" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ./$TEST_SCENE_DIR:/root/$TEST_SCENE_DIR \
    --name $CONTAINER_NAME \
    $IMAGE_NAME

xhost -local:docker # Revoke local docker connections to X server
