#!/bin/bash
cd /home/jetson

# Lanzar MediaMTX
./mediamtx &
sleep 2

# Lanzar audio permanente
ffmpeg -y -f alsa -ac 2 -ar 48000 -i hw:BYPM300,0 \
  -c:a libopus -b:a 64k -vn \
  -f rtsp -rtsp_transport tcp \
  rtsp://localhost:8554/audio &

echo "✅ MediaMTX + Audio arrancados"
echo "📺 Stream: http://192.168.0.172:8889"
wait
