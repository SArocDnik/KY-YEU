from flask import Flask, jsonify, request, send_from_directory
import json
import os
from datetime import datetime
import threading
import urllib.request
import urllib.parse
import uuid
try:
    from werkzeug.utils import secure_filename
except ImportError:
    # Fallback nếu werkzeug không có
    def secure_filename(filename):
        return filename.replace(' ', '_').replace('/', '_')
from pymongo import MongoClient

app = Flask(__name__)
DB_FILE = 'guestbook.json'

# --- VERCEL DETECTION ---
IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)

# --- UPLOAD CONFIG ---
# Trên Vercel, dùng /tmp cho file tạm (giới hạn 512MB)
if IS_VERCEL:
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Tạo thư mục uploads nếu chưa tồn tại (với error handling cho Vercel)
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
except Exception as e:
    print(f"Warning: Cannot create upload folder: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

MONGO_URI = os.environ.get('MONGO_URI') # Get connection string from Environment

# --- DATABASE ADAPTER ---
class DataStore:
    def __init__(self):
        self.use_mongo = False
        self.collection = None
        
        if MONGO_URI:
            try:
                client = MongoClient(MONGO_URI)
                # Force a specific database name if URI doesn't specify one
                # This fixes "No default database name defined" error
                db_name = urllib.parse.urlparse(MONGO_URI).path.strip('/')
                if not db_name:
                    db = client['yearbook_2026'] # Default DB name
                else:
                    db = client.get_default_database()
                
                self.collection = db['guestbook']
                self.use_mongo = True
                print(f">> Connected to MongoDB Atlas")
            except Exception as e:
                print(f"!! MongoDB Connection Failed: {e}. Falling back to JSON.")
        
        if not self.use_mongo:
             print(f">> Using Local JSON Storage: {DB_FILE}")

    def get_all(self):
        if self.use_mongo:
            # Sort by _id desc (newest first) and limit 100
            cursor = self.collection.find({}, {'_id': 0}).sort('_id', -1).limit(100)
            return list(cursor)
        else:
            if not os.path.exists(DB_FILE):
                return []
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []

    def insert(self, msg_obj):
        if self.use_mongo:
            self.collection.insert_one(msg_obj.copy())
            # Cleanup old messages (>100)
            count = self.collection.count_documents({})
            if count > 100:
                # Find the 100th latest doc
                latest_100 = self.collection.find().sort('_id', -1).limit(100)
                last_doc = list(latest_100)[-1]
                # Delete anything older than that
                self.collection.delete_many({'_id': {'$lt': last_doc['_id']}})
        else:
            data = self.get_all()
            data.insert(0, msg_obj)
            data = data[:100]
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return data

    def seed(self, messages):
        if self.use_mongo:
             self.collection.insert_many(messages)
        else:
            current_data = self.get_all()
            new_data = messages + current_data
            new_data = new_data[:100]
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)

db = DataStore()

