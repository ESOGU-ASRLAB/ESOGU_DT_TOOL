# ROS2 Humble + Gazebo + MoveIt2 Docker Container
FROM osrf/ros:humble-desktop-full

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# Set up display for GUI applications
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

# Install essential tools and dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    # ROS2 packages
    ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-gazebo-ros-pkgs \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-controller-manager \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-joint-state-publisher-gui \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-ur \
    ros-${ROS_DISTRO}-ur-description \
    ros-${ROS_DISTRO}-ur-msgs \
    ros-${ROS_DISTRO}-ur-dashboard-msgs \
    # GUI support
    x11-apps \
    mesa-utils \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    # Additional utilities
    nano \
    vim \
    tmux \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    numpy \
    transforms3d \
    pymodbus

# Create workspace directory
WORKDIR /root/colcon_ws

# Copy the entire directory contents as src
COPY . /root/colcon_ws/src/

# Initialize rosdep (if not already done)
RUN rosdep update || true

# Install dependencies from packages
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    rosdep install --from-paths src --ignore-src -r -y || true

# Build the workspace
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source ROS2 and workspace automatically
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source /root/colcon_ws/install/setup.bash" >> /root/.bashrc && \
    echo "export ROS_DOMAIN_ID=42" >> /root/.bashrc && \
    echo "echo '🤖 ROS2 Humble Workspace Ready!'" >> /root/.bashrc && \
    echo "echo '📦 Packages: MoveIt2, Gazebo, UR Robot, Custom packages'" >> /root/.bashrc

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
source /opt/ros/${ROS_DISTRO}/setup.bash\n\
source /root/colcon_ws/install/setup.bash\n\
exec "$@"' > /ros_entrypoint.sh && \
    chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
