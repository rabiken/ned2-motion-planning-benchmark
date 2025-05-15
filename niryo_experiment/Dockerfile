# Base image with Ubuntu 20.04 and ROS Noetic
FROM ros:noetic-ros-base-focal

# Avoid user interaction during install
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    python3-numpy \
    python3-yaml \
    python3-pil \
    python3-pymodbus \
    libasio-dev \
    nlohmann-json3-dev \
    curl \
    wget \
    build-essential \
    python3-catkin-tools \
    ros-noetic-catkin \
    ros-noetic-joy \
    ros-noetic-tf2-web-republisher \
    ros-noetic-rosbridge-server \
    ros-noetic-moveit \
    ros-noetic-moveit-msgs \
    ros-noetic-moveit-ros-move-group \
    ros-noetic-moveit-kinematics \
    ros-noetic-moveit-planners-ompl \
    ros-noetic-moveit-ros-visualization \
    ros-noetic-moveit-ros-benchmarks \
    ros-noetic-moveit-ros-warehouse \
    ros-noetic-warehouse-ros-mongo \
    ros-noetic-moveit-fake-controller-manager \
    ros-noetic-effort-controllers \
    ros-noetic-ros-controllers \
    && rm -rf /var/lib/apt/lists/*

# Set up workspace
RUN mkdir -p /root/catkin_ws/src
WORKDIR /root/catkin_ws/src

# Clone the Niryo Ned ROS packages
RUN git clone https://github.com/NiryoRobotics/ned_ros.git

# Initialize rosdep
# Add ROS Noetic sources manually and install missing dependencies
RUN apt-get update && \
    apt-get install -y \
    catkin-lint \
    ros-noetic-roslint \
    ros-noetic-joint-state-publisher \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher-gui \
    ros-noetic-code-coverage \
    ros-noetic-gazebo-ros-control \
    ros-noetic-gazebo-ros \
    sqlite3 \
    python3-yaml \
    python3-numpy \
    python3-pil \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Build the workspace for Ned2 simulation
WORKDIR /root/catkin_ws
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin_make"

# Build our custom workspace for Comparative Study
WORKDIR /root
RUN mkdir -p /root/ws_compare_alg/src
WORKDIR /root/ws_compare_alg
COPY ./src /root/ws_compare_alg/src
RUN /bin/bash -c "source /root/catkin_ws/devel/setup.bash && catkin_make"

# Source ROS workspace by default
RUN echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
RUN echo "source /root/catkin_ws/devel/setup.bash" >> ~/.bashrc
RUN echo "source /root/ws_compare_alg/devel/setup.bash" >> ~/.bashrc

WORKDIR /root

CMD ["bash"]
