import io
import base64
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, request, jsonify
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection

app = Flask(__name__)

# 六軸名稱
EMOTIONS = ['緊張', '害怕', '不安', '神經質', '不耐煩', '挫敗感']

# KPI 分級 + Emoji
EMOJI_LEVELS = [
    (0.8, '🥵', '需放鬆'),
    (0.6, '😣', '偏高'),
    (0.3, '😐', '正常'),
    (0.0, '🙂', '良好'),
    (-1.0, '😌', '穩定')
]

def get_kpi_text(scores_dict, date_range):
    text = f"\n📊 你的情緒狀態指標（{date_range[0]}～{date_range[1]}）：\n\n"
    for label in EMOTIONS:
        score = scores_dict.get(label, 0.0)
        for threshold, emoji, desc in EMOJI_LEVELS:
            if score >= threshold:
                text += f"- {label}：{score:.2f} {emoji}（{desc}）\n"
                break
    return text

def radar_factory(num_vars, frame='circle'):
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    def draw_poly_frame(self, x0, y0, r):
        verts = [(np.cos(t) * r + x0, np.sin(t) * r + y0) for t in theta]
        return plt.Polygon(verts, closed=True, edgecolor="k")

    class RadarAxes(PolarAxes):
        name = 'radar'
        RESOLUTION = 1

        def fill(self, *args, **kwargs):
            kwargs['alpha'] = 0.5
            return super().fill(*args, **kwargs)

        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                line.set_linewidth(2)
            return lines

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

    register_projection(RadarAxes)
    return theta

def generate_radar_chart_with_kpi(user_id, date_range, scores_dict):
    N = len(EMOTIONS)
    theta = radar_factory(N)
    data = [scores_dict.get(label, 0.0) for label in EMOTIONS]
    data += data[:1]  # 關閉雷達圈
    theta = np.concatenate((theta, [theta[0]]))

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='radar'))
    ax.set_ylim(-1, 1)
    ax.plot(theta, data, color='red')
    ax.fill(theta, data, color='red', alpha=0.3)
    ax.set_varlabels(EMOTIONS)
    ax.set_title(f"{user_id} 的情緒雷達圖", va='bottom')

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    kpi_text = get_kpi_text(scores_dict, date_range)
    return {
        'radarImageBase64': image_base64,
        'kpiText': kpi_text
    }

@app.route('/draw_emotion_radar', methods=['POST'])
def draw_radar():
    data = request.get_json()
    user_id = data.get('userId')
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    scores = data.get('emotionScores')  # Dict[str, float]

    result = generate_radar_chart_with_kpi(user_id, (start_date, end_date), scores)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5001, debug=True)