FROM python:3.10-slim

# ctranslate2 / onnxruntime 需要 libgomp1；apt 走清华镜像（大陆服务器直连 deb.debian.org 不通）
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list 2>/dev/null; \
    apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY server.py index.html app.js styles.css world.html world.js world.css ./
COPY js/ js/
COPY assets/ assets/
COPY data/ data/

# 应用以非 root 运行（compose 里 user: "1000:1000"），
# 可写位置只有挂载卷（data/、assets/audio/cache）与 tmpfs /tmp。
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8765/api/health', timeout=5)"]

CMD ["python", "server.py"]
