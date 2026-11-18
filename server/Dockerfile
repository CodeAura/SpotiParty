# The SpotiParty Hub in a container. Build from the repository root:
#   docker build -f server/Dockerfile -t spotiparty-hub .
# or use server/docker-compose.yml. Only the Python standard library is used: no pip install.
FROM python:3.12-alpine

RUN addgroup -S spotiparty && adduser -S -G spotiparty -h /data spotiparty \
    && mkdir -p /data && chown spotiparty:spotiparty /data
WORKDIR /app
COPY hub/ hub/
COPY web/ web/

USER spotiparty
ENV PYTHONUNBUFFERED=1
VOLUME ["/data"]
# 8770: dashboard, guest page and screen. 8771/udp: Android TV finds the hub on its own.
EXPOSE 8770 8771/udp
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8770/api/ping', timeout=4)"
CMD ["python3", "hub/spotiparty_hub.py", "--data", "/data", "--web", "/app/web", "--port", "8770", "--setup-pin"]
