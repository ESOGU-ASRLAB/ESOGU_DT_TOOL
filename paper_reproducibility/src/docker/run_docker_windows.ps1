#!/bin/bash
# Windows için Docker Container Çalıştırma Script'i
# PowerShell'de çalıştırılmalı

# Renk kodları
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ROS2 Docker Container - Windows${NC}"
echo -e "${BLUE}========================================${NC}"

# VcXsrv kontrolü
echo -e "\n${GREEN}1. VcXsrv X Server kontrolü...${NC}"
echo "VcXsrv çalışıyor olmalı!"
echo "Eğer yüklü değilse: https://sourceforge.net/projects/vcxsrv/"
echo ""
echo "VcXsrv ayarları:"
echo "  ✓ Multiple windows"
echo "  ✓ Display number: 0"
echo "  ✓ Start no client"
echo "  ✓ Disable access control (ÖNEMLI!)"
echo ""

# DISPLAY ayarı
$WSL_HOST = (wsl hostname -I).Trim()
$env:DISPLAY = "${WSL_HOST}:0.0"

echo -e "${GREEN}2. DISPLAY değişkeni ayarlandı: $env:DISPLAY${NC}"

# Docker kontrolü
echo -e "\n${GREEN}3. Docker Desktop kontrolü...${NC}"
if (!(docker ps 2>$null)) {
    echo -e "${RED}❌ Docker çalışmıyor! Docker Desktop'ı başlatın.${NC}"
    exit 1
}
echo "✅ Docker çalışıyor"

# Container'ı çalıştır
echo -e "\n${GREEN}4. Container başlatılıyor...${NC}"

docker run -it --rm `
    --name ros2_moveit_container `
    --privileged `
    --net=host `
    -e DISPLAY=$env:DISPLAY `
    -e QT_X11_NO_MITSHM=1 `
    -e LIBGL_ALWAYS_SOFTWARE=1 `
    -e ROS_DOMAIN_ID=42 `
    -v ${PWD}/../src:/root/colcon_ws/src:rw `
    ros2_colcon_workspace:humble `
    bash

echo -e "\n${GREEN}Container kapatıldı.${NC}"