# --- LINK STORE (Personalized Links) ---
class LinkStore:
    """Quản lý các link cá nhân hóa cho thiệp mời"""
    def __init__(self):
        self.use_mongo = False
        self.collection = None
        self.local_file = 'personalized_links.json'
        
        if MONGO_URI:
            try:
                client = MongoClient(MONGO_URI)
                db_name = urllib.parse.urlparse(MONGO_URI).path.strip('/')
                if not db_name:
                    database = client['yearbook_2026']
                else:
                    database = client.get_default_database()
                
                self.collection = database['personalized_links']
                # Tạo index unique cho slug
                self.collection.create_index('slug', unique=True)
                self.use_mongo = True
            except Exception as e:
                print(f"!! LinkStore MongoDB Failed: {e}")
        
    def _generate_slug(self, name):
        """Tạo slug từ tên người nhận"""
        import re
        import unicodedata
        # Chuẩn hóa unicode và loại bỏ dấu
        slug = unicodedata.normalize('NFD', name.lower())
        slug = slug.encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        return slug or 'link'
    
    def create(self, recipient_name, message, custom_slug=None, page_title=None, 
                 sender_name=None, subtitle=None, og_image=None):
        """Tạo link mới với Open Graph support"""
        slug = custom_slug.strip() if custom_slug else self._generate_slug(recipient_name)
        
        # Kiểm tra slug đã tồn tại
        if self.get_by_slug(slug):
            # Thêm số ngẫu nhiên nếu trùng
            import random
            slug = f"{slug}-{random.randint(100, 999)}"
        
        # Tạo default subtitle nếu không có
        default_subtitle = "Thanh xuân như một cơn mưa rào. Hãy cùng mình lưu giữ lại những khoảnh khắc rực rỡ nhất của tuổi học trò trước khi chúng ta mỗi người một ngả..."
        
        link_data = {
            'slug': slug,
            'recipient_name': recipient_name,
            'sender_name': sender_name or 'Bạn bè',
            'message': message,
            'page_title': page_title or f"Thiệp mời {recipient_name}",
            'subtitle': subtitle or default_subtitle,
            'og_image': og_image,  # Path to uploaded image
            'created_at': datetime.now().isoformat()
        }
        
        if self.use_mongo:
            self.collection.insert_one(link_data.copy())
        else:
            data = self.get_all()
            data.insert(0, link_data)
            with open(self.local_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return link_data
    
    def update(self, slug, data):
        """Cập nhật link đã tồn tại"""
        if self.use_mongo:
            # Chỉ update các field được phép
            update_fields = {k: v for k, v in data.items() if k in ['recipient_name', 'sender_name', 'message', 'page_title', 'subtitle', 'og_image']}
            result = self.collection.update_one({'slug': slug}, {'$set': update_fields})
            return result.modified_count > 0 or result.matched_count > 0
        else:
            links = self.get_all()
            for link in links:
                if link.get('slug') == slug:
                    # Update fields
                    if 'recipient_name' in data: link['recipient_name'] = data['recipient_name']
                    if 'sender_name' in data: link['sender_name'] = data['sender_name']
                    if 'message' in data: link['message'] = data['message']
                    if 'page_title' in data: link['page_title'] = data['page_title']
                    if 'subtitle' in data: link['subtitle'] = data['subtitle']
                    if 'og_image' in data: link['og_image'] = data['og_image']
                    
                    with open(self.local_file, 'w', encoding='utf-8') as f:
                        json.dump(links, f, ensure_ascii=False, indent=2)
                    return True
            return False
    
    def get_all(self):
        """Lấy tất cả links"""
        if self.use_mongo:
            cursor = self.collection.find({}, {'_id': 0}).sort('_id', -1)
            return list(cursor)
        else:
            if not os.path.exists(self.local_file):
                return []
            try:
                with open(self.local_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
    
    def get_by_slug(self, slug):
        """Lấy link theo slug"""
        if self.use_mongo:
            return self.collection.find_one({'slug': slug}, {'_id': 0})
        else:
            for link in self.get_all():
                if link.get('slug') == slug:
                    return link
            return None
    
    def delete(self, slug):
        """Xóa link theo slug"""
        if self.use_mongo:
            result = self.collection.delete_one({'slug': slug})
            return result.deleted_count > 0
        else:
            data = self.get_all()
            new_data = [l for l in data if l.get('slug') != slug]
            if len(new_data) < len(data):
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                return True
            return False

link_store = LinkStore()

# --- TEMPLATE STORE (Message Templates) ---
class TemplateStore:
    """Quản lý các template lời chúc tùy chỉnh"""
    def __init__(self):
        self.use_mongo = False
        self.collection = None
        self.local_file = 'message_templates.json'
        
        if MONGO_URI:
            try:
                client = MongoClient(MONGO_URI)
                db_name = urllib.parse.urlparse(MONGO_URI).path.strip('/')
                if not db_name:
                    database = client['yearbook_2026']
                else:
                    database = client.get_default_database()
                
                self.collection = database['message_templates']
                self.use_mongo = True
            except Exception as e:
                print(f"!! TemplateStore MongoDB Failed: {e}")
    
    def create(self, name, content):
        """Tạo template mới"""
        template_data = {
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        
        if self.use_mongo:
            self.collection.insert_one(template_data.copy())
        else:
            data = self.get_all()
            data.insert(0, template_data)
            with open(self.local_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return template_data
    
    def get_all(self):
        """Lấy tất cả templates"""
        if self.use_mongo:
            cursor = self.collection.find({}, {'_id': 0}).sort('_id', -1)
            return list(cursor)
        else:
            if not os.path.exists(self.local_file):
                return []
            try:
                with open(self.local_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
    
    def delete(self, name):
        """Xóa template theo tên"""
        if self.use_mongo:
            result = self.collection.delete_one({'name': name})
            return result.deleted_count > 0
        else:
            data = self.get_all()
            new_data = [t for t in data if t.get('name') != name]
            if len(new_data) < len(data):
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                return True
            return False

template_store = TemplateStore()

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
        
        # Prepare new messages
        new_msgs = []
        for msg in GEN_Z_MESSAGES:
            m = msg.copy()
            m['time'] = current_date
            new_msgs.append(m)
        
        # Use DataStore
        db.seed(new_msgs)
            
        return jsonify({"status": "seeded", "count": len(new_msgs)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- PERSONALIZED LINKS API ---
@app.route('/api/links', methods=['GET'])
def get_links():
    """Lấy danh sách tất cả links"""
    try:
        links = link_store.get_all()
        return jsonify(links)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/links', methods=['POST'])
def create_link():
    """Tạo link cá nhân hóa mới với Open Graph support"""
    try:
        data = request.json
        recipient_name = data.get('recipient_name', '').strip()
        message = data.get('message', '').strip()
        custom_slug = data.get('slug', '').strip()
        page_title = data.get('page_title', '').strip()
        sender_name = data.get('sender_name', '').strip()
        subtitle = data.get('subtitle', '').strip()
        og_image = data.get('og_image', '').strip()
        
        if not recipient_name:
            return jsonify({"error": "Tên người nhận không được để trống"}), 400
        if not message:
            return jsonify({"error": "Lời chúc không được để trống"}), 400
        
        link = link_store.create(
            recipient_name, 
            message, 
            custom_slug or None, 
            page_title or None,
            sender_name or None,
            subtitle or None,
            og_image or None
        )
        return jsonify({"status": "success", "link": link})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/links/<slug>', methods=['PUT'])
def update_link(slug):
    """Cập nhật link đã tồn tại"""
    try:
        data = request.json
        success = link_store.update(slug, data)
        if success:
            return jsonify({"status": "success", "slug": slug})
        return jsonify({"error": "Link không tồn tại"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload ảnh nền cho Open Graph"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Không có file được chọn"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Không có file được chọn"}), 400
        
        if file and allowed_file(file.filename):
            # Tạo tên file unique
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            
            try:
                # Tạo thư mục nếu chưa có
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Trả về URL của ảnh
                image_url = f"/uploads/{filename}"
                
                # Cảnh báo nếu đang trên Vercel
                warning = None
                if IS_VERCEL:
                    warning = "Lưu ý: Ảnh upload trên Vercel chỉ là tạm thời. Khuyến nghị dùng link ảnh từ Imgur/Cloudinary."
                
                return jsonify({
                    "status": "success", 
                    "url": image_url, 
                    "filename": filename,
                    "warning": warning
                })
            except Exception as save_error:
                return jsonify({
                    "error": f"Không thể lưu file: {str(save_error)}. Hãy dùng URL ảnh trực tiếp (Imgur, Cloudinary...).",
                    "use_external_url": True
                }), 500
        else:
            return jsonify({"error": "Định dạng file không được hỗ trợ. Chỉ chấp nhận: png, jpg, jpeg, gif, webp"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Phục vụ file ảnh đã upload"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({"error": "File không tồn tại"}), 404

@app.route('/api/links/<slug>', methods=['DELETE'])
def delete_link(slug):
    """Xóa link"""
    try:
        success = link_store.delete(slug)
        if success:
            return jsonify({"status": "deleted"})
        return jsonify({"error": "Link không tồn tại"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- TEMPLATES API ---
@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Lấy danh sách templates"""
    try:
        templates = template_store.get_all()
        return jsonify(templates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Tạo template mới"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        content = data.get('content', '').strip()
        
        if not name:
            return jsonify({"error": "Tên template không được để trống"}), 400
        if not content:
            return jsonify({"error": "Nội dung template không được để trống"}), 400
        
        template = template_store.create(name, content)
        return jsonify({"status": "success", "template": template})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates/<name>', methods=['DELETE'])
def delete_template(name):
    """Xóa template"""
    try:
        success = template_store.delete(name)
        if success:
            return jsonify({"status": "deleted"})
        return jsonify({"error": "Template không tồn tại"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ADMIN PANEL ---
@app.route('/admin')
def admin_panel():
    """Trang quản lý tạo link"""
    return send_from_directory('.', 'admin.html')

# --- PERSONALIZED PAGE ---
@app.route('/p/<slug>')
def personalized_page(slug):
    """Hiển thị trang thiệp mời cá nhân hóa với Open Graph"""
    link = link_store.get_by_slug(slug)
    if not link:
        return "<h1>404 - Link không tồn tại</h1>", 404
    
    # Đọc template và thay thế placeholder
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Tạo URL đầy đủ cho ảnh
        # Fix: Force HTTPS on Vercel/Production for Facebook Crawler
        if IS_VERCEL or request.headers.get('X-Forwarded-Proto') == 'https':
            base_url = f"https://{request.host}"
        else:
            base_url = request.host_url.rstrip('/')
            
        og_image_url = link.get('og_image')
        
        # Logic Fix V2: Handle User Input more robustly (e.g. missing 'https://')
        if not og_image_url:
            # Case 1: Empty -> Default Unsplash
            og_image_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1200&auto=format&fit=crop"
        elif og_image_url.startswith('/'):
            # Case 2: Local path (uploaded via our API) -> Prepend Base URL
            og_image_url = f"{base_url}{og_image_url}"
        elif not og_image_url.startswith('http'):
            # Case 3: External link but missing protocol (e.g. "imgur.com/...") -> Add https://
            og_image_url = f"https://{og_image_url}"
        # Case 4: Absolute URL (starts with http/https) -> Keep as is
        
        # Tạo OG title: Sử dụng Page Title đã custom trong Admin
        og_title = link.get('page_title')
        # Fallback (phòng trường hợp cũ không có field này)
        if not og_title:
             sender = link.get('sender_name', 'Bạn bè')
             recipient = link.get('recipient_name', '')
             og_title = f"Thiệp mời: Kỷ Yếu - {sender} gửi {recipient} | Thiệp Online"
        
        # Subtitle cho description
        og_description = link.get('subtitle', 'Thanh xuân như một cơn mưa rào. Hãy cùng mình lưu giữ lại những khoảnh khắc rực rỡ nhất của tuổi học trò trước khi chúng ta mỗi người một ngả...')
        
        # Full URL của trang
        og_url = f"{base_url}/p/{slug}"

        # Clean old tags: Replace everything between default markers
        start_marker = '<!-- Default Open Graph / Facebook / Messenger -->'
        end_marker = '<!-- Tailwind CSS -->'
        
        if start_marker in html and end_marker in html:
            # Escape & for HTML attributes to prevent breaking signed URLs (fbcdn)
            # Facebook Crawler requires strict HTML entity encoding for ampersands in attributes
            og_image_url_escaped = og_image_url.replace('&', '&amp;')
            
            parts = html.split(start_marker)
            pre_part = parts[0]
            # Find the rest after the start marker
            rest = parts[1]
            if end_marker in rest:
                 post_part = rest.split(end_marker)[1]
                 
                 # New Dynamic Block
                 new_block = f'''{start_marker}
    <meta property="og:type" content="website">
    <meta property="og:url" content="{og_url}">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_description}">
    <meta property="og:image" content="{og_image_url_escaped}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:locale" content="vi_VN">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_description}">
    <meta name="twitter:image" content="{og_image_url_escaped}">
    
    <script>
        window.PERSONALIZED_DATA = {{
            recipientName: "{link['recipient_name']}",
            senderName: "{link.get('sender_name', 'Bạn bè')}",
            message: "{link['message'].replace('"', '\\"').replace(chr(10), '\\n').replace(chr(13), '')}",
            pageTitle: "{link['page_title']}",
            subtitle: "{link.get('subtitle', '').replace('"', '\\"')}"
        }};
    </script>
    {end_marker}'''
                 html = pre_part + new_block + post_part
        else:
            # Fallback if markers missing (shouldn't happen)
            pass

        # Thay thế tiêu đề trang (Dùng Regex để handle whitespace)
        import re
        html = re.sub(
            r'<title>.*?</title>',
            f'<title>{link["page_title"]}</title>',
            html,
            count=1,
            flags=re.DOTALL
        )
        
        return html
    except Exception as e:
        return f"<h1>Error: {e}</h1>", 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        data = db.get_all()
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

        # Insert via DataStore
        db.insert(new_msg)
        
        # Return updated list
        all_messages = db.get_all()
        # Filter for display
        public_messages = [m for m in all_messages if m.get('is_public', True) is not False]
            
        # Send Discord Notification (Async)
        try:
            threading.Thread(target=send_discord_notification, args=(new_msg.get('name'), new_msg.get('msg'), new_msg.get('is_public', True))).start()
        except Exception as e:
            print(f"Thread error: {e}")

        return jsonify({"status": "success", "data": public_messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">> YEARBOOK SYSTEM ONLINE: http://localhost:5000")
    app.run(debug=True, port=1000)
