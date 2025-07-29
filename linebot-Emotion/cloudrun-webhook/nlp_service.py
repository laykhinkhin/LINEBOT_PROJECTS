from flask import Flask, request, jsonify
from google.cloud import language_v1
from dotenv import load_dotenv
import os

# ✅ 載入 .env 檔
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = Flask(__name__)
client = language_v1.LanguageServiceClient()

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')

    if not text:
        return jsonify({'error': 'Missing text'}), 400

    # ✅ 文件設定
    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language="zh"
    )

    try:
        # ✅ 情緒分析
        sentiment_response = client.analyze_sentiment(document=document)
        score = sentiment_response.document_sentiment.score

        # ✅ 關鍵詞提取（entity）
        entity_response = client.analyze_entities(document=document)
        keywords = [entity.name for entity in entity_response.entities if entity.salience > 0.01]
        keywords = list(set(keywords))  # 去除重複
        keywords_str = ", ".join(keywords) if keywords else "(無摘要)"

        return jsonify({
            'score': score,
            'keywords': keywords_str
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
