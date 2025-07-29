# --- 第一階段：建立 Node.js LINE Bot ---
FROM node:18 AS bot
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY app.js ./

# --- 第二階段：建立 Python Flask 服務（nlp / chart / gemini）---
FROM python:3.11-slim AS python-services
WORKDIR /services
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY nlp_service.py draw_emotion_chart.py gemini_service.py ./

# --- 第三階段：整合映像（Node.js + Python + 啟動腳本）---
FROM python:3.11-slim
WORKDIR /srv

# ✅ 複製服務與程式碼
COPY --from=bot /app /srv/bot
COPY --from=python-services /services /srv/services
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ✅ 安裝 Node.js（給 LINE Bot 用）
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    cd /srv/bot && npm ci --omit=dev

# ✅ 開放 Flask 與 LINE Bot 使用的 port
EXPOSE 8080 5000 5001 5002

# ✅ 啟動全部子服務
CMD ["/entrypoint.sh"]
