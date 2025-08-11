# --- 第一階段：建立 Node.js LINE Bot ---
FROM node:18 AS bot
WORKDIR /app

# 複製並安裝 Node 套件
COPY package*.json ./
RUN npm install

# 複製 LINE Bot 程式與環境變數（.env 是開發用）
COPY .env .env
COPY app.js ./

# --- 第二階段：建立 Python Flask 服務（nlp / radar / gemini / summary）---
FROM python:3.11-slim AS python-services
WORKDIR /services

# 複製 requirements 並安裝套件
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有 Flask 子服務
COPY nlp_service.py draw_emotion_radar.py gemini_service.py summary_service.py ./

# --- 第三階段：整合映像（Node.js + Python + 啟動腳本）---
FROM python:3.11-slim
WORKDIR /srv

# ✅ 複製所有檔案到最終映像
COPY --from=bot /app /srv/bot
COPY --from=python-services /services /srv/services
COPY entrypoint.sh /entrypoint.sh

# ✅ 設定權限
RUN chmod +x /entrypoint.sh

# ✅ 安裝 Python 套件
RUN pip install --no-cache-dir -r /srv/services/requirements.txt

# ✅ 安裝 Node.js（給 LINE Bot 用）
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    cd /srv/bot && npm ci --omit=dev

# ✅ 開放對外 port（Cloud Run 用）
EXPOSE 8080 5000 5001 5002 5003

# ✅ 啟動全部服務
CMD ["/entrypoint.sh"]