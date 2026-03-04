FROM jellyfin/jellyfin:latest

RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install requests beautifulsoup4 --break-system-packages && \
    apt-get clean

COPY strm_sync.py /app/strm_sync.py

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8096

CMD ["/start.sh"]
