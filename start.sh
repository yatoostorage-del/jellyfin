#!/bin/sh
python3 /app/strm_sync.py &
/jellyfin/jellyfin --datadir /config --cachedir /cache --ffmpeg /usr/lib/jellyfin-ffmpeg/ffmpeg
