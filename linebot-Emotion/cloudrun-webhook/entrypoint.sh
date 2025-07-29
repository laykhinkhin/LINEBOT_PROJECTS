#!/bin/bash

# 啟動 Flask 子服務
cd /srv/services
python3 nlp_service.py &       # port 5000
python3 draw_emotion_chart.py &  # port 5001
python3 gemini_service.py &    # port 5002

# 啟動主 LINE Bot
cd /srv/bot
node app.js

