// app.js
require('dotenv').config()

const express = require('express')
const line = require('@line/bot-sdk')
const admin = require('firebase-admin')
const axios = require('axios')
const bodyParser = require('body-parser')

// ✅ 初始化 Firebase
admin.initializeApp()
const db = admin.firestore()

// ✅ LINE 設定
const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.CHANNEL_SECRET,
}

const client = new line.Client(config)
const app = express()

// ✅ 用 rawBody 給 LINE middleware 做簽名驗證
app.post(
  '/callback',
  bodyParser.json({
    verify: (req, res, buf) => {
      req.rawBody = buf
    },
  }),
  line.middleware(config),
  async (req, res) => {
    try {
      const results = await Promise.all(req.body.events.map(handleEvent))
      res.json(results)
    } catch (err) {
      console.error('Webhook 處理錯誤:', err)
      res.status(500).end()
    }
  }
)

// ✅ 呼叫 NLP 服務：取得情緒分數與關鍵字
async function analyzeSentimentAndKeywords(text) {
  try {
    const res = await axios.post(process.env.NLP_SERVICE_URL + '/analyze', { text })
    return res.data
  } catch (e) {
    console.error('分析錯誤:', e.message)
    return { score: 0, keywords: [] }
  }
}

// ✅ 呼叫 Gemini 關懷語 API
async function generateCaringMessage(text, keywords) {
  try {
    const res = await axios.post(process.env.CARE_SERVICE_URL + '/care', {
      text,
      keywords
    })
    return res.data.message || '請記得好好照顧自己 ❤️'
  } catch (e) {
    console.error('❌ 關懷語錯誤:', e.message)
    return '請記得好好照顧自己 ❤️'
  }
}

// ✅ 呼叫雷達圖 API
async function fetchEmotionRadar(userId, startDate, endDate, emotionScores) {
  try {
    const res = await axios.post(process.env.RADAR_SERVICE_URL + '/draw_emotion_radar', {
      userId,
      startDate,
      endDate,
      emotionScores
    })
    return res.data
  } catch (e) {
    console.error('畫雷達圖錯誤:', e.message)
    return null
  }
}

// ✅ 處理 LINE Event
async function handleEvent(event) {
  if (event.type !== 'message' || event.message.type !== 'text') return null

  const userText = event.message.text
  const userId = event.source.userId

  // ✅ 觸發『心情追蹤』功能
  if (userText.includes('心情追蹤')) {
    const startDate = '2025-07-10'
    const endDate = '2025-07-15'

    // 從 Firestore 抓六種指標的平均分數
    const scoresSnapshot = await db.collection('messages')
      .where('userId', '==', userId)
      .where('timestamp', '>=', new Date(startDate))
      .where('timestamp', '<=', new Date(endDate + 'T23:59:59'))
      .get()

    const emotionScores = {
      '緊張': 0,
      '害怕': 0,
      '不安': 0,
      '神經質': 0,
      '不耐煩': 0,
      '挫敗感': 0
    }
    let count = 0

    scoresSnapshot.forEach(doc => {
      const data = doc.data()
      if (data.keywords) {
        for (const k of data.keywords) {
          if (emotionScores[k] !== undefined) {
            emotionScores[k] += data.score
          }
        }
        count++
      }
    })

    if (count > 0) {
      for (const k in emotionScores) {
        emotionScores[k] = parseFloat((emotionScores[k] / count).toFixed(3))
      }
    }

    const radarResult = await fetchEmotionRadar(userId, startDate, endDate, emotionScores)
    if (!radarResult) {
      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: '抱歉，心情雷達圖生成失敗 😢'
      })
    }

    return client.replyMessage(event.replyToken, [
      {
        type: 'text',
        text: `📌 這是你 ${startDate}～${endDate} 的心情狀態雷達圖與指標：\n\n${radarResult.kpiText}`
      },
      {
        type: 'image',
        originalContentUrl: `data:image/png;base64,${radarResult.radarImageBase64}`,
        previewImageUrl: `data:image/png;base64,${radarResult.radarImageBase64}`
      }
    ])
  }

  // ✅ NLP 情緒分析 & 關懷語
  const { score, keywords } = await analyzeSentimentAndKeywords(userText)
  await db.collection('messages').add({
    userId,
    score,
    keywords,
    timestamp: admin.firestore.Timestamp.now()
  })

  let reply = `情緒分數：${score.toFixed(3)}\n`
  if (score > 0.3) {
    reply += '聽起來你今天心情不錯 😊'
  } else if (score < -0.3) {
    const careMessage = await generateCaringMessage(userText, keywords)
    reply += careMessage
  } else {
    reply += '你的心情還好～'
  }

  return client.replyMessage(event.replyToken, {
    type: 'text',
    text: reply
  })
}

// ✅ 啟動伺服器
const PORT = process.env.PORT || 8080
app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`))