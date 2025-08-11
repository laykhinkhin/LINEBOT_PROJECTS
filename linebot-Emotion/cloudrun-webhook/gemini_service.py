from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
import os
import requests
import datetime

app = Flask(__name__)
CORS(app)

# ✅ 初始化 Firebase
db = firestore.Client()

# ✅ Gemini 分析服務的 URL（來自 env）
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "http://localhost:5001/analyze-emotion")

@app.route('/get-emotion-summary', methods=['POST'])
def get_summary():
    data = request.get_json()
    user_id = data.get("userId")
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not user_id or not start_date or not end_date:
        return jsonify({"error": "userId, startDate, endDate 為必填"}), 400

    try:
        # ✅ 時間區間轉換
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)

        # ✅ Firestore 查詢
        snapshot = db.collection("messages") \
            .where("userId", "==", user_id) \
            .where("timestamp", ">=", start) \
            .where("timestamp", "<", end) \
            .stream()

        messages = []
        summary_list = []

        for doc in snapshot:
            d = doc.to_dict()
            msg = d.get("text", "")
            score = d.get("score", 0.0)
            timestamp = d.get("timestamp")

            # ✅ timestamp 格式處理
            if isinstance(timestamp, datetime.datetime):
                date_str = timestamp.strftime("%Y-%m-%d")
            else:
                date_str = ""

            messages.append(msg)
            summary_list.append({
                "date": date_str,
                "score": round(score, 3),
                "text": msg
            })

        # ✅ 若無資料
        if not messages:
            return jsonify({
                "scores": {
                    "緊張": 0, "害怕": 0, "不安": 0,
                    "神經質": 0, "不耐煩": 0, "挫敗感": 0
                },
                "keywords": ["查無資料"],
                "summary": []
            })

        # ✅ 呼叫 Gemini API
        try:
            res = requests.post(GEMINI_API_URL, json={"messages": messages})
            res.raise_for_status()
            gemini_result = res.json()
        except Exception as e:
            print("⚠️ Gemini API 呼叫錯誤：", e)
            gemini_result = {
                "scores": {
                    "緊張": 0, "害怕": 0, "不安": 0,
                    "神經質": 0, "不耐煩": 0, "挫敗感": 0
                },
                "keywords": ["Gemini API 呼叫失敗"]
            }

        return jsonify({
            "scores": gemini_result.get("scores", {}),
            "keywords": gemini_result.get("keywords", []),
            "summary": summary_list
        })

    except Exception as e:
        print("🔥 get-emotion-summary 失敗：", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5003)