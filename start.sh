#!/bin/sh
echo "=== Starting strm_sync ===" 
python3 /app/strm_sync.py &
echo "=== Starting Jellyfin ==="
exec /jellyfin/jellyfin \
  --datadir /config \
  --cachedir /cache \
  --ffmpeg /usr/lib/jellyfin-ffmpeg/ffmpeg
