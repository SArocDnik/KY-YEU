from flask import Flask, jsonify, request, send_from_directory
import json
import os
import json
import os
from datetime import datetime
import threading
import urllib.request

app = Flask(__name__)
DB_FILE = 'guestbook.json'
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461950574827278408/I2_yuUEogKPtxHnNAKF46tqPQF_PtT2salGtcBqA6QKoQL7TPGaLK7vdBMVD5FD1tPoX"

def send_discord_notification(name, msg, is_public=True):
    try:
        title = "🎉 New Yearbook Message!" if is_public else "🔒 New PRIVATE Yearbook Message!"
        color = 5797887 if is_public else 16711680 # Blue for Public, Red for Private
        
        payload = {
            "embeds": [
                {
                    "title": title,
                    "color": color, 
                    "fields": [
                        {"name": "From", "value": f"**{name}**", "inline": True},
                        {"name": "Message", "value": msg, "inline": False},
                        {"name": "Visibility", "value": "Public" if is_public else "Private", "inline": True}
                    ],
                    "footer": {"text": "Yearbook 2026 Notification System"}
                }
            ]
        }
        
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            pass # Success
    except Exception as e:
        print(f"Failed to send Discord webhook: {e}")


GEN_Z_MESSAGES = [
    {"name": "Thảo_Mai_Pro", "msg": "Mãi keo lì nha các bạn iu <3 Ra trường đừng quên tao đấy!", "time": "Just now"},
    {"name": "Boiz_Phố_Núi", "msg": "12 Tin mãi đỉnh, không nói nhiều! AE mình là cái gì? Là gia đình!", "time": "Just now"},
    {"name": "Shark_Hưng_Thịnh", "msg": "Chúc cả lớp sớm giàu, thành công rực rỡ. Lúc đó nhớ donate tao nha :v", "time": "Just now"},
    {"name": "Ngọc_Hân_Chanh_Sả", "msg": "Ra trường rồi nhớ giữ liên lạc, đứa nào seen không rep tao block thẳng tay =))", "time": "Just now"},
    {"name": "Dũng_Hacker", "msg": "Flex nhẹ cái lưu bút xịn xò này. Chúc ae code đời không bug!", "time": "Just now"},
    {"name": "Lớp_Trưởng_Gương_Mẫu", "msg": "Hẹn 10 năm nữa họp lớp, ai không đi làm... con cún 🐕 nhớ chưa!", "time": "Just now"},
    {"name": "Nhung_Baby", "msg": "Cảm ơn thanh xuân đã cho tui gặp các bợn. Yêu cả nhà nhiều lắm <3", "time": "Just now"},
    {"name": "Khánh_Sky", "msg": "Over hợp! Chúc mọi người chân cứng đá mềm, vững bước tương lai.", "time": "Just now"},
    {"name": "Hội_Người_Yêu_Cũ", "msg": "Kiếp này là bạn, kiếp sau vẫn là bạn nhớ! Đừng quên những ngày trốn học đi net.", "time": "Just now"},
    {"name": "Gamer_Ẩn_Danh", "msg": "GGWP! Game này kết thúc để mở ra map mới. Good luck have fun ae!", "time": "Just now"}
]

@app.route('/api/seed', methods=['POST'])
def seed_data():
    try:
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Read existing
        data = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

        # Append new messages
        new_msgs = []
        for msg in GEN_Z_MESSAGES:
            m = msg.copy()
            m['time'] = current_date
            new_msgs.append(m)
        
        # Add to beginning
        data = new_msgs + data
        data = data[:100]

        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        return jsonify({"status": "seeded", "count": len(new_msgs)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    if not os.path.exists(DB_FILE):
        return jsonify([])
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Filter public messages (default to True if key missing)
        public_messages = [m for m in data if m.get('is_public', True) is not False]
        return jsonify(public_messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def check_profanity(text):
    # Basic Blacklist (Vietnamese & English)
    bad_words = [
        "dm", "dkm", "đm", "đkm", "vcl", "vl", "vãi", "buồi", "cặc", "lồn", "đéo", "đĩ", "fuck", "shit", "bitch", "bastard", "ngu", "chó", "cút"
    ]
    text_lower = text.lower()
    for word in bad_words:
        if word in text_lower: # Simple substring check (can be improved)
            return True
    return False

@app.route('/api/messages', methods=['POST'])
def add_message():
    try:
        new_msg = request.json
        name = new_msg.get('name', '')
        msg = new_msg.get('msg', '')

        if not name or not msg:
            return jsonify({"error": "Missing fields"}), 400
        
        # Check Profanity
        if check_profanity(name) or check_profanity(msg):
             return jsonify({"error": "Nội dung chứa từ ngữ không phù hợp. Vui lòng lịch sự!"}), 400
        
        # Add timestamp if missing
        if not new_msg.get('time'):
            new_msg['time'] = datetime.now().strftime("%d/%m/%Y")

        messages = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = []
        
        # Prepend new message
        messages.insert(0, new_msg)
        
        # Limit to 100 messages
        messages = messages[:100]

        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
            
        # Send Discord Notification (Async)
        try:
            threading.Thread(target=send_discord_notification, args=(new_msg.get('name'), new_msg.get('msg'), new_msg.get('is_public', True))).start()
        except Exception as e:
            print(f"Thread error: {e}")

        return jsonify({"status": "success", "data": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">> YEARBOOK SYSTEM ONLINE: http://localhost:5000")
    app.run(debug=True, port=5000)
