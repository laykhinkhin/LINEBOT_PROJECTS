from flask import Blueprint, request, jsonify
from google.cloud import firestore
import requests, datetime, os

summary_bp = Blueprint('summary', __name__)
db = firestore.Client()
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "http://localhost:5001/analyze-emotion")

@summary_bp.route('/get-emotion-summary', methods=['POST'])
def get_summary():
    data = request.get_json()
    user_id = data.get("userId")
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    if not user_id or not start_date or not end_date:
        return jsonify({"error": "userId, startDate, endDate 為必填"}), 400
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        snapshot = db.collection("messages").where("userId", "==", user_id).where("timestamp", ">=", start).where("timestamp", "<", end).stream()
        messages, summary_list = [], []
        for doc in snapshot:
            d = doc.to_dict()
            messages.append(d.get("text", ""))
            summary_list.append({"date": d.get("timestamp", "").strftime("%Y-%m-%d"), "score": round(d.get("score", 0), 3), "text": d.get("text", "")})
        if not messages:
            return jsonify({"scores": {k: 0 for k in ["緊張","害怕","不安","神經質","不耐煩","挫敗感"]}, "keywords": ["查無資料"], "summary": []})
        res = requests.post(GEMINI_API_URL, json={"messages": messages})
        gemini_result = res.json() if res.ok else {"scores": {k: 0 for k in ["緊張","害怕","不安","神經質","不耐煩","挫敗感"]}, "keywords": ["Gemini API 呼叫失敗"]}
        return jsonify({"scores": gemini_result["scores"], "keywords": gemini_result["keywords"], "summary": summary_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
