#!/bin/bash
# Linux için Docker Container Çalıştırma Script'i

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ROS2 Docker Container - Linux${NC}"
echo -e "${BLUE}========================================${NC}"

# X11 forwarding için izin ver
echo -e "\n${GREEN}1. X11 forwarding izni veriliyor...${NC}"
xhost +local:docker

# Docker kontrolü
echo -e "\n${GREEN}2. Docker kontrolü...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker çalışmıyor! Lütfen Docker'ı başlatın.${NC}"
    exit 1
fi
echo "✅ Docker çalışıyor"

# Container'ı çalıştır
echo -e "\n${GREEN}3. Container başlatılıyor...${NC}"

docker run -it --rm \
    --name ros2_moveit_container \
    --privileged \
    --net=host \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e ROS_DOMAIN_ID=42 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd)/../src:/root/colcon_ws/src:rw \
    -v /dev/dri:/dev/dri \
    ros2_colcon_workspace:humble \
    bash

echo -e "\n${GREEN}Container kapatıldı.${NC}"
xhost -local:docker
