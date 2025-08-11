from flask import Flask
from draw_emotion_radar import radar_bp
from gemini_service import gemini_bp
from nlp_service import nlp_bp
from summary_service import summary_bp

app = Flask(__name__)
app.register_blueprint(radar_bp, url_prefix='/radar')
app.register_blueprint(gemini_bp, url_prefix='/gemini')
app.register_blueprint(nlp_bp, url_prefix='/nlp')
app.register_blueprint(summary_bp, url_prefix='/summary')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
