from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")  # 從 .env 環境變數讀取

@app.route("/care", methods=["POST"])
def generate_care():
    data = request.get_json()
    user_text = data.get("text", "")
    keywords = data.get("keywords", [])  # 預期為 list

    # 關鍵字轉為文字字串顯示
    keyword_text = "、".join(keywords)

    # 建立 prompt
    prompt = f"""
你是一位溫暖且富有同理心的心理陪伴助理。
請根據以下使用者訊息與其情緒關鍵字，生成一句溫柔、不批判、非制式的關懷語句。
請勿問問題，語氣要真誠自然，有具體安慰與支持性語言。

使用者訊息：{user_text}
情緒關鍵字：{keyword_text}

請直接回覆一句安慰語。
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    headers = { "Content-Type": "application/json" }
    body = {
        "contents": [
            {
                "parts": [
                    { "text": prompt }
                ]
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        res.raise_for_status()
        response_json = res.json()
        message = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        return jsonify({"message": message})

    except Exception as e:
        print("Gemini error:", e)
        return jsonify({"message": "你已經很努力了，請記得給自己一點溫柔 ❤️"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)

