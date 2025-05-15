#!/bin/bash

# Name for the image
IMAGE_NAME="ned-ros-noetic"

echo "Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .
