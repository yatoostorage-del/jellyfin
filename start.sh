#!/bin/sh
python3 /app/strm_sync.py 2>&1 | tee /proc/1/fd/1 &
/jellyfin/jellyfin --datadir /config --cachedir /cache --ffmpeg /usr/lib/jellyfin-ffmpeg/ffmpeg
