#!/bin/bash

# 啟動 Flask 子服務（照舊）
cd /srv/services
python3 nlp_service.py &         # port 5000
python3 draw_emotion_radar.py &  # port 5001
python3 gemini_service.py &      # port 5002
python3 summary_service.py &     # port 5003

# 啟動主 LINE Bot，**一定要監聽 Cloud Run 要求的 $PORT（預設 8080）**
cd /srv/bot
node app.js