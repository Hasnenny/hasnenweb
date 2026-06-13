# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🚀 SERVER HUB — Professional Hosting Control Panel                      ║
║  Version: 2.0  |  By: @Y0YY12  |  Admin: OWNER                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  - Full PHP / Node.js / Python support                                   ║
║  - Docker user isolation                                                 ║
║  - ZIP extract, file manager, drag & drop                                ║
║  - Admin approval for new registrations                                  ║
║  - Modern responsive UI (SERVER HUB theme)                               ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os, sys, gc, re, ast, json, time, uuid, html, shutil, socket
import signal, string, random, secrets, hashlib, logging, platform
import zipfile, tarfile, threading, subprocess, warnings
import urllib.request, urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from collections import deque
from io import BytesIO

try:
    import resource
except ImportError:
    resource = None

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from flask import (Flask, render_template_string, request, jsonify, session,
                   redirect, url_for, send_file, send_from_directory)
from werkzeug.utils import secure_filename

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
#  1.  Unlimited Resources
# ─────────────────────────────────────────────
def set_unlimited_resources():
    if not resource:
        return False
    try:
        resource.setrlimit(resource.RLIMIT_AS,    (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_DATA,  (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_NOFILE,(999999, 999999))
        resource.setrlimit(resource.RLIMIT_NPROC, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        return True
    except Exception:
        return False

set_unlimited_resources()

def _memory_monitor():
    while True:
        time.sleep(30)
        try:
            gc.collect()
            try:
                open('/proc/sys/vm/drop_caches','w').write('3')
            except Exception:
                pass
        except Exception:
            pass

threading.Thread(target=_memory_monitor, daemon=True).start()

# ─────────────────────────────────────────────
#  2.  Paths & Settings
# ─────────────────────────────────────────────
DEFAULT_BASE = os.environ.get('BASE_PATH') or (
    os.path.join(os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', os.getcwd()), 'panel_data')
    if (os.path.exists('/home/runner') or 'REPL_ID' in os.environ)
    else '/tmp/panel_data'
)
BASE_PATH          = DEFAULT_BASE
os.makedirs(BASE_PATH, exist_ok=True)

USERS_FOLDER       = os.path.join(BASE_PATH, 'users_data')
USERS_FILE         = os.path.join(BASE_PATH, 'users.json')
PROCESSES_FILE     = os.path.join(BASE_PATH, 'processes.json')
SCHEDULES_FILE     = os.path.join(BASE_PATH, 'schedules.json')
LOGS_FILE          = os.path.join(BASE_PATH, 'activity.log')
USER_SESSIONS_FILE = os.path.join(BASE_PATH, 'user_sessions.json')
BACKUPS_FOLDER     = os.path.join(BASE_PATH, 'backups')
TEMP_FOLDER        = os.path.join(BASE_PATH, 'temp')
PACKAGES_FILE      = os.path.join(BASE_PATH, 'packages.json')
DOCKER_FILE        = os.path.join(BASE_PATH, 'docker.json')
MASTER_CONFIG_FILE = os.path.join(BASE_PATH, 'master_config.json')
PORTS_FILE         = os.path.join(BASE_PATH, 'ports.json')
ACTIVITY_FILE      = os.path.join(BASE_PATH, 'activity_feed.json')
OWNER_CONFIG_FILE  = os.path.join(BASE_PATH, 'owner_config.json')
MAINTENANCE_FILE   = os.path.join(BASE_PATH, 'maintenance.json')
BOT_STATS_FILE     = os.path.join(BASE_PATH, 'bot_stats.json')
ANNOUNCE_FILE      = os.path.join(BASE_PATH, 'announcements.json')
SECURITY_ALERTS_FILE = os.path.join(BASE_PATH, 'security_alerts.json')
NODEJS_PROCS_FILE  = os.path.join(BASE_PATH, 'nodejs_procs.json')
PHP_CONFIG_FILE    = os.path.join(BASE_PATH, 'php_config.json')

PROFILE_IMAGE_URL = "https://k.top4top.io/p_3785nf0ym1.jpg"
ENTRY_SOUND_URL   = "https://b.top4top.io/m_3785fa5tu2.mp4"

# ─────────────────────────────────────────────
#  3.  JSON Helpers
# ─────────────────────────────────────────────
def init_json_file(path, default):
    if not os.path.exists(path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

def load_json_file(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}

def save_json_file(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────
#  4.  Master Config
# ─────────────────────────────────────────────
def load_master_config():
    default = {
        'master_username': 'OWNER',
        'master_password_hash': hashlib.sha256('Hasnen1@@1'.encode()).hexdigest(),
        'port': 3178,
        'main_file': 'main.py'
    }
    if not os.path.exists(MASTER_CONFIG_FILE):
        save_json_file(MASTER_CONFIG_FILE, default)
        return default
    cfg = load_json_file(MASTER_CONFIG_FILE)
    if not cfg:
        return default
    for k, v in default.items():
        cfg.setdefault(k, v)
    return cfg

MASTER_CONFIG        = load_master_config()
MASTER_USERNAME      = MASTER_CONFIG.get('master_username', 'OWNER')
MASTER_PASSWORD_HASH = MASTER_CONFIG.get('master_password_hash')
SERVER_START_TIME    = time.time()

# ─────────────────────────────────────────────
#  5.  Create Folders & Init Files
# ─────────────────────────────────────────────
for _f in [USERS_FOLDER, TEMP_FOLDER, BACKUPS_FOLDER]:
    os.makedirs(_f, exist_ok=True)

init_json_file(USERS_FILE, {})
init_json_file(PROCESSES_FILE, {})
init_json_file(SCHEDULES_FILE, {})
init_json_file(USER_SESSIONS_FILE, {})
init_json_file(PACKAGES_FILE, {'pip': [], 'apt': [], 'npm': []})
init_json_file(DOCKER_FILE, {'containers': [], 'images': []})
init_json_file(PORTS_FILE, {'ports': []})
init_json_file(ACTIVITY_FILE, {'events': []})
init_json_file(OWNER_CONFIG_FILE, {
    'telegram_token': '', 'telegram_owner_id': '', 'bot_linked': False,
    'panel_name': 'SERVER HUB', 'welcome_msg': 'Welcome to SERVER HUB'
})
init_json_file(MAINTENANCE_FILE, {'enabled': False, 'message': 'Under maintenance. Try later.'})
init_json_file(BOT_STATS_FILE, {'total_users':0,'total_servers':0,'active_bots':0,'zip_files':0,'last_updated':''})
init_json_file(ANNOUNCE_FILE, {'list': []})
init_json_file(SECURITY_ALERTS_FILE, {'alerts': []})
init_json_file(NODEJS_PROCS_FILE, {})
init_json_file(PHP_CONFIG_FILE, {'default_version': '8.1'})

# ─────────────────────────────────────────────
#  6.  Owner helpers
# ─────────────────────────────────────────────
def load_owner_config():
    d = {'telegram_token':'','telegram_owner_id':'','bot_linked':False,
         'panel_name':'SERVER HUB','welcome_msg':'Welcome to SERVER HUB'}
    cfg = load_json_file(OWNER_CONFIG_FILE, d)
    for k,v in d.items(): cfg.setdefault(k,v)
    return cfg

def load_maintenance(): return load_json_file(MAINTENANCE_FILE, {'enabled':False,'message':'Under maintenance'})
def save_maintenance(d): save_json_file(MAINTENANCE_FILE, d)
def load_bot_stats(): return load_json_file(BOT_STATS_FILE, {})
def load_announcements(): return load_json_file(ANNOUNCE_FILE, {'list':[]})
def save_announcements(d): save_json_file(ANNOUNCE_FILE, d)

def load_security_alerts(): return load_json_file(SECURITY_ALERTS_FILE, {'alerts':[]})
def save_security_alert(username, filename, threats, ip):
    """Store a security alert and return the alert dict."""
    data = load_security_alerts()
    alert = {
        'id': str(uuid.uuid4())[:8],
        'username': username,
        'filename': filename,
        'threats': threats,
        'ip': ip,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reviewed': False
    }
    data['alerts'].insert(0, alert)
    data['alerts'] = data['alerts'][:200]   # keep last 200
    save_json_file(SECURITY_ALERTS_FILE, data)
    return alert

# ─────────────────────────────────────────────
#  7.  Flask App
# ─────────────────────────────────────────────
app = Flask(__name__)

_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret_key')
if os.path.exists(_SECRET_FILE):
    with open(_SECRET_FILE) as _sf:
        app.secret_key = _sf.read().strip()
else:
    _k = secrets.token_hex(64)
    open(_SECRET_FILE, 'w').write(_k)
    app.secret_key = _k

app.permanent_session_lifetime = timedelta(days=30)
app.config['MAX_CONTENT_LENGTH'] = None
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.before_request
def check_maintenance():
    maint = load_maintenance()
    if not maint.get('enabled'):
        return None
    if request.path in ['/login','/logout','/register'] or request.path.startswith('/api/'):
        return None
    if session.get('username') == MASTER_USERNAME:
        return None
    return render_template_string(MAINTENANCE_TMPL, message=maint.get('message','Under maintenance')), 503

# ─────────────────────────────────────────────
#  8.  Activity & Logging
# ─────────────────────────────────────────────
def add_activity_event(username, action, details=''):
    try:
        data = load_json_file(ACTIVITY_FILE, {'events': []})
        events = data.get('events', [])
        events.insert(0, {
            'id': str(uuid.uuid4())[:8],
            'username': username,
            'action': action,
            'details': details,
            'ip': request.remote_addr if request else '-',
            'timestamp': datetime.now().isoformat(),
            'time_text': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_json_file(ACTIVITY_FILE, {'events': events[:300]})
    except Exception:
        pass

def log_activity(username, action, details=''):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOGS_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] [{username}] {action} | {details}\n')
        add_activity_event(username, action, details)
    except Exception:
        pass

# ─────────────────────────────────────────────
#  9.  Replit KV Store
# ─────────────────────────────────────────────
_REPLIT_DB_URL = os.environ.get('REPLIT_DB_URL','')
_KV_USERS_KEY  = 'serverhub_users_v2'

def _kv_get(key):
    if not _REPLIT_DB_URL: return None
    try:
        url = _REPLIT_DB_URL.rstrip('/') + '/' + urllib.parse.quote(key, safe='')
        with urllib.request.urlopen(urllib.request.Request(url), timeout=5) as r:
            return r.read().decode('utf-8')
    except Exception:
        return None

def _kv_set(key, value):
    if not _REPLIT_DB_URL: return False
    try:
        data = urllib.parse.urlencode({key:value}).encode('utf-8')
        urllib.request.urlopen(urllib.request.Request(_REPLIT_DB_URL, data=data, method='POST'), timeout=5)
        return True
    except Exception:
        return False

def load_users():
    if _REPLIT_DB_URL:
        raw = _kv_get(_KV_USERS_KEY)
        if raw:
            try:
                d = json.loads(raw)
                if isinstance(d, dict):
                    save_json_file(USERS_FILE, d)
                    return d
            except Exception:
                pass
    return load_json_file(USERS_FILE, {})

def save_users(u):
    if not isinstance(u, dict): return
    existing = load_json_file(USERS_FILE, {})
    if not u and existing:
        return
    save_json_file(USERS_FILE, u)
    _kv_set(_KV_USERS_KEY, json.dumps(u, ensure_ascii=False))

def load_processes():     return load_json_file(PROCESSES_FILE)
def save_processes(p):    save_json_file(PROCESSES_FILE, p)
def load_schedules():     return load_json_file(SCHEDULES_FILE)
def save_schedules(s):    save_json_file(SCHEDULES_FILE, s)
def load_user_sessions(): return load_json_file(USER_SESSIONS_FILE)
def save_user_sessions(s):save_json_file(USER_SESSIONS_FILE, s)
def load_packages():      return load_json_file(PACKAGES_FILE)
def save_packages(p):     save_json_file(PACKAGES_FILE, p)
def load_ports():         return load_json_file(PORTS_FILE, {'ports':[]}).get('ports',[])
def save_ports(p):        save_json_file(PORTS_FILE, {'ports':p})

# ─────────────────────────────────────────────
#  10.  User Paths & Session Helpers
# ─────────────────────────────────────────────
def get_user_path(username):
    if username == MASTER_USERNAME:
        return BASE_PATH
    return os.path.join(USERS_FOLDER, username)

def ensure_user_folder(username):
    if username == MASTER_USERNAME: return
    p = get_user_path(username)
    os.makedirs(p, exist_ok=True)

def is_path_allowed(username, path):
    try:
        base = os.path.realpath(get_user_path(username))
        target = os.path.realpath(str(path))
        return target.startswith(base)
    except Exception:
        return False

def register_session(username):
    s = load_user_sessions()
    s[username] = s.get(username, 0) + 1
    save_user_sessions(s)

def unregister_session(username):
    s = load_user_sessions()
    s[username] = max(0, s.get(username, 1) - 1)
    save_user_sessions(s)

def can_user_login(username):
    users = load_users()
    ud = users.get(username, {})
    if not isinstance(ud, dict): return True
    # check expiry
    exp = ud.get('expiry')
    if exp:
        try:
            if datetime.fromisoformat(exp) < datetime.now():
                return False
        except Exception:
            pass
    # check max sessions
    mx = ud.get('max_sessions', 999)
    s = load_user_sessions()
    return s.get(username, 0) < mx

# ─────────────────────────────────────────────
#  11.  System Stats
# ─────────────────────────────────────────────
def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        uptime = int(time.time() - SERVER_START_TIME)
        h, r = divmod(uptime, 3600)
        m, s = divmod(r, 60)

        def _ip():
            try:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s2.connect(('8.8.8.8',80))
                ip = s2.getsockname()[0]
                s2.close()
                return ip
            except Exception:
                return '127.0.0.1'

        port = int(os.environ.get('PORT', MASTER_CONFIG.get('port') or 3178))
        return {
            'cpu': f'{cpu}%',
            'memory': f'{mem.used/1024**3:.1f} GB / {mem.total/1024**3:.1f} GB',
            'memory_percent': mem.percent,
            'disk': f'{disk.used/1024**3:.1f} GB / {disk.total/1024**3:.1f} GB',
            'disk_percent': disk.percent,
            'network_in': f'{net.bytes_recv/1024**2:.1f} MB',
            'network_out': f'{net.bytes_sent/1024**2:.1f} MB',
            'uptime': f'{h}h {m}m {s}s',
            'hostname': socket.gethostname(),
            'ip': _ip(),
            'port': port,
            'platform': platform.system(),
            'python': sys.version.split()[0],
        }
    except Exception as e:
        return {'error': str(e)}

# ─────────────────────────────────────────────
#  12.  Process Management
# ─────────────────────────────────────────────
running_processes = {}
file_processes    = {}
nodejs_processes = {}
_php_servers = {}

# ─────────────────────────────────────────────
#  15.  ZIP Extract Helpers
# ─────────────────────────────────────────────
ALLOWED_EXTENSIONS = {
    'py','js','ts','jsx','tsx','json','yaml','yml','toml','cfg','ini',
    'txt','md','html','htm','css','scss','sass','less',
    'sh','bash','bat','cmd',
    'jpg','jpeg','png','gif','webp','svg','ico',
    'mp3','mp4','ogg','wav',
    'zip','tar','gz','rar','7z',
    'pdf','doc','docx','xls','xlsx',
    'php','rb','go','rs','java','c','cpp','h',
    'sql','db','sqlite','env','xml',
    'woff','woff2','ttf','eot',
}

BLOCKED_EXTENSIONS = {'exe','com','scr','vbs','bat','cmd','ps1','msi','dll','sys',
                      'pif','application','gadget','hta','cpl','msc'}

# Only block clear real threats
DANGEROUS_PATTERNS = [
    (r'system\s*\(\s*\$_(?:GET|POST|REQUEST)|passthru\s*\(\s*\$_', 'PHP web shell'),
    (r'eval\s*\(\s*base64_decode\s*\(\s*\$_|eval\s*\(\s*gzinflate', 'PHP obfuscated shell'),
    (r'exec\s*\(base64\.b64decode\s*\(', 'Base64 exec payload'),
    (r'socket\.connect.*(?:4444|1337|31337)', 'Reverse shell socket'),
    (r'reverse_shell|bind_shell|meterpreter', 'Shell payload keyword'),
]

FILE_THEFT_BOT_SIGNATURES = [
    {'name': 'File-theft bot (Telegram + os.walk + send_document)',
     'require_all': [
         r'TeleBot\s*\(|telegram\.Bot\s*\(',
         r'os\.walk\s*\(',
         r'send_document|sendDocument'
     ]},
]

def scan_file_content(filepath):
    threats = []
    try:
        ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        if ext not in ('py','js','php','sh','bash','html','htm'):
            return []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(300_000)
        for pattern, desc in DANGEROUS_PATTERNS:
            try:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    threats.append(desc)
            except re.error:
                pass
        for sig in FILE_THEFT_BOT_SIGNATURES:
            if all(re.search(p, content, re.IGNORECASE | re.DOTALL) for p in sig['require_all']):
                if sig['name'] not in threats:
                    threats.append(sig['name'])
    except Exception:
        pass
    return threats
MAX_EXTRACT_SIZE = 500 * 1024 * 1024  # 500 MB

def safe_extract(archive_path, dest_dir, username):
    """Safely extract ZIP/TAR/RAR archives"""
    os.makedirs(dest_dir, exist_ok=True)
    if not is_path_allowed(username, dest_dir):
        return {'success': False, 'error': 'Forbidden destination'}
    
    ext = os.path.splitext(archive_path)[1].lower()
    extracted = []
    total_size = 0
    
    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for info in zf.infolist():
                    if total_size > MAX_EXTRACT_SIZE:
                        return {'success': False, 'error': 'Archive too large (>500 MB)'}
                    # path traversal protection
                    target = os.path.realpath(os.path.join(dest_dir, info.filename))
                    if not target.startswith(os.path.realpath(dest_dir)):
                        continue
                    zf.extract(info, dest_dir)
                    total_size += info.file_size
                    extracted.append(info.filename)
        
        elif ext in ('.tar','.gz','.bz2','.tgz') or archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:*') as tf:
                for member in tf.getmembers():
                    if total_size > MAX_EXTRACT_SIZE:
                        return {'success': False, 'error': 'Archive too large'}
                    target = os.path.realpath(os.path.join(dest_dir, member.name))
                    if not target.startswith(os.path.realpath(dest_dir)):
                        continue
                    tf.extract(member, dest_dir)
                    total_size += member.size
                    extracted.append(member.name)
        
        else:
            # try unrar if available
            try:
                r = subprocess.run(['unrar', 'x', '-y', archive_path, dest_dir],
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    extracted = ['(unrar extracted)']
                else:
                    return {'success': False, 'error': 'Unsupported format or unrar not available'}
            except Exception:
                return {'success': False, 'error': 'Unsupported archive format'}
        
        log_activity(username, 'files.extract', f'{len(extracted)} files extracted to {dest_dir}')
        return {'success': True, 'extracted': len(extracted), 'dest': dest_dir}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ─────────────────────────────────────────────
#  16.  Decorators
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        if 'logged_in' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success':False,'error':'Session expired'}), 401
            return redirect('/login')
        return f(*a, **kw)
    return w

def master_required(f):
    @wraps(f)
    def w(*a, **kw):
        if session.get('username') != MASTER_USERNAME:
            return jsonify({'success':False,'error':'Master only'}), 403
        return f(*a, **kw)
    return w

# ─────────────────────────────────────────────
#  17.  Maintenance Template
# ─────────────────────────────────────────────
MAINTENANCE_TMPL = r'''
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maintenance — SERVER HUB</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}
body{background:#0b0f17;color:#c9d1d9;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{text-align:center;padding:50px 40px;background:#161b22;border:1px solid #30363d;border-radius:16px;max-width:480px;width:92%}
.icon{font-size:72px;margin-bottom:20px;animation:spin 4s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
h1{font-size:26px;color:#fff;margin-bottom:8px}
.sub{color:#7c5cfc;font-size:12px;letter-spacing:3px;text-transform:uppercase;margin-bottom:20px}
.msg{background:#0d1117;border:1px solid #30363d;border-left:4px solid #7c5cfc;padding:16px;border-radius:8px;color:#8b949e;line-height:1.7}
.foot{margin-top:20px;font-size:11px;color:#484f58}
</style></head>
<body><div class="card">
<div class="icon">⚙️</div>
<h1>Under Maintenance</h1>
<div class="sub">SERVER HUB</div>
<div class="msg">{{ message }}</div>
<div class="foot">All rights reserved © SERVER HUB — By @Y0YY12</div>
</div></body></html>
'''

# ─────────────────────────────────────────────────────────────────────────────
#  18.  AUTH TEMPLATE  (Login + Register — SERVER HUB theme)
# ─────────────────────────────────────────────────────────────────────────────
AUTH_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SERVER HUB — Access</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter','Segoe UI',sans-serif}
html,body{height:100%;background:#0b0f17}
body{
  display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:
    radial-gradient(ellipse at 15% 50%,rgba(192,57,43,.4) 0%,transparent 55%),
    radial-gradient(ellipse at 85% 20%,rgba(142,68,173,.3) 0%,transparent 50%),
    radial-gradient(ellipse at 50% 100%,rgba(231,76,60,.2) 0%,transparent 60%),
    url('https://i.ibb.co/60Zvqk5L/photo.jpg') center/cover no-repeat fixed,
    #080b12;
  position:relative;overflow:hidden;
}
body::after{
  content:'';position:fixed;inset:0;
  background:rgba(8,11,18,.68);
  backdrop-filter:blur(3px) saturate(1.4);
  pointer-events:none;z-index:1;
}
body::before{
  content:'';position:absolute;inset:0;
  background-image:
    linear-gradient(rgba(124,92,252,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(124,92,252,.04) 1px,transparent 1px);
  background-size:60px 60px;
  animation:gridMove 25s linear infinite;
  pointer-events:none;
}
@keyframes gridMove{to{background-position:60px 60px}}

/* ── Glow orbs ── */
.orb{position:fixed;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:2}
.orb1{width:400px;height:400px;background:rgba(192,57,43,.14);top:-100px;left:-100px;animation:orbFloat1 12s ease-in-out infinite}
.orb2{width:300px;height:300px;background:rgba(142,68,173,.1);bottom:-80px;right:-80px;animation:orbFloat2 15s ease-in-out infinite}
@keyframes orbFloat1{0%,100%{transform:translate(0,0)}50%{transform:translate(60px,40px)}}
@keyframes orbFloat2{0%,100%{transform:translate(0,0)}50%{transform:translate(-40px,-30px)}}

/* ── Main wrap ── */
.wrap{
  position:relative;z-index:3;
  display:flex;flex-direction:column;align-items:center;
  width:min(460px,95vw);
}

/* ── Card (single container for logo + forms) ── */
.card{
  width:100%;
  background:rgba(13,17,23,.92);
  border:1px solid rgba(48,54,61,.8);
  border-radius:24px;
  overflow:hidden;
  box-shadow:
    0 30px 80px rgba(0,0,0,.6),
    0 0 0 1px rgba(124,92,252,.08),
    inset 0 1px 0 rgba(255,255,255,.04);
  backdrop-filter:blur(24px);
}

/* ── Logo block inside card ── */
.logo-block{
  display:flex;flex-direction:column;align-items:center;
  padding:32px 28px 24px;
  background:linear-gradient(180deg,rgba(124,92,252,.06) 0%,transparent 100%);
  border-bottom:1px solid rgba(48,54,61,.5);
  position:relative;
}
.logo-block::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 0%,rgba(124,92,252,.15) 0%,transparent 70%);
  pointer-events:none;
}
.logo-img{
  width:90px;height:90px;border-radius:50%;
  object-fit:cover;
  border:3px solid rgba(124,92,252,.5);
  box-shadow:0 0 30px rgba(124,92,252,.4),0 0 60px rgba(124,92,252,.15);
  animation:logoPulse 3s ease-in-out infinite;
  position:relative;z-index:1;
  background:#161b22;
}
@keyframes logoPulse{
  0%,100%{box-shadow:0 0 30px rgba(192,57,43,.5),0 0 60px rgba(192,57,43,.15);border-color:rgba(192,57,43,.6)}
  50%{box-shadow:0 0 50px rgba(231,76,60,.7),0 0 90px rgba(142,68,173,.3);border-color:rgba(231,76,60,.8)}
}
.logo-title{
  font-size:26px;font-weight:900;letter-spacing:2px;margin-top:14px;
  background:linear-gradient(135deg,#ff6b6b,#c0392b,#8e44ad);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  position:relative;z-index:1;
}
.logo-sub{
  color:#484f58;font-size:11px;margin-top:5px;
  letter-spacing:3px;text-transform:uppercase;
  position:relative;z-index:1;
}

/* ── Forms area ── */
.forms-area{padding:28px}

/* Tabs */
.tabs{
  display:flex;margin-bottom:24px;
  background:#0b0f17;border-radius:10px;padding:4px;gap:4px;
  border:1px solid rgba(48,54,61,.6);
}
.tab{
  flex:1;text-align:center;padding:10px 8px;cursor:pointer;
  color:#8b949e;font-weight:600;font-size:13px;border-radius:7px;
  transition:.25s;user-select:none;
}
.tab:hover{color:#c9d1d9;background:rgba(255,255,255,.04)}
.tab.active{
  color:#fff;
  background:linear-gradient(135deg,#c0392b,#922b21);
  box-shadow:0 2px 12px rgba(192,57,43,.5);
}

/* Form */
.form{display:none}
.form.active{display:block;animation:fadeUp .25s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.field{margin-bottom:14px}
.field label{
  display:block;color:#8b949e;font-size:10px;
  text-transform:uppercase;letter-spacing:1.2px;margin-bottom:5px;font-weight:700;
}
.field input{
  width:100%;padding:12px 14px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(48,54,61,.8);
  border-radius:8px;color:#e6edf3;font-size:14px;outline:none;
  transition:.2s;
}
.field input:focus{
  border-color:#7c5cfc;
  background:rgba(124,92,252,.05);
  box-shadow:0 0 0 3px rgba(124,92,252,.15);
}
.field input::placeholder{color:#30363d}
.btn{
  width:100%;padding:13px;border:none;border-radius:9px;cursor:pointer;
  background:linear-gradient(135deg,#e74c3c,#c0392b,#8e44ad);color:#fff;
  font-weight:700;font-size:14px;transition:.25s;margin-top:6px;
  box-shadow:0 4px 16px rgba(192,57,43,.45);
  letter-spacing:.8px;position:relative;overflow:hidden;
}
.btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.1),transparent);
  opacity:0;transition:.2s;
}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(124,92,252,.55)}
.btn:hover::before{opacity:1}
.btn:active{transform:translateY(0)}
.msg{
  margin-top:12px;padding:11px 14px;border-radius:8px;font-size:12.5px;text-align:center;
  display:flex;align-items:center;justify-content:center;gap:6px;
}
.msg.error{background:rgba(248,81,73,.08);border:1px solid rgba(248,81,73,.25);color:#f85149}
.msg.success{background:rgba(46,160,67,.08);border:1px solid rgba(46,160,67,.25);color:#3fb950}
.msg.pending{background:rgba(255,170,0,.08);border:1px solid rgba(255,170,0,.25);color:#e3a008}
.divider{
  display:flex;align-items:center;gap:10px;
  margin:16px 0;color:#30363d;font-size:11px;
}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:rgba(48,54,61,.6)}
.foot{
  text-align:center;margin-top:18px;padding-top:14px;
  border-top:1px solid rgba(48,54,61,.4);
  font-size:11px;color:#30363d;
}
.foot a{color:#7c5cfc;text-decoration:none;transition:.2s}
.foot a:hover{color:#a78bfa}

/* Particles */
.particles{position:fixed;inset:0;pointer-events:none;z-index:2;overflow:hidden}
.particle{
  position:absolute;border-radius:50%;
  background:rgba(124,92,252,.5);animation:float linear infinite;
}
@keyframes float{
  0%{transform:translateY(100vh) scale(0);opacity:0}
  10%{opacity:1;transform:translateY(80vh) scale(1)}
  90%{opacity:.6}
  100%{transform:translateY(-5vh) scale(.5) rotate(360deg);opacity:0}
}
</style>
</head>
<body>
<div class="orb orb1"></div>
<div class="orb orb2"></div>
<div class="particles" id="ptcls"></div>
<audio id="ea" autoplay loop preload="auto"><source src="''' + ENTRY_SOUND_URL + r'''" type="audio/mp4"></audio>

<div class="wrap">
  <div class="card">

    <!-- ── Logo Block ── -->
    <div class="logo-block">
      <img class="logo-img"
           src="https://i.ibb.co/60Zvqk5L/photo.jpg"
           alt="SERVER HUB"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
      <div style="display:none;width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#7c5cfc,#00bfff);align-items:center;justify-content:center;font-size:36px;border:3px solid rgba(124,92,252,.5);box-shadow:0 0 30px rgba(124,92,252,.4)">🚀</div>
      <div class="logo-title">SERVER HUB</div>
      <div class="logo-sub">Professional Hosting Panel</div>
    </div>

    <!-- ── Forms Block ── -->
    <div class="forms-area">
      <div class="tabs">
        <div class="tab active" data-f="login">🔐 Sign In</div>
        <div class="tab" data-f="register">✨ Register</div>
      </div>

      <form class="form active" id="login-form" method="post" action="/login">
        <div class="field"><label>Username</label><input name="username" placeholder="Enter your username" required autofocus autocomplete="username"></div>
        <div class="field"><label>Password</label><input type="password" name="password" placeholder="Enter your password" required autocomplete="current-password"></div>
        <button class="btn" type="submit">Sign In →</button>
        {% if error and error_type == 'login' %}
          <div class="msg {% if 'pending' in error.lower() or 'waiting' in error.lower() or 'approval' in error.lower() %}pending{% else %}error{% endif %}">{{ error }}</div>
        {% endif %}
      </form>

      <form class="form" id="register-form" method="post" action="/register">
        <div class="field"><label>Username</label><input name="username" placeholder="Choose a username" required autocomplete="username"></div>
        <div class="field"><label>🔵 Telegram Username <span style="color:#f85149">*</span></label><input name="tg_username" placeholder="@yourusername" required autocomplete="off"></div>
        <div class="field"><label>Password</label><input type="password" name="password" placeholder="Min 4 characters" required autocomplete="new-password"></div>
        <div class="field"><label>Confirm Password</label><input type="password" name="confirm_password" placeholder="Repeat password" required autocomplete="new-password"></div>
        <button class="btn" type="submit">Create Account →</button>
        {% if error and error_type == 'register' %}
          <div class="msg {% if '✅' in error or 'sent' in error.lower() %}success{% else %}error{% endif %}">{{ error }}</div>
        {% endif %}
      </form>

      <div class="foot">SERVER HUB &copy; 2025 &nbsp;·&nbsp; By <a href="https://t.me/Y0YY12" target="_blank">@Y0YY12</a></div>
    </div>

  </div>
</div>

<script>
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    const fid=t.dataset.f;
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.form').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById(fid+'-form').classList.add('active');
  });
});
{% if error and error_type == 'register' %}
document.querySelectorAll('.tab').forEach(t=>{if(t.dataset.f==='register')t.click();});
{% endif %}
(function(){
  var a=document.getElementById('ea');
  if(!a)return;a.volume=0.35;
  function p(){var r=a.play();if(r)r.catch(()=>{});}
  p();setInterval(()=>{if(a.paused)p();},1000);
  ['click','keydown','touchstart'].forEach(e=>document.addEventListener(e,p,{once:true}));
})();
(function(){
  var c=document.getElementById('ptcls');
  for(var i=0;i<18;i++){
    var d=document.createElement('div');
    var s=2+Math.random()*4;
    d.className='particle';
    d.style.cssText='left:'+(Math.random()*100)+'%;width:'+s+'px;height:'+s+'px;animation-duration:'+(10+Math.random()*14)+'s;animation-delay:'+(-Math.random()*24)+'s';
    c.appendChild(d);
  }
})();
</script>
</body>
</html>
'''

# ─────────────────────────────────────────────────────────────────────────────
#  19.  MAIN DASHBOARD TEMPLATE  (SERVER HUB)
# ─────────────────────────────────────────────────────────────────────────────
def get_html_template(is_master, username=None):
    extra_tabs = ''
    if is_master:
        extra_tabs = '''
        <div class="tab-item" data-tab="ai" style="color:#a78bfa;font-weight:600">🤖 AI</div>
        <div class="tab-item" data-tab="users">👥 Users</div>
        <div class="tab-item" data-tab="hosting" style="color:#06b6d4;font-weight:600">🌐 Hosting</div>
        <div class="tab-item" data-tab="cmds">⌨️ Commands</div>
        <div class="tab-item" data-tab="backups">💾 Backup</div>
        <div class="tab-item" data-tab="network">🌐 Net</div>
        <div class="tab-item" data-tab="startup">🚀 Startup</div>
        <div class="tab-item" data-tab="settings">⚙️ Settings</div>
        <div class="tab-item" data-tab="activity">📋 Log</div>
        <div class="tab-item" data-tab="owner" style="color:#7c5cfc;font-weight:700">👑 Owner</div>
        '''
    else:
        extra_tabs = '''
        <div class="tab-item" data-tab="ai" style="color:#a78bfa;font-weight:600">🤖 AI</div>
        <div class="tab-item" data-tab="hosting" style="color:#06b6d4;font-weight:600">🌐 Hosting</div>
        <div class="tab-item" data-tab="cmds">⌨️ Commands</div>
        <div class="tab-item" data-tab="settings">⚙️ Settings</div>
        <div class="tab-item" data-tab="activity">📋 Log</div>
        '''

    owner_panel_html = ''
    if is_master:
        owner_panel_html = r'''
<!-- ===== OWNER TAB ===== -->
<div class="tab-content" id="tab-owner">
  <!-- Stats Row -->
  <div class="stats4">
    <div class="stat4 purple"><div class="s4lbl">Total Users</div><div class="s4val" id="ow-users">—</div></div>
    <div class="stat4 blue"><div class="s4lbl">Servers</div><div class="s4val" id="ow-servers">—</div></div>
    <div class="stat4 green"><div class="s4lbl">Active Bots</div><div class="s4val" id="ow-bots">—</div></div>
    <div class="stat4 orange"><div class="s4lbl">ZIP Files</div><div class="s4val" id="ow-zips">—</div></div>
  </div>

  <!-- Maintenance -->
  <div class="section-card">
    <div class="section-head">🔧 Maintenance Mode</div>
    <div class="section-body">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <label class="toggle-switch">
          <input type="checkbox" id="maint-toggle-chk" onchange="toggleMaintenance()">
          <span class="slider"></span>
        </label>
        <span style="color:#8b949e;font-size:13px">Enable Maintenance Mode</span>
      </div>
      <div class="field-block"><label>Maintenance Message</label>
        <textarea id="maint-msg" rows="2" style="width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#e6edf3;font-size:13px;resize:vertical"></textarea>
      </div>
      <button class="btn-action" onclick="saveMaintMsg()">Save Message</button>
    </div>
  </div>

  <!-- Telegram Bot -->
  <div class="section-card">
    <div class="section-head">🤖 Telegram Bot Integration</div>
    <div class="section-body">
      <div id="bot-status-badge" style="margin-bottom:12px"></div>
      <div class="field-block"><label>Bot Token</label><input id="tg-token" type="password" placeholder="1234567890:AAF..."></div>
      <div class="field-block"><label>Owner Telegram ID</label><input id="tg-ownerid" placeholder="123456789"></div>
      <div id="bot-link-status" style="color:#8b949e;font-size:12px;margin-bottom:8px"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn-action" onclick="linkBot()">🔗 Link Bot</button>
        <button class="btn-action gray" onclick="unlinkBot()">🔓 Unlink</button>
      </div>
      <div id="bot-control-panel" style="display:none;margin-top:16px">
        <div class="section-head" style="margin-bottom:8px">Bot Control</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <button class="btn-action green" onclick="botAction('start')">▶ Start</button>
          <button class="btn-action" onclick="botAction('restart')">↺ Restart</button>
          <button class="btn-action danger" onclick="botAction('stop')">■ Stop</button>
          <button class="btn-action gray" onclick="refreshBotStats()">🔄 Refresh</button>
        </div>
        <div class="console-box" id="bot-console" style="height:120px"></div>
        <div class="cmd-input" style="margin-top:8px">
          <span class="prompt">$</span>
          <input id="bot-cmd-input" placeholder="Send command..." onkeydown="if(event.key==='Enter')sendBotCmd()">
        </div>
      </div>
    </div>
  </div>

  <!-- Panel Settings -->
  <div class="section-card">
    <div class="section-head">⚙️ Panel Settings</div>
    <div class="section-body">
      <div class="field-block"><label>Panel Name</label><input id="panel-name-inp" placeholder="SERVER HUB"></div>
      <div class="field-block"><label>Welcome Message</label><input id="panel-welcome-inp" placeholder="Welcome!"></div>
      <button class="btn-action" onclick="savePanelSettings()">Save Settings</button>
    </div>
  </div>

  <!-- Announcements -->
  <div class="section-card">
    <div class="section-head">📢 Announcements</div>
    <div class="section-body">
      <div class="field-block"><label>New Announcement</label><input id="ann-txt" placeholder="Type announcement..."></div>
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button class="btn-action" onclick="addAnnouncement()">Add</button>
        <button class="btn-action gray" onclick="ownerBroadcast()">📡 Broadcast</button>
      </div>
      <div id="ann-list"></div>
    </div>
  </div>

  <!-- ZIP Files -->
  <div class="section-card">
    <div class="section-head">📦 User ZIP Files</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <button class="btn-action" onclick="loadOwnerZips()">🔄 Refresh</button>
        <button class="btn-action green" onclick="downloadAllZips()">⬇ Download All</button>
      </div>
      <div id="owner-zip-list"></div>
    </div>
  </div>

  <!-- Pending Registrations -->
  <div class="section-card">
    <div class="section-head">⏳ Pending Account Approvals</div>
    <div class="section-body">
      <button class="btn-action" onclick="loadPendingUsers()" style="margin-bottom:10px">🔄 Refresh</button>
      <div id="pending-users-list"></div>
    </div>
  </div>

  <!-- Security Alerts -->
  <div class="section-card" style="border-color:rgba(248,81,73,.4)">
    <div class="section-head" style="color:#f85149">🛡️ Security Alerts — ملفات مشبوهة</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        <button class="btn-action gray" onclick="loadSecurityAlerts()">🔄 Refresh</button>
        <button class="btn-action danger" onclick="clearSecurityAlerts()">🗑 Clear All</button>
      </div>
      <div id="security-alerts-list">
        <div style="color:var(--text3);padding:10px;text-align:center">اضغط Refresh لتحميل التنبيهات</div>
      </div>
    </div>
  </div>

  <!-- Danger Zone -->
  <div class="section-card" style="border-color:#f85149">
    <div class="section-head" style="color:#f85149">⚠️ Danger Zone</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn-action danger" onclick="ownerAction('clear_all_logs')">🗑 Clear All Logs</button>
        <button class="btn-action danger" onclick="ownerAction('kick_all_users')">👢 Kick All Users</button>
        <button class="btn-action danger" onclick="ownerAction('reset_stats')">📊 Reset Stats</button>
        <button class="btn-action gray" onclick="ownerAction('restart_panel')">🔄 Restart Panel</button>
      </div>
    </div>
  </div>
</div>
'''

    return r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SERVER HUB — Control Panel</title>
<style>
:root{
  --bg:#080b12;--bg2:#0c1018;--bg3:#111620;--bg4:#161d28;
  --border:#1e2738;--border2:#2a3548;
  --accent:#c0392b;--accent2:#e74c3c;--accent3:#8e44ad;
  --neon:#ff2d55;--neon2:#a855f7;
  --green:#27ae60;--red:#e74c3c;--yellow:#f39c12;--orange:#e67e22;
  --text:#eaf0fb;--text2:#8899b0;--text3:#3d5068;
}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter','Segoe UI',sans-serif}
html,body{background:var(--bg);color:var(--text);min-height:100vh}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}

/* ── TOPBAR ── */
.topbar{
  background:var(--bg2);border-bottom:1px solid var(--border);
  padding:0 20px;height:56px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(0,0,0,.4);
}
.topbar .brand{
  font-size:18px;font-weight:800;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  display:flex;align-items:center;gap:8px;
}
.topbar .brand-icon{font-size:20px;-webkit-text-fill-color:initial}
.topbar .icons{display:flex;gap:10px;align-items:center}
.topbar .ic{
  color:var(--text2);font-size:17px;cursor:pointer;
  background:none;border:0;padding:6px;border-radius:6px;
  transition:.2s;
}
.topbar .ic:hover{color:var(--text);background:var(--bg3)}
.topbar .avatar{
  width:30px;height:30px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:700;color:#fff;cursor:default;
  border:2px solid rgba(124,92,252,.4);
}
.user-badge{
  display:flex;align-items:center;gap:8px;
  background:var(--bg3);border:1px solid var(--border);
  border-radius:20px;padding:4px 12px 4px 4px;
  font-size:12px;color:var(--text2);
}
.status-dot{
  width:8px;height:8px;border-radius:50%;background:var(--green);
  animation:blink 2s ease-in-out infinite;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}

/* ── TABS ── */
.tabs{
  background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;overflow-x:auto;padding:0 12px;
  scrollbar-width:none;gap:0;position:sticky;top:0;z-index:10;
}
.tabs::-webkit-scrollbar{display:none}
.tab-item{
  padding:12px 15px;color:var(--text3);cursor:pointer;
  font-size:12.5px;white-space:nowrap;font-weight:500;
  border-bottom:2px solid transparent;transition:.15s;user-select:none;
  display:flex;align-items:center;gap:6px;letter-spacing:.2px;
}
.tab-item:hover{color:var(--text);background:rgba(255,255,255,.03)}
.tab-item.active{
  color:var(--accent);border-bottom-color:var(--accent);
  font-weight:600;background:rgba(124,92,252,.06);
}

/* ── CONTAINER ── */
.container{max-width:1400px;margin:0 auto;padding:8px 12px}
.tab-content{display:none;animation:fadein .15s}
.tab-content.active{display:block}
/* console tab fills viewport height */
#tab-console{display:none;flex-direction:column}
#tab-console.active{display:flex;flex-direction:column;height:calc(100vh - 110px)}
@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* ── CONSOLE ── */
.power-row{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:5px;margin-bottom:6px;align-items:center}
.btn-power{
  padding:7px 6px;border:none;border-radius:6px;font-weight:600;
  font-size:11.5px;cursor:pointer;color:#fff;transition:.2s;letter-spacing:.3px;
}
.btn-start{background:linear-gradient(135deg,#1a7f37,#2ea043);box-shadow:0 2px 8px rgba(46,160,67,.3)}
.btn-start:hover{filter:brightness(1.1)}
.btn-restart{background:linear-gradient(135deg,#5a3fc0,#7c5cfc);box-shadow:0 2px 8px rgba(124,92,252,.3)}
.btn-restart:hover{filter:brightness(1.1)}
.btn-stop{background:linear-gradient(135deg,#b62324,#f85149);box-shadow:0 2px 8px rgba(248,81,73,.3)}
.btn-stop:hover{filter:brightness(1.1)}
.status-badge{
  display:flex;align-items:center;gap:6px;
  font-size:12px;font-weight:600;padding:8px 12px;
  background:var(--bg3);border:1px solid var(--border);border-radius:20px;
  white-space:nowrap;
}

/* ── VS Code-style terminal ── */
.term-window{
  background:#0d1117;border:1px solid #21262d;border-radius:10px;
  overflow:hidden;display:flex;flex-direction:column;
  flex:1;min-height:0;
  box-shadow:0 4px 24px rgba(0,0,0,.5);
}
#terminals-container{flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden}
#terminals-container>[id^="term-wrap-"]{flex:1;display:flex;flex-direction:column;min-height:0}
.term-titlebar{
  display:flex;align-items:center;gap:6px;
  background:#161b22;border-bottom:1px solid #21262d;
  padding:6px 12px;flex-shrink:0;user-select:none;
}
.term-dot{width:11px;height:11px;border-radius:50%;cursor:pointer;flex-shrink:0}
.term-dot.red{background:#ff5f57}.term-dot.yellow{background:#febc2e}.term-dot.green{background:#28c840}
.term-title{flex:1;text-align:center;font-size:11px;color:#8b949e;font-family:monospace;letter-spacing:.5px}
.term-output{
  flex:1;overflow-y:auto;padding:12px 16px 6px;
  font-family:'Fira Code','Cascadia Code','Consolas',monospace;
  font-size:13px;line-height:1.7;color:#c9d1d9;
  white-space:pre-wrap;word-break:break-word;cursor:text;
  scroll-behavior:smooth;
}
.term-output::-webkit-scrollbar{width:6px}
.term-output::-webkit-scrollbar-track{background:transparent}
.term-output::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
.term-input-row{
  display:flex;align-items:center;gap:0;
  background:#010409;border-top:2px solid #21262d;
  padding:8px 14px;flex-shrink:0;
}
.term-prompt-label{
  color:#00ff41;font-family:'Fira Code',monospace;font-size:12.5px;
  white-space:nowrap;pointer-events:none;user-select:none;margin-right:8px;
  line-height:1;flex-shrink:0;
}
.term-field{
  flex:1;background:none;border:0;outline:0;
  color:#e6edf3;font-family:'Fira Code',monospace;font-size:13.5px;
  padding:6px 0;direction:ltr;unicode-bidi:embed;caret-color:#00ff41;
  min-width:0;
}
.term-field::placeholder{color:#3d444d;font-size:12px}
.term-send-btn{
  background:none;border:none;color:#3d444d;cursor:pointer;
  font-size:18px;padding:4px 8px;transition:.15s;flex-shrink:0;
}
.term-send-btn:hover{color:#00ff41}
/* output line colors */
.t-err{color:#ff6b6b}.t-warn{color:#d29922}.t-ok{color:#3fb950}
.t-prompt{color:#00ff41}.t-cmd{color:#79c0ff;font-weight:600}
.t-dim{color:#6e7681}.t-special{color:#e3b341}
/* quick install buttons */
/* quickbar removed */

/* ── Hosting deploy output ── */
.deploy-out{
  margin-top:10px;background:#010409;border:1px solid #21262d;
  border-radius:8px;padding:12px;font-family:'Fira Code',monospace;
  font-size:12px;color:#7ee787;max-height:160px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-all;
}
.deploy-out.err{color:#ff6b6b}

/* ── Commands accordion ── */
.cmd-group{border:1px solid var(--border);border-radius:8px;overflow:hidden}
.cmd-group-head{
  display:flex;justify-content:space-between;align-items:center;
  padding:10px 14px;background:var(--bg3);cursor:pointer;
  font-size:13px;font-weight:600;color:var(--text);transition:.15s;
  user-select:none;
}
.cmd-group-head:hover{background:var(--bg2)}
.cmd-group-body{padding:10px 12px;background:var(--bg)}
.cmd-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
  gap:6px;
}
.cmd-item{
  padding:7px 10px;background:var(--bg3);border:1px solid var(--border);
  border-radius:6px;font-family:'Fira Code',monospace;font-size:11.5px;
  color:#79c0ff;cursor:pointer;transition:.15s;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;
}
.cmd-item:hover{background:#161b22;border-color:#58a6ff;color:#c9d1d9}
.cmd-item:active{transform:scale(.97)}
/* old cmd-input hidden/unused */
.cmd-input{display:none}
.console-box{display:none}

/* ── STATS GRID ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:6px;margin-bottom:8px}
.stat-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:7px;
  padding:8px 10px;position:relative;overflow:hidden;
  transition:.2s;
}
.stat-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2));
}
.stat-card:hover{border-color:var(--accent)}
.stat-card .lbl{font-size:9px;color:var(--text2);text-transform:uppercase;letter-spacing:.6px;margin-bottom:3px;font-weight:600}
.stat-card .val{font-size:12px;color:var(--text);font-weight:700}
.stat-card .val .max{color:var(--text3);font-weight:400;font-size:10px}
.stat-card.green::before{background:var(--green)}
.stat-card.red::before{background:var(--red)}
.stat-card.yellow::before{background:var(--yellow)}
.stat-card.orange::before{background:var(--orange)}

/* ── SECTION CARD ── */
.section-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:12px;
  margin-bottom:14px;overflow:hidden;
}
.section-head{
  padding:12px 16px;background:var(--bg4);border-bottom:1px solid var(--border);
  font-size:12px;font-weight:700;color:var(--text2);text-transform:uppercase;
  letter-spacing:1px;display:flex;align-items:center;gap:6px;
}
.section-body{padding:16px}

/* ── FILES ── */
.file-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.file-toolbar button{
  padding:8px 14px;border:1px solid var(--border);border-radius:6px;
  background:var(--bg4);color:var(--text);font-size:12px;cursor:pointer;
  font-weight:500;transition:.15s;display:flex;align-items:center;gap:4px;
}
.file-toolbar button:hover{background:var(--accent);border-color:var(--accent);color:#fff}
.breadcrumb{
  padding:8px 12px;background:var(--bg2);border:1px solid var(--border);
  border-radius:6px;font-size:12px;color:var(--text2);font-family:monospace;
  margin-bottom:10px;overflow-x:auto;white-space:nowrap;
}
.file-list{
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;overflow:hidden;
}
.file-item{
  display:flex;align-items:center;padding:10px 14px;
  border-bottom:1px solid var(--border);cursor:pointer;
  transition:.15s;gap:10px;
}
.file-item:last-child{border-bottom:none}
.file-item:hover{background:var(--bg4)}
.file-icon{font-size:16px;width:24px;text-align:center;flex-shrink:0}
.file-name{flex:1;font-size:13px;color:var(--text);font-weight:500;word-break:break-all}
.file-size{font-size:11px;color:var(--text3);flex-shrink:0}
.file-actions{display:flex;gap:4px;flex-shrink:0}
.file-actions button{
  padding:4px 8px;border:none;border-radius:4px;font-size:11px;cursor:pointer;
  background:var(--bg4);color:var(--text2);transition:.15s;
}
.file-actions button:hover{background:var(--accent);color:#fff}
.file-actions button.danger:hover{background:var(--red)}

/* ── AI CHAT ── */
.ai-chat-wrap{
  display:flex;flex-direction:column;
  height:calc(100vh - 130px);min-height:500px;max-height:800px;
  background:var(--bg2);border:1px solid rgba(124,92,252,.2);
  border-radius:16px;overflow:hidden;
  box-shadow:0 0 40px rgba(124,92,252,.05);
}
.ai-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 18px;
  background:linear-gradient(90deg,rgba(124,92,252,.08),rgba(0,191,255,.04),transparent);
  border-bottom:1px solid rgba(48,54,61,.7);
  flex-shrink:0;
}
.ai-header-left{display:flex;align-items:center;gap:12px}
.ai-avatar-main{
  width:38px;height:38px;border-radius:50%;
  background:linear-gradient(135deg,#7c5cfc,#5a3fc0);
  display:flex;align-items:center;justify-content:center;
  font-size:18px;flex-shrink:0;
  box-shadow:0 0 16px rgba(124,92,252,.4);
}
.ai-header-title{font-size:14px;font-weight:700;color:var(--text)}
.ai-header-sub{font-size:11px;color:var(--text3);margin-top:2px}
.ai-clear-btn{
  background:none;border:1px solid rgba(48,54,61,.6);color:var(--text3);
  border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;transition:.2s;
}
.ai-clear-btn:hover{background:rgba(248,81,73,.1);border-color:rgba(248,81,73,.3);color:#f85149}

.ai-messages-box{
  flex:1;overflow-y:auto;padding:16px;
  display:flex;flex-direction:column;gap:14px;
  background:#010409;
  scrollbar-width:thin;scrollbar-color:#30363d #010409;
}
.ai-messages-box::-webkit-scrollbar{width:5px}
.ai-messages-box::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}

.ai-msg{display:flex;flex-direction:column;animation:fadeUp .2s ease}
.ai-bubble{display:flex;gap:10px;align-items:flex-start;max-width:86%}
.ai-msg.ai-user .ai-bubble{flex-direction:row-reverse;margin-left:auto;max-width:80%}
.ai-avatar{
  width:30px;height:30px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:14px;
  background:var(--bg3);border:1px solid var(--border);margin-top:2px;
}
.ai-msg.ai-user .ai-avatar{
  background:linear-gradient(135deg,#7c5cfc,#5a3fc0);border-color:transparent;
  font-size:12px;color:#fff;font-weight:700;
}
.ai-text{
  padding:11px 15px;border-radius:14px;font-size:13.5px;line-height:1.7;
  background:rgba(255,255,255,.04);border:1px solid rgba(48,54,61,.6);
  color:var(--text);white-space:pre-wrap;word-break:break-word;
  border-bottom-left-radius:4px;
}
.ai-msg.ai-user .ai-text{
  background:linear-gradient(135deg,rgba(124,92,252,.18),rgba(90,63,192,.12));
  border-color:rgba(124,92,252,.25);
  border-bottom-right-radius:4px;border-bottom-left-radius:14px;
  text-align:right;direction:rtl;
}
.ai-text code{
  background:rgba(124,92,252,.12);padding:2px 7px;border-radius:5px;
  font-family:'Fira Code','Consolas',monospace;font-size:12px;color:#a78bfa;
}
.ai-text pre{
  background:#0d1117;border:1px solid rgba(48,54,61,.8);border-radius:10px;
  padding:14px;overflow-x:auto;margin:10px 0;position:relative;
}
.ai-text pre code{background:none;padding:0;color:#7ee787;font-size:12px;display:block}
.ai-time{font-size:10px;color:var(--text3);margin-top:4px;padding:0 4px}
.ai-msg.ai-user .ai-time{text-align:right}

/* Thinking */
.ai-thinking-box{
  padding:10px 16px;flex-shrink:0;
  background:rgba(124,92,252,.03);border-top:1px solid rgba(48,54,61,.5);
}
.ai-thinking-label{
  display:flex;align-items:center;gap:8px;
  font-size:11px;color:#7c5cfc;font-weight:600;letter-spacing:.5px;margin-bottom:6px;
}
.ai-think-dots{display:flex;gap:3px;align-items:center}
.ai-think-dots span{width:5px;height:5px;border-radius:50%;background:#7c5cfc;animation:typingDot 1.2s ease-in-out infinite}
.ai-think-dots span:nth-child(2){animation-delay:.2s}
.ai-think-dots span:nth-child(3){animation-delay:.4s}
.ai-reasoning-text{
  font-size:11px;color:#484f58;font-family:'Fira Code','Consolas',monospace;
  max-height:80px;overflow-y:auto;line-height:1.6;white-space:pre-wrap;
}

/* Input */
.ai-input-area{
  flex-shrink:0;padding:12px 14px;
  border-top:1px solid rgba(48,54,61,.6);
  background:rgba(255,255,255,.01);
}
.ai-input-row{display:flex;gap:10px;align-items:flex-end}
.ai-textarea{
  flex:1;padding:11px 14px;min-height:42px;max-height:120px;
  background:rgba(255,255,255,.04);border:1px solid rgba(48,54,61,.8);
  border-radius:12px;color:var(--text);font-size:13.5px;
  outline:none;resize:none;transition:.2s;font-family:inherit;line-height:1.55;
  direction:auto;overflow-y:auto;
}
.ai-textarea:focus{
  border-color:#7c5cfc;
  background:rgba(124,92,252,.04);
  box-shadow:0 0 0 3px rgba(124,92,252,.1);
}
.ai-textarea::placeholder{color:#30363d}
.ai-send-btn{
  width:42px;height:42px;flex-shrink:0;
  background:linear-gradient(135deg,#7c5cfc,#5a3fc0);
  border:none;border-radius:12px;color:#fff;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:.2s;box-shadow:0 4px 14px rgba(124,92,252,.35);
}
.ai-send-btn:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(124,92,252,.5)}
.ai-send-btn:active{transform:translateY(0)}
.ai-send-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.ai-footer-info{font-size:10.5px;color:var(--text3);margin-top:7px;text-align:center}

/* Typing indicator */
.ai-typing-wrap{display:flex;align-items:center;gap:10px}
.ai-typing{display:flex;gap:4px;align-items:center;padding:10px 14px;background:rgba(255,255,255,.04);border:1px solid rgba(48,54,61,.6);border-radius:14px;border-bottom-left-radius:4px}
.ai-typing span{width:6px;height:6px;border-radius:50%;background:#7c5cfc;animation:typingDot 1.2s ease-in-out infinite}
.ai-typing span:nth-child(2){animation-delay:.2s}
.ai-typing span:nth-child(3){animation-delay:.4s}
@keyframes typingDot{0%,60%,100%{transform:translateY(0);opacity:.3}30%{transform:translateY(-5px);opacity:1}}

/* ── DROP ZONE (kept minimal for JS compat) ── */

/* ── BUTTONS ── */
.btn-action{
  padding:8px 16px;border:none;border-radius:6px;cursor:pointer;
  background:linear-gradient(135deg,var(--accent),#5a3fc0);color:#fff;
  font-weight:600;font-size:12px;transition:.2s;letter-spacing:.3px;
}
.btn-action:hover{filter:brightness(1.1);transform:translateY(-1px)}
.btn-action.gray{background:var(--bg4);border:1px solid var(--border);color:var(--text2)}
.btn-action.gray:hover{background:var(--border);color:var(--text)}
.btn-action.green{background:linear-gradient(135deg,#1a7f37,#2ea043)}
.btn-action.danger{background:linear-gradient(135deg,#b62324,#f85149)}
.btn-action.orange{background:linear-gradient(135deg,var(--orange),#c7541f)}

/* ── FORMS ── */
.field-block{margin-bottom:12px}
.field-block label{display:block;font-size:11px;color:var(--text2);font-weight:600;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px}
.field-block input,.field-block select,.field-block textarea{
  width:100%;padding:10px 12px;background:var(--bg2);
  border:1px solid var(--border);border-radius:6px;color:var(--text);
  font-size:13px;outline:none;transition:.2s;
}
.field-block input:focus,.field-block select:focus,.field-block textarea:focus{
  border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,92,252,.15);
}
.field-block input::placeholder{color:var(--text3)}
.row-end{display:flex;justify-content:flex-end;gap:8px;margin-top:10px}

/* ── MODAL ── */
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.modal.open{display:flex}
.modal-box{background:var(--bg3);border:1px solid var(--border);border-radius:16px;width:min(540px,94vw);max-height:90vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.modal-head{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-head h3{font-size:16px;font-weight:700;color:var(--text)}
.modal-head .close{background:none;border:0;color:var(--text2);font-size:22px;cursor:pointer;line-height:1;padding:0 4px}
.modal-head .close:hover{color:var(--text)}
.modal-body{padding:20px;overflow-y:auto;flex:1}
.modal-foot{padding:14px 20px;border-top:1px solid var(--border);display:flex;gap:8px;justify-content:flex-end}

/* ── EDITOR ── */
.editor-wrap{position:relative}
.editor-box{
  width:100%;min-height:320px;padding:14px;
  background:#010409;border:1px solid var(--border);border-radius:8px;
  color:#7ee787;font-family:monospace;font-size:13px;
  outline:none;resize:vertical;line-height:1.6;tab-size:2;
}
.editor-box:focus{border-color:var(--accent)}

/* ── NODE.JS TAB ── */
.nodejs-project-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:14px;margin-bottom:10px;
  display:flex;align-items:center;justify-content:space-between;
  gap:12px;
}
.project-info .p-name{font-size:14px;font-weight:700;color:var(--text)}
.project-info .p-meta{font-size:11px;color:var(--text2);margin-top:3px}
.p-status{font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px}
.p-status.running{background:rgba(46,160,67,.15);color:var(--green);border:1px solid rgba(46,160,67,.3)}
.p-status.stopped{background:rgba(248,81,73,.1);color:var(--red);border:1px solid rgba(248,81,73,.2)}
.log-box{
  background:#010409;border:1px solid var(--border);border-radius:6px;
  padding:10px;font-family:monospace;font-size:11px;color:#7ee787;
  height:180px;overflow-y:auto;margin-top:8px;white-space:pre-wrap;
}

/* ── PHP TAB ── */
.php-server-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:14px;margin-bottom:10px;
}

/* ── OWNER STATS ── */
.stats4{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:14px}
.stat4{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center;position:relative;overflow:hidden}
.stat4::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat4.purple::before{background:var(--accent)}
.stat4.blue::before{background:var(--accent2)}
.stat4.green::before{background:var(--green)}
.stat4.orange::before{background:var(--orange)}
.s4lbl{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.s4val{font-size:28px;font-weight:800;color:var(--text)}

/* ── TOGGLE SWITCH ── */
.toggle-switch{position:relative;width:44px;height:24px;flex-shrink:0}
.toggle-switch input{display:none}
.slider{
  position:absolute;inset:0;background:var(--bg4);border:1px solid var(--border);
  border-radius:24px;cursor:pointer;transition:.3s;
}
.slider:before{
  content:'';position:absolute;left:3px;top:3px;
  width:16px;height:16px;border-radius:50%;
  background:var(--text2);transition:.3s;
}
input:checked + .slider{background:var(--accent);border-color:var(--accent)}
input:checked + .slider:before{transform:translateX(20px);background:#fff}

/* ── TOAST ── */
.toast-container{position:fixed;bottom:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:8px}
.toast{
  padding:12px 18px;border-radius:10px;font-size:13px;font-weight:600;
  color:#fff;display:flex;align-items:center;gap:8px;
  animation:slideIn .3s ease;box-shadow:0 4px 20px rgba(0,0,0,.4);
  max-width:300px;
}
.toast.ok{background:linear-gradient(135deg,#1a7f37,#2ea043)}
.toast.err{background:linear-gradient(135deg,#b62324,#f85149)}
.toast.info{background:linear-gradient(135deg,var(--accent),#5a3fc0)}
@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}

/* ── SERVERS MODAL ── */
.srv-card{
  display:flex;align-items:center;justify-content:space-between;
  background:var(--bg4);border:1px solid var(--border);border-radius:8px;
  padding:12px 14px;margin-bottom:8px;transition:.15s;
}
.srv-card:hover{border-color:var(--accent)}
.srv-name{font-size:14px;font-weight:600;color:var(--text)}
.srv-meta{font-size:12px;color:var(--text2);margin-top:2px}
.srv-del-btn{
  background:var(--red);border:none;border-radius:6px;
  color:#fff;font-size:16px;width:32px;height:32px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:.15s;flex-shrink:0;
}
.srv-del-btn:hover{filter:brightness(1.2)}

/* ── ZIP ITEMS ── */
.zip-item{
  display:flex;justify-content:space-between;align-items:center;
  background:var(--bg4);border:1px solid var(--border);border-radius:6px;
  padding:10px 12px;margin-bottom:6px;
}
.z-name{color:var(--text);font-size:13px;font-family:monospace}
.z-size{color:var(--text2);font-size:11px;margin-top:2px}

/* ── PENDING ── */
.pending-card{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  background:var(--bg4);border:1px solid rgba(255,170,0,.3);border-radius:8px;
  padding:10px 14px;margin-bottom:8px;
}
.pending-card .p-user{font-size:13px;font-weight:600;color:var(--text)}
.pending-card .p-time{font-size:11px;color:var(--text2);margin-top:2px}

/* ── RESPONSIVE ── */
@media(max-width:600px){
  .stats-grid{grid-template-columns:1fr 1fr}
  .power-row{grid-template-columns:1fr 1fr 1fr;gap:6px}
  .power-row .status-badge{display:none}
  .topbar .brand{font-size:15px}
  .container{padding:12px 10px}
  .stats4{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="brand">
    <span class="brand-icon">🚀</span> SERVER HUB
  </div>
  <div class="icons">
    <button class="ic" onclick="loadSearch()" title="Search">🔍</button>
    <button class="ic" onclick="openServersModal()" title="Servers">🗂</button>
    <div class="user-badge">
      <div class="status-dot"></div>
      <span id="topbar-user">''' + html.escape(username or '') + r'''</span>
    </div>
    <button class="ic" onclick="location.href='/logout'" title="Logout">⏏</button>
  </div>
</div>

<!-- TABS -->
<div class="tabs" id="tabs">
  <div class="tab-item active" data-tab="console">⬛ Terminal</div>
  <div class="tab-item" data-tab="files">📁 Files</div>
  <div class="tab-item" data-tab="databases">🗄 DB</div>
  <div class="tab-item" data-tab="schedules">⏰ Cron</div>
  ''' + extra_tabs + r'''
</div>

<div class="container">
<div id="toast-container" class="toast-container"></div>

<!-- ===== CONSOLE TAB ===== -->
<div class="tab-content active" id="tab-console">
  <!-- ── Power row ── -->
  <div class="power-row">
    <button class="btn-power btn-start"   onclick="powerAction('start')">▶ Start</button>
    <button class="btn-power btn-restart" onclick="powerAction('restart')">↺ Restart</button>
    <button class="btn-power btn-stop"    onclick="powerAction('stop')">■ Stop</button>
    <div class="status-badge">
      <span id="proc-dot" style="width:8px;height:8px;border-radius:50%;background:#f85149;display:inline-block"></span>
      <span id="proc-status">Stopped</span>
    </div>
  </div>

  <!-- ── Terminal tabs bar ── -->
  <div id="term-tabs-bar" style="display:flex;align-items:center;gap:4px;margin-bottom:4px;flex-wrap:wrap">
    <!-- tab buttons injected by JS -->
    <button onclick="addTerminal()"
      style="padding:4px 10px;background:#21262d;border:1px dashed #30363d;border-radius:5px;
             color:#58a6ff;cursor:pointer;font-size:11px;white-space:nowrap;font-family:monospace;
             transition:.15s" title="ترمنال جديد"
      onmouseover="this.style.borderColor='#58a6ff'" onmouseout="this.style.borderColor='#30363d'">
      + new
    </button>
  </div>

  <!-- ── Terminal windows container ── -->
  <div id="terminals-container"></div>

  <!-- Stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card"><div class="lbl">IP Address</div><div class="val" id="s-ip">—</div></div>
    <div class="stat-card"><div class="lbl">Panel Port</div><div class="val green" id="s-port" style="cursor:pointer;color:#3fb950" onclick="copyPort()" title="Click to copy">—</div></div>
    <div class="stat-card"><div class="lbl">Uptime</div><div class="val" id="s-uptime">—</div></div>
    <div class="stat-card"><div class="lbl">CPU</div><div class="val" id="s-cpu">—</div></div>
    <div class="stat-card"><div class="lbl">Memory</div><div class="val" id="s-mem">—</div></div>
    <div class="stat-card"><div class="lbl">Disk</div><div class="val" id="s-disk">—</div></div>
    <div class="stat-card green"><div class="lbl">Net In</div><div class="val" id="s-in">—</div></div>
    <div class="stat-card orange"><div class="lbl">Net Out</div><div class="val" id="s-out">—</div></div>
    <div class="stat-card"><div class="lbl">Hostname</div><div class="val" id="s-host">—</div></div>
    <div class="stat-card"><div class="lbl">Platform</div><div class="val" id="s-plat">—</div></div>
  </div>

  <!-- Service Links -->
  <div class="section-card">
    <div class="section-head">🔗 Active Services & Links</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="stat-card" style="cursor:pointer" id="web-link-card" onclick="openWebLink()">
          <div class="lbl">🌐 Website</div>
          <div class="val" style="font-size:12px;color:#3fb950;word-break:break-all" id="web-link">No HTML file</div>
        </div>
        <div class="stat-card" style="cursor:pointer" id="api-link-card" onclick="openApiLink()">
          <div class="lbl">⚡ API Service</div>
          <div class="val" style="font-size:12px;color:#00bfff;word-break:break-all" id="api-link">No API file</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px">
        <a href="https://t.me/Y0YY12" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">👨‍💻 Developer</div><div class="val" style="font-size:12px;color:var(--accent)">@Y0YY12</div></div>
        </a>
        <a href="https://t.me/Notfound_ELMODMEN" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">📢 Channel</div><div class="val" style="font-size:12px;color:var(--yellow)">@OWNER</div></div>
        </a>
        <div class="stat-card"><div class="lbl">🔌 Port</div><div class="val" id="port-display" style="color:var(--green);cursor:pointer" onclick="copyPort()">—</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ===== FILES TAB ===== -->
<div class="tab-content" id="tab-files">
  <input type="file" id="file-up" style="display:none" multiple onchange="uploadFiles(this)">
  <input type="file" id="zip-up" style="display:none" accept=".zip,.tar,.gz,.tar.gz,.rar" onchange="uploadAndExtract(this)">

  <div class="file-toolbar">
    <button onclick="createDir()">📁 New Folder</button>
    <button onclick="newFile()">📄 New File</button>
    <button onclick="document.getElementById('file-up').click()">⬆ Upload</button>
    <button onclick="document.getElementById('zip-up').click()">📦 Extract ZIP</button>
    <button onclick="loadFiles()">🔄 Refresh</button>
  </div>

  <div class="breadcrumb" id="breadcrumb">/ home /</div>
  <div class="file-list" id="file-list"></div>
</div>

<!-- ===== AI TAB ===== -->
<div class="tab-content" id="tab-ai">
  <div class="ai-chat-wrap">
    <!-- Header -->
    <div class="ai-header">
      <div class="ai-header-left">
        <div class="ai-avatar-main">🤖</div>
        <div>
          <div class="ai-header-title">SERVER HUB AI</div>
          <div class="ai-header-sub">GPT-OSS 120B · NVIDIA NIM</div>
        </div>
      </div>
      <button class="ai-clear-btn" onclick="clearAiChat()" title="Clear chat">🗑</button>
    </div>

    <!-- Messages -->
    <div id="ai-messages" class="ai-messages-box">
      <div class="ai-msg ai-assistant">
        <div class="ai-bubble">
          <span class="ai-avatar">🤖</span>
          <div class="ai-text">مرحباً! أنا مساعدك الذكي.<br>اسألني أي شيء — كود، أفكار، شرح، أو أي مساعدة تحتاجها.</div>
        </div>
      </div>
    </div>

    <!-- Thinking -->
    <div id="ai-thinking-box" class="ai-thinking-box" style="display:none">
      <div class="ai-thinking-label">
        <span class="ai-think-dots"><span></span><span></span><span></span></span>
        جاري التفكير...
      </div>
      <div id="ai-reasoning" class="ai-reasoning-text"></div>
    </div>

    <!-- Input -->
    <div class="ai-input-area">
      <div class="ai-input-row">
        <textarea id="ai-input"
          class="ai-textarea"
          placeholder="اكتب رسالتك هنا... (Enter للإرسال، Shift+Enter لسطر جديد)"
          rows="1"
          onkeydown="aiKeyDown(event)"
          oninput="autoResizeAI(this)"
        ></textarea>
        <button onclick="sendAiMessage()" id="ai-send-btn" class="ai-send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <div class="ai-footer-info">Enter للإرسال · Shift+Enter لسطر جديد · يدعم العربية والإنجليزية</div>
    </div>
  </div>
</div>

<!-- ===== DATABASES TAB ===== -->
<div class="tab-content" id="tab-databases">
  <div class="section-card">
    <div class="section-head">🗄 Create Database</div>
    <div class="section-body">
      <p style="color:var(--text2);font-size:13px;margin-bottom:12px">Manage SQLite / JSON databases in your panel folder.</p>
      <div class="field-block"><label>Database Name</label><input id="db-name" placeholder="my_database"></div>
      <div class="row-end"><button class="btn-action" onclick="createDB()">Create Database</button></div>
    </div>
  </div>
  <div id="db-list"></div>
</div>

<!-- ===== SCHEDULES TAB ===== -->
<div class="tab-content" id="tab-schedules">
  <div class="section-card">
    <div class="section-head">⏰ Create Schedule</div>
    <div class="section-body">
      <div class="field-block"><label>Name</label><input id="sch-name" placeholder="Daily backup"></div>
      <div class="field-block"><label>Command</label><input id="sch-cmd" placeholder="echo hello"></div>
      <div class="field-block"><label>Cron Expression</label><input id="sch-cron" value="* * * * *"></div>
      <div class="row-end"><button class="btn-action" onclick="addSchedule()">Add Schedule</button></div>
    </div>
  </div>
  <div id="sch-list"></div>
</div>

<!-- ===== HOSTING TAB ===== -->
<div class="tab-content" id="tab-hosting">
  <!-- Netlify -->
  <div class="section-card" style="border-color:rgba(0,194,255,.2)">
    <div class="section-head" style="color:#00c2ff">
      <span style="font-size:18px">▲</span> Netlify Deploy
    </div>
    <div class="section-body">
      <div class="field-block">
        <label>🔑 Netlify Token</label>
        <input id="netlify-token" type="password" placeholder="nfp_xxxxxxxxxxxx">
      </div>
      <div class="field-block">
        <label>📁 ZIP Path <span style="color:var(--text3)">(static site — HTML/CSS/JS)</span></label>
        <input id="netlify-zip" placeholder="/path/to/site.zip">
      </div>
      <div class="field-block">
        <label>🏷️ Site Name <span style="color:#e3b341;font-size:11px">مثال: OWNER-portfolio</span></label>
        <input id="netlify-name" placeholder="اكتب اسم الموقع (حروف وأرقام وشرطة فقط)"
          oninput="this.value=this.value.toLowerCase().replace(/[^a-z0-9-]/g,'-').replace(/-{2,}/g,'-')"
          style="font-family:monospace">
        <div style="font-size:10px;color:var(--text3);margin-top:3px">
          سيظهر الموقع على: <span id="netlify-url-preview" style="color:#00c2ff;font-family:monospace">your-site.netlify.app</span>
        </div>
      </div>
      <div class="row-end" style="gap:8px">
        <button class="btn-action gray"  onclick="netlifyTest()">🔌 Test Token</button>
        <button class="btn-action" style="background:linear-gradient(135deg,#00c2ff,#0070f3)"
          onclick="netlifyDeploy()">▲ Deploy to Netlify</button>
      </div>
      <div id="netlify-out" class="deploy-out" style="display:none"></div>
    </div>
  </div>

  <!-- Vercel -->
  <div class="section-card" style="border-color:rgba(255,255,255,.1);margin-top:10px">
    <div class="section-head" style="color:#e2e8f0">
      <span style="font-size:16px">▶</span> Vercel Deploy
    </div>
    <div class="section-body">
      <div class="field-block">
        <label>🔑 Vercel Token</label>
        <input id="vercel-token" type="password" placeholder="vcp_xxxxxxxxxxxx">
      </div>
      <div class="field-block">
        <label>📁 ZIP Path <span style="color:var(--text3)">(HTML/CSS/JS only)</span></label>
        <input id="vercel-zip" placeholder="/path/to/site.zip">
      </div>
      <div class="field-block">
        <label>🏷️ Project Name <span style="color:#e3b341;font-size:11px">مثال: OWNER-app</span></label>
        <input id="vercel-name" placeholder="اكتب اسم المشروع (حروف وأرقام وشرطة فقط)"
          oninput="this.value=this.value.toLowerCase().replace(/[^a-z0-9-]/g,'-').replace(/-{2,}/g,'-')"
          style="font-family:monospace">
        <div style="font-size:10px;color:var(--text3);margin-top:3px">
          سيظهر المشروع على: <span id="vercel-url-preview" style="color:#e2e8f0;font-family:monospace">your-project.vercel.app</span>
        </div>
      </div>
      <div class="row-end" style="gap:8px">
        <button class="btn-action gray"  onclick="vercelTest()">🔌 Test Token</button>
        <button class="btn-action" style="background:linear-gradient(135deg,#1a1a1a,#444)"
          onclick="vercelDeploy()">▶ Deploy to Vercel</button>
      </div>
      <div id="vercel-out" class="deploy-out" style="display:none"></div>
    </div>
  </div>

  <!-- Deployments list -->
  <div class="section-card" style="margin-top:10px">
    <div class="section-head">📋 Deployments</div>
    <div class="section-body">
      <button class="btn-action gray" onclick="loadDeployments()">🔄 Refresh</button>
      <div id="deployments-list" style="margin-top:10px"></div>
    </div>
  </div>
</div>

<!-- ===== COMMANDS TAB ===== -->
<div class="tab-content" id="tab-cmds">
  <div class="section-card">
    <div class="section-head">⌨️ Terminal Commands Reference</div>
    <div class="section-body">
      <div style="display:grid;gap:10px" id="cmds-accordion">

        <!-- Python -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('py')">
            <span>🐍 Python</span><span id="pg-py-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-py">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('python3 --version')">python3 --version</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install -r requirements.txt')">pip3 install -r requirements.txt</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install flask')">pip3 install flask</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install requests')">pip3 install requests</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install numpy pandas')">pip3 install numpy pandas</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install torch')">pip3 install torch</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install transformers')">pip3 install transformers</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 list')">pip3 list</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 freeze > requirements.txt')">pip3 freeze > requirements.txt</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install --upgrade pip')">pip3 upgrade</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('python3 -m venv venv && source venv/bin/activate')">create venv</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('source venv/bin/activate')">activate venv</div>
            </div>
          </div>
        </div>

        <!-- Node.js -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('node')">
            <span>🟢 Node.js</span><span id="pg-node-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-node" style="display:none">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('node --version')">node --version</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm --version')">npm --version</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm install')">npm install</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm start')">npm start</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm run dev')">npm run dev</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm install express')">install express</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm install -g nodemon')">install nodemon</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm update')">npm update</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npm list')">npm list</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('yarn install')">yarn install</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('npx create-react-app .')">create react app</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('node index.js')">node index.js</div>
            </div>
          </div>
        </div>

        <!-- PHP -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('php')">
            <span>🐘 PHP</span><span id="pg-php-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-php" style="display:none">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('php --version')">php --version</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('php -S 0.0.0.0:8080')">php -S 0.0.0.0:8080</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('composer install')">composer install</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('composer update')">composer update</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('composer require guzzlehttp/guzzle')">install guzzle</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('php artisan serve')">artisan serve</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('php artisan migrate')">artisan migrate</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('php artisan key:generate')">key:generate</div>
            </div>
          </div>
        </div>

        <!-- Git -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('git')">
            <span>📦 Git</span><span id="pg-git-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-git" style="display:none">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('git init')">git init</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git clone ')">git clone</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git status')">git status</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git add .')">git add .</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git commit -m "update"')">git commit</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git push origin main')">git push</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git pull')">git pull</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git log --oneline')">git log</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git branch -a')">git branch</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('git checkout -b new-branch')">new branch</div>
            </div>
          </div>
        </div>

        <!-- System / APT -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('sys')">
            <span>🖥️ System & APT</span><span id="pg-sys-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-sys" style="display:none">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get update')">apt update</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get upgrade -y')">apt upgrade</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get install -y curl')">install curl</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get install -y git')">install git</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get install -y nodejs npm')">install node</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get install -y php')">install php</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('apt-get install -y ffmpeg')">install ffmpeg</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('ls -la')">ls -la</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pwd')">pwd</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('df -h')">disk usage</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('free -h')">memory</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('ps aux | head -20')">processes</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('kill -9 ')">kill PID</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('chmod +x ')">chmod +x</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('cat ')">cat file</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('mkdir -p ')">mkdir</div>
            </div>
          </div>
        </div>

        <!-- AI / ML -->
        <div class="cmd-group">
          <div class="cmd-group-head" onclick="toggleCmdGroup('ai')">
            <span>🤖 AI / ML</span><span id="pg-ai-arrow">▼</span>
          </div>
          <div class="cmd-group-body" id="pg-ai" style="display:none">
            <div class="cmd-grid">
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install torch torchvision')">install torch</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install transformers')">install transformers</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install openai')">install openai</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install anthropic')">install anthropic</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install langchain')">install langchain</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install ollama')">install ollama</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install sentence-transformers')">sentence-transformers</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('pip3 install diffusers accelerate')">diffusers</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('nvidia-smi')">nvidia-smi</div>
              <div class="cmd-item" onclick="sendCmdToTerminal('python3 -c \"import torch; print(torch.cuda.is_available())\"')">check CUDA</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</div>


''' + (r'''
<!-- ===== USERS TAB (master only) ===== -->
<div class="tab-content" id="tab-users">
  <div class="section-card">
    <div class="section-head">👤 Add User</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="field-block"><label>Username</label><input id="u-name" placeholder="username"></div>
        <div class="field-block"><label>Password</label><input id="u-pass" type="password" placeholder="password"></div>
        <div class="field-block"><label>🔵 Telegram Username</label><input id="u-tg" placeholder="@username"></div>
        <div class="field-block"><label>Plan</label>
          <select id="u-plan" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px" onchange="onPlanChange()">
            <option value="free_trial">🆓 Free Trial — 7 أيام</option>
            <option value="paid_20">⭐ Paid 20 يوم — 15 نجمة</option>
            <option value="paid_30">💎 Paid 30 يوم — 25 نجمة</option>
            <option value="custom">🎯 Custom</option>
          </select>
        </div>
        <div class="field-block" id="u-custom-days-wrap" style="display:none"><label>Custom Days</label><input id="u-days" type="number" value="7" min="1"></div>
        <div class="field-block"><label>Max Sessions</label><input id="u-max" type="number" value="1"></div>
        <div class="field-block"><label>Max Servers</label>
          <select id="u-maxsrv" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="1">1 Server</option><option value="2">2 Servers</option>
            <option value="3">3 Servers</option><option value="5">5 Servers</option>
            <option value="10">10 Servers</option><option value="999">Unlimited</option>
          </select>
        </div>
        <div class="field-block"><label>Main File</label><input id="u-main" value="main.py"></div>
      </div>
      <div class="row-end"><button class="btn-action" onclick="addUser()">Add User</button></div>
    </div>
  </div>
  <div id="users-list"></div>

  <!-- Edit Modal -->
  <div class="modal" id="edit-user-modal">
    <div class="modal-box">
      <div class="modal-head"><h3>Edit User</h3><button class="close" onclick="closeModal('edit-user-modal')">×</button></div>
      <div class="modal-body">
        <input type="hidden" id="eu-name">
        <div class="field-block"><label>New Password</label><input id="eu-pass" type="password" placeholder="(leave blank to keep)"></div>
        <div class="field-block"><label>Max Sessions</label><input id="eu-max" type="number"></div>
        <div class="field-block"><label>Max Servers</label>
          <select id="eu-maxsrv" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="1">1</option><option value="2">2</option><option value="3">3</option>
            <option value="5">5</option><option value="10">10</option><option value="999">Unlimited</option>
          </select>
        </div>
        <div class="field-block"><label>Main File</label><input id="eu-main"></div>
        <div class="field-block"><label>Extend Subscription (days)</label><input id="eu-days" type="number" value="30" min="30"></div>
      </div>
      <div class="modal-foot">
        <button class="btn-action gray" onclick="closeModal('edit-user-modal')">Cancel</button>
        <button class="btn-action" onclick="saveEditUser()">Save</button>
      </div>
    </div>
  </div>
</div>

<!-- ===== BACKUPS TAB ===== -->
<div class="tab-content" id="tab-backups">
  <div class="section-card">
    <div class="section-head">💾 Backups</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button class="btn-action green" onclick="createBackup()">➕ Create Backup</button>
        <button class="btn-action gray" onclick="loadBackups()">🔄 Refresh</button>
      </div>
      <div id="backups-list"></div>
    </div>
  </div>
</div>

<!-- ===== NETWORK TAB ===== -->
<div class="tab-content" id="tab-network">
  <div class="section-card">
    <div class="section-head">🔌 Extra Ports</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
        <input id="new-port" type="number" placeholder="Port (e.g. 8080)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;width:160px">
        <input id="new-port-note" placeholder="Note (optional)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1;min-width:120px">
        <button class="btn-action" onclick="addPort()">Add Port</button>
      </div>
      <div id="ports-list"></div>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">🔍 Port Scanner</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input id="scan-host" placeholder="Host (e.g. 127.0.0.1)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <input id="scan-ports" placeholder="Ports (22,80,443,8080)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action" onclick="scanPorts()">Scan</button>
      </div>
      <div id="scan-results" style="margin-top:12px"></div>
    </div>
  </div>
</div>

<!-- ===== STARTUP TAB ===== -->
<div class="tab-content" id="tab-startup">
  <div class="section-card">
    <div class="section-head">🚀 Startup / Auto-Start</div>
    <div class="section-body">
      <div class="field-block"><label>Main Startup File</label><input id="startup-file" placeholder="main.py"></div>
      <button class="btn-action" onclick="setStartupFile()">Set Startup File</button>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">📦 Package Manager</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input id="pip-pkg" placeholder="pip package name" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action orange" onclick="installPip()">pip install</button>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <input id="npm-pkg" placeholder="npm package name" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action green" onclick="installNpm()">npm install</button>
      </div>
    </div>
  </div>
</div>
''' if is_master else '') + r'''

<!-- ===== SETTINGS TAB ===== -->
<div class="tab-content" id="tab-settings">
  <div class="section-card">
    <div class="section-head">🔒 Change Password</div>
    <div class="section-body">
      <div class="field-block"><label>Current Password</label><input id="cur-pass" type="password" placeholder="Current password"></div>
      <div class="field-block"><label>New Password</label><input id="new-pass" type="password" placeholder="New password"></div>
      <div class="row-end"><button class="btn-action" onclick="changePassword()">Change Password</button></div>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">🖥 System Info</div>
    <div class="section-body">
      <pre id="sysinfo-box" style="color:var(--text2);font-size:12px;font-family:monospace;white-space:pre-wrap"></pre>
      <div class="row-end"><button class="btn-action gray" onclick="loadSysinfo()">🔄 Refresh</button></div>
    </div>
  </div>
</div>

<!-- ===== ACTIVITY TAB ===== -->
<div class="tab-content" id="tab-activity">
  <div class="section-card">
    <div class="section-head">📋 Activity Feed</div>
    <div class="section-body">
      <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
        <button class="btn-action gray" onclick="loadActivity()">🔄 Refresh</button>
      </div>
      <div id="activity-list"></div>
    </div>
  </div>
</div>

''' + owner_panel_html + r'''

</div><!-- /container -->

<!-- EDITOR MODAL -->
<div class="modal" id="editor-modal">
  <div class="modal-box" style="max-width:800px;width:95vw">
    <div class="modal-head">
      <h3 id="editor-title">Edit File</h3>
      <button class="close" onclick="closeModal('editor-modal')">×</button>
    </div>
    <div class="modal-body">
      <textarea class="editor-box" id="editor-content" spellcheck="false"></textarea>
    </div>
    <div class="modal-foot">
      <button class="btn-action gray" onclick="closeModal('editor-modal')">Cancel</button>
      <button class="btn-action" onclick="saveFile()">💾 Save</button>
    </div>
  </div>
</div>

<!-- SERVERS MODAL -->
<div class="modal" id="servers-modal">
  <div class="modal-box">
    <div class="modal-head"><h3>🗂 Servers</h3><button class="close" onclick="closeModal('servers-modal')">×</button></div>
    <div class="modal-body" id="servers-modal-list" style="max-height:400px;overflow-y:auto"></div>
    <div class="modal-foot"><button class="btn-action gray" onclick="closeModal('servers-modal')">Close</button></div>
  </div>
</div>

<!-- EXTRACT MODAL -->
<div class="modal" id="extract-modal">
  <div class="modal-box">
    <div class="modal-head"><h3>📦 Extract Archive</h3><button class="close" onclick="closeModal('extract-modal')">×</button></div>
    <div class="modal-body">
      <input type="hidden" id="extract-src">
      <div class="field-block"><label>Extract to folder</label><input id="extract-dest" placeholder="(same directory)"></div>
    </div>
    <div class="modal-foot">
      <button class="btn-action gray" onclick="closeModal('extract-modal')">Cancel</button>
      <button class="btn-action" onclick="doExtract()">📦 Extract</button>
    </div>
  </div>
</div>

<script>
// ─── Config ───
const IS_MASTER = ''' + ('true' if is_master else 'false') + r''';
var USER_PATH = '';
var currentPath = '';
var currentEditPath = null;
var statsInterval = null;

// ─── Multi-Terminal State ──────────────────────────────────────────────────
var terminals = {};          // tid -> { processId, history, histIdx, interval, dir }
var activeTerminalId = null;
var terminalCounter = 0;

function createTerminalState(tid){
  terminals[tid] = {
    processId: null,
    history: [],
    histIdx: -1,
    interval: null,
    dir: '~'
  };
}

// legacy shims so old code still works
Object.defineProperty(window, 'currentProcessId', {
  get(){ return activeTerminalId ? terminals[activeTerminalId]?.processId : null; },
  set(v){ if(activeTerminalId && terminals[activeTerminalId]) terminals[activeTerminalId].processId = v; }
});
Object.defineProperty(window, 'cmdHistory', {
  get(){ return activeTerminalId ? (terminals[activeTerminalId]?.history||[]) : []; },
  set(v){ if(activeTerminalId && terminals[activeTerminalId]) terminals[activeTerminalId].history = v; }
});
Object.defineProperty(window, 'cmdHistIdx', {
  get(){ return activeTerminalId ? (terminals[activeTerminalId]?.histIdx ?? -1) : -1; },
  set(v){ if(activeTerminalId && terminals[activeTerminalId]) terminals[activeTerminalId].histIdx = v; }
});
Object.defineProperty(window, 'consoleInterval', {
  get(){ return activeTerminalId ? terminals[activeTerminalId]?.interval : null; },
  set(v){ if(activeTerminalId && terminals[activeTerminalId]) terminals[activeTerminalId].interval = v; }
});

// ─── Toast ───
function toast(msg, isErr=false, isInfo=false){
  const c=document.getElementById('toast-container');
  const t=document.createElement('div');
  t.className='toast '+(isErr?'err':isInfo?'info':'ok');
  t.textContent=msg;
  c.appendChild(t);
  setTimeout(()=>t.remove(), 3500);
}

// ─── Tab switching ───
document.querySelectorAll('.tab-item').forEach(tab=>{
  tab.addEventListener('click',()=>{
    const id=tab.dataset.tab;
    document.querySelectorAll('.tab-item').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-'+id).classList.add('active');
    // lazy loaders
    if(id==='users') loadUsers();
    if(id==='backups') loadBackups();
    if(id==='network') loadPorts();
    if(id==='activity') loadActivity();
    if(id==='owner') loadOwnerPanel();
    if(id==='hosting') loadDeployments();
    if(id==='cmds') {}  // static content
  });
});

// ─── Modal helpers ───
function openModal(id){ document.getElementById(id).classList.add('open'); }
function closeModal(id){ document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal').forEach(m=>{
  m.addEventListener('click',e=>{ if(e.target===m) m.classList.remove('open'); });
});

// ─── Escape HTML ───
function escapeHtml(s){ return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

// ─── Stats polling ───
async function loadStats(){
  try{
    const r = await fetch('/api/system');
    const d = await r.json();
    if(d.cpu){
      document.getElementById('s-ip').textContent = d.ip||'—';
      document.getElementById('s-cpu').textContent = d.cpu||'—';
      document.getElementById('s-mem').textContent = d.memory||'—';
      document.getElementById('s-disk').textContent = d.disk||'—';
      document.getElementById('s-uptime').textContent = d.uptime||'—';
      document.getElementById('s-in').textContent = d.network_in||'—';
      document.getElementById('s-out').textContent = d.network_out||'—';
      document.getElementById('s-host').textContent = d.hostname||'—';
      document.getElementById('s-port').textContent = d.port||'—';
      document.getElementById('s-plat').textContent = (d.platform||'')+(d.python?' / py'+d.python:'');
      document.getElementById('port-display').textContent = d.port||'—';
      USER_PATH = USER_PATH || '';
    }
  } catch(e){}
}

async function loadProfile(){
  try{
    const r=await fetch('/api/profile');
    const d=await r.json();
    USER_PATH = d.user_path || '';
    currentPath = USER_PATH;
    document.getElementById('topbar-user').textContent = d.username || '';
    // update web/api links
    document.getElementById('web-link').textContent = '/web/'+d.username+'/';
    document.getElementById('api-link').textContent = '/api-service/'+d.username+'/';
  }catch(e){}
}

function openWebLink(){ window.open('/web/'+(document.getElementById('topbar-user').textContent||'')+'/', '_blank'); }
function openApiLink(){ window.open('/api-service/'+(document.getElementById('topbar-user').textContent||'')+'/', '_blank'); }

function copyPort(){
  const p = document.getElementById('port-display').textContent;
  navigator.clipboard.writeText(p).then(()=>toast('Port copied: '+p));
}

// ─── Power / Process ───
async function powerAction(action){
  if(action==='start'){
    let mainFile = 'main.py';
    try {
      const mfR = await fetch('/api/files/main-file');
      const mfD = await mfR.json();
      mainFile = mfD.main_file || 'main.py';
    } catch(e) {}
    if(!currentPath){
      try{ const p=await fetch('/api/profile').then(r=>r.json()); currentPath=p.user_path||''; }catch(e){}
    }
    appendConsole('┌──(𝙴𝙻𝙼𝙾𝙳𝙼𝙴𝙽㉿server-hub)-[~]');
    appendConsole('└─$ python3 ' + mainFile + '  ▶ Starting...');
    try {
      const r = await fetch('/api/file/run', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({path: currentPath, filename: mainFile})});
      const d = await r.json();
      if(d.success){
        currentProcessId = d.process_id;
        setProcStatus(true);
        appendConsole('[✔] Process started — ID: ' + d.process_id);
        toast('▶ Started: '+mainFile);
        startConsolePolling();
      } else {
        appendConsole('[✘] ERROR: ' + (d.error||'Failed to start'));
        toast('❌ '+(d.error||'Failed'), true);
      }
    } catch(e) {
      appendConsole('[✘] Network error: ' + (e.message||e));
      toast('❌ Network error', true);
    }
  } else if(action==='stop'){
    if(!currentProcessId){ toast('لا يوجد بروسيس شغال حالياً', true); return; }
    appendConsole('└─$ kill ' + currentProcessId + '  ■ Stopping...');
    try {
      await fetch('/api/file/stop', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({process_id: currentProcessId})});
      appendConsole('[✔] Process stopped.');
    } catch(e) {
      appendConsole('[!] Stop request sent (connection issue).');
    }
    currentProcessId = null;
    setProcStatus(false);
    toast('■ Stopped');
    stopConsolePolling();
  } else if(action==='restart'){
    appendConsole('└─$ ↺ Restarting...');
    if(currentProcessId){
      try {
        await fetch('/api/file/stop', {method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({process_id: currentProcessId})});
      } catch(e) {}
      currentProcessId = null;
      setProcStatus(false);
      stopConsolePolling();
      appendConsole('[✔] Stopped — restarting in 800ms...');
    }
    setTimeout(()=>powerAction('start'), 800);
  }
}

function setProcStatus(running){
  const dot=document.getElementById('proc-dot');
  const txt=document.getElementById('proc-status');
  dot.style.background = running ? '#3fb950' : '#f85149';
  txt.textContent = running ? 'Running' : 'Stopped';
}

// ═══════════════════════════════════════════════════════════════════════════
//  MULTI-TERMINAL ENGINE
// ═══════════════════════════════════════════════════════════════════════════

function terminalBannerHTML(tid){
  return `<div class="t-dim" style="font-size:10px;margin-bottom:4px;user-select:none;padding:2px 0 4px;border-bottom:1px solid #21262d">` +
    `<span style="background:linear-gradient(90deg,#a855f7,#00bfff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900;letter-spacing:2px">ELMODMEN</span>` +
    `  <span style="color:#3d444d">SERVER HUB v2.0 · @Y0YY12 · terminal #${tid}</span></div>` +
    `<div class="t-prompt">┌──(<span style="color:#ff3399">runner</span>㉿<span style="color:#58a6ff">serverhub</span>)-[<span style="color:#e3b341">~</span>]</div>` +
    `<div class="t-prompt">└─<span style="color:#ff3399">$</span> <span class="t-dim" style="font-size:10px">ready — click anywhere to type</span></div>`;
}

/* ── QUICK INSTALL COMMANDS ── */

function buildTerminalEl(tid){
  const wrap = document.createElement('div');
  wrap.id = `term-wrap-${tid}`;
  wrap.style.display = 'none';

  // ── VS Code window wrapper ──
  const win = document.createElement('div');
  win.className = 'term-window';

  // title bar (3 dots + title)
  const titlebar = document.createElement('div');
  titlebar.className = 'term-titlebar';
  titlebar.innerHTML =
    `<div class="term-dot red"   title="إغلاق"    onclick="closeTerminal('${tid}')"></div>` +
    `<div class="term-dot yellow" title="تصغير"></div>` +
    `<div class="term-dot green"  title="تكبير"   onclick="toggleTermSize('${tid}')"></div>` +
    `<div class="term-title">runner㉿serverhub — terminal ${tid}</div>` +
    `<div style="font-size:10px;color:#3d444d;cursor:pointer" onclick="clearTerminal('${tid}')">⌫ clear</div>`;
  win.appendChild(titlebar);

  // quick-install bar

  // ── OUTPUT area — click anywhere = focus input ──
  const out = document.createElement('div');
  out.id = `console-output-${tid}`;
  out.className = 'term-output';
  out.innerHTML = terminalBannerHTML(tid);
  out.addEventListener('click', ()=> focusTerminal(tid));
  win.appendChild(out);

  // ── INPUT row (no separate bar — merged with window) ──
  const inputRow = document.createElement('div');
  inputRow.className = 'term-input-row';
  inputRow.id = `term-input-row-${tid}`;
  inputRow.innerHTML =
    `<div class="term-prompt-label" id="cwd-prompt-${tid}">` +
      `<span style="color:#ff3399">runner</span><span style="color:#6e7681">@</span>` +
      `<span style="color:#58a6ff">serverhub</span>` +
      `<span style="color:#6e7681">:</span><span style="color:#e3b341" id="cwd-val-${tid}">~</span>` +
      `<span style="color:#ff3399">$</span> ` +
    `</div>` +
    `<input id="cmd-field-${tid}" class="term-field"
       dir="auto" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"
       placeholder="type a command..."
       onkeydown="termKeyDown(event,'${tid}')">` +
    `<button class="term-send-btn" onclick="termRunCmd('${tid}')" title="Enter">↵</button>`;
  win.appendChild(inputRow);

  wrap.appendChild(win);
  return wrap;
}

function focusTerminal(tid){
  const inp = document.getElementById(`cmd-field-${tid}`);
  if(inp){ inp.focus(); inp.scrollIntoView({block:'nearest'}); }
}

function toggleTermSize(tid){
  const w = document.getElementById(`term-wrap-${tid}`)?.querySelector('.term-window');
  if(!w) return;
  const win = w;
  win._big = !win._big;
  win.style.height = win._big ? '75vh' : '';
}

function clearTerminal(tid){
  const out = document.getElementById(`console-output-${tid}`);
  if(!out) return;
  out.innerHTML = terminalBannerHTML(tid);
}

function addTerminal(){
  terminalCounter++;
  const tid = String(terminalCounter);
  createTerminalState(tid);

  // tab button
  const tabsBar = document.getElementById('term-tabs-bar');
  const btn = document.createElement('div');
  btn.id = `term-tab-${tid}`;
  btn.style.cssText = 'display:flex;align-items:center;gap:4px;padding:4px 10px;background:#21262d;' +
    'border:1px solid #30363d;border-radius:5px;cursor:pointer;font-size:11px;' +
    'color:#8b949e;transition:.15s;white-space:nowrap;font-family:monospace';
  btn.innerHTML =
    `<span style="color:#28c840;font-size:8px">●</span> #${tid}` +
    ` <span onclick="event.stopPropagation();closeTerminal('${tid}')"
        style="color:#3d444d;margin-left:3px;font-size:13px;line-height:1" title="close">×</span>`;
  btn.onclick = ()=> switchTerminal(tid);
  tabsBar.insertBefore(btn, tabsBar.lastElementChild);

  document.getElementById('terminals-container').appendChild(buildTerminalEl(tid));
  switchTerminal(tid);
}

function switchTerminal(tid){
  Object.keys(terminals).forEach(id=>{
    const w=document.getElementById(`term-wrap-${id}`);
    if(w) w.style.display='none';
    const t=document.getElementById(`term-tab-${id}`);
    if(t){t.style.borderColor='#30363d';t.style.color='#8b949e';t.style.background='#21262d';}
  });
  activeTerminalId = tid;
  const w=document.getElementById(`term-wrap-${tid}`);
  if(w) w.style.display='block';
  const t=document.getElementById(`term-tab-${tid}`);
  if(t){t.style.borderColor='#58a6ff';t.style.color='#c9d1d9';t.style.background='#161b22';}
  setTimeout(()=> focusTerminal(tid), 40);
}

function closeTerminal(tid){
  if(Object.keys(terminals).length<=1){toast('يجب إبقاء ترمنال واحد',true);return;}
  if(terminals[tid]?.interval) clearInterval(terminals[tid].interval);
  delete terminals[tid];
  document.getElementById(`term-wrap-${tid}`)?.remove();
  document.getElementById(`term-tab-${tid}`)?.remove();
  const rem=Object.keys(terminals);
  if(rem.length) switchTerminal(rem[rem.length-1]);
}

function termQuickCmd(tid, cmd){
  const inp = document.getElementById(`cmd-field-${tid}`);
  if(inp){ inp.value=cmd; focusTerminal(tid); }
}

function appendToTerminal(tid, txt){
  const out = document.getElementById('console-output-'+tid);
  if(!out) return;
  const t = (txt||'').replace(/\r/g,'');
  if(t==='' && t!=='0') return;
  const line = document.createElement('div');
  line.dir = 'auto';
  line.style.cssText = "font-family:'Fira Code','Consolas',monospace;font-size:12.5px;line-height:1.65;padding-left:2px";
  if(/^(error|err:|traceback|exception)/i.test(t)||/error.*:/i.test(t)||t.includes('❌'))
    line.style.color='#ff6b6b';
  else if(/^(warn|warning|⚠)/i.test(t))
    line.style.color='#d29922';
  else if(/^(\[.?\]|✅|success|started|running|done)/i.test(t)||t.includes('[✔]'))
    line.style.color='#3fb950';
  else if(t.startsWith('└─$')||t.startsWith('┌──'))
    line.style.color='#00ff41';
  else if(t.startsWith('$ ')||t.startsWith('└─$ '))
    { line.style.color='#79c0ff'; line.style.fontWeight='600'; }
  else if(/^(stopping|restarting|■|●)/i.test(t))
    line.style.color='#e3b341';
  else
    line.style.color='#c9d1d9';
  line.textContent = t;
  out.appendChild(line);
  out.scrollTop = out.scrollHeight;
  if(out.children.length > 1200) out.removeChild(out.children[0]);
}

function appendConsole(txt){
  if(activeTerminalId) appendToTerminal(activeTerminalId, txt);
}

async function termRunCmd(tid){
  const inp = document.getElementById(`cmd-field-${tid}`);
  if(!inp) return;
  const cmd = inp.value.trim();
  if(!cmd) return;
  const ts = terminals[tid];
  ts.history.unshift(cmd); ts.histIdx=-1;
  inp.value='';
  appendToTerminal(tid, '└─$ '+cmd);
  if(ts.processId){
    await fetch('/api/file/input',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({process_id:ts.processId,input:cmd})});
  } else {
    try{
      const r=await fetch('/api/exec',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({command:cmd,cwd:currentPath})});
      const d=await r.json();

      // ── Interactive process started → begin polling ──
      if(d.interactive && d.process_id){
        ts.processId = d.process_id;
        appendToTerminal(tid, '▶ ' + (d.message||'Interactive process started'));
        setProcStatus(true);
        startConsolePolling();
        return;
      }

      if(d.output) d.output.split('\n').forEach(l=>{ if(l.trim()) appendToTerminal(tid,l); });
      if(d.error)  appendToTerminal(tid,'❌ '+d.error);
      if(/^cd\s/.test(cmd)){
        const nd=cmd.slice(3).trim()||'~';
        const el=document.getElementById(`cwd-val-${tid}`);
        if(el) el.textContent=nd;
      }
    }catch(e){ appendToTerminal(tid,'❌ Error: '+e); }
  }
}

async function runCmd(){
  if(activeTerminalId) await termRunCmd(activeTerminalId);
}

function termKeyDown(e, tid){
  const ts=terminals[tid];
  const inp=document.getElementById(`cmd-field-${tid}`);
  if(!ts||!inp) return;
  if(e.key==='Enter'){ e.preventDefault(); termRunCmd(tid); }
  else if(e.key==='ArrowUp'){
    e.preventDefault();
    ts.histIdx=Math.min(ts.histIdx+1,ts.history.length-1);
    inp.value=ts.history[ts.histIdx]||'';
    inp.selectionStart=inp.selectionEnd=inp.value.length;
  } else if(e.key==='ArrowDown'){
    e.preventDefault();
    ts.histIdx=Math.max(ts.histIdx-1,-1);
    inp.value=ts.histIdx>=0?ts.history[ts.histIdx]:'';
    inp.selectionStart=inp.selectionEnd=inp.value.length;
  } else if(e.key==='Tab') e.preventDefault();
}

function cmdKeyDown(e){
  if(activeTerminalId) termKeyDown(e,activeTerminalId);
}

function startConsolePolling(){
  if(!activeTerminalId) return;
  stopConsolePolling();
  const tid=activeTerminalId;
  const ts=terminals[tid];
  ts.interval=setInterval(async()=>{
    if(!ts.processId) return;
    try{
      const r=await fetch('/api/file/output/'+ts.processId);
      const d=await r.json();
      if(d.success && d.output && d.output.length){
        d.output.forEach(l=>appendToTerminal(tid,l));
        await fetch('/api/file/output/'+ts.processId+'/clear',{method:'POST'}).catch(()=>{});
      }
      if(!d.is_running){ setProcStatus(false); ts.processId=null; clearInterval(ts.interval); ts.interval=null; }
    }catch(e){}
  },800);
}

function stopConsolePolling(){
  if(!activeTerminalId) return;
  const ts=terminals[activeTerminalId];
  if(ts?.interval){ clearInterval(ts.interval); ts.interval=null; }
}

function initTerminals(){ addTerminal(); }
// ─── FILES ───
async function loadFiles(path){
  if(!path && !currentPath){
    const prof=await fetch('/api/profile').then(r=>r.json());
    currentPath = prof.user_path || '';
  }
  const p = path || currentPath;
  currentPath = p;
  try{
    const r=await fetch('/api/files?path='+encodeURIComponent(p));
    const d=await r.json();
    renderFiles(d.files||[], p);
    renderBreadcrumb(p);
  }catch(e){ toast('Failed to load files', true); }
}

function getFileIcon(name, isDir){
  if(isDir) return '📁';
  const ext=name.split('.').pop().toLowerCase();
  const m={py:'🐍',js:'📜',ts:'📜',jsx:'⚛️',tsx:'⚛️',
           html:'🌐',htm:'🌐',css:'🎨',scss:'🎨',
           json:'📋',yml:'⚙️',yaml:'⚙️',toml:'⚙️',ini:'⚙️',
           md:'📝',txt:'📄',sh:'⚡',bash:'⚡',
           zip:'📦',tar:'📦',gz:'📦',rar:'📦',
           jpg:'🖼',jpeg:'🖼',png:'🖼',gif:'🖼',svg:'🖼',
           mp4:'🎬',mp3:'🎵',pdf:'📕',php:'🐘',rb:'💎',
           sql:'🗄',db:'🗄',sqlite:'🗄'};
  return m[ext]||'📄';
}

function renderFiles(files, path){
  const list=document.getElementById('file-list');
  if(!files.length){
    list.innerHTML='<div style="padding:24px;text-align:center;color:var(--text3)">📂 Empty folder</div>';
    return;
  }
  list.innerHTML='';
  files.forEach(f=>{
    const fp=path.replace(/\/*$/,'')+'/'+f.name;
    const row=document.createElement('div');
    row.className='file-item';
    row.innerHTML=`
      <span class="file-icon">${getFileIcon(f.name, f.is_dir)}</span>
      <span class="file-name">${escapeHtml(f.name)}</span>
      <span class="file-size">${f.size||''}</span>
      <div class="file-actions">
        ${f.is_dir?`<button onclick="loadFiles('${escapeHtml(fp)}')">Open</button>`:
          `<button onclick="editFile('${escapeHtml(fp)}','${escapeHtml(f.name)}')">Edit</button>
           <button onclick="runSingleFile('${escapeHtml(fp)}','${escapeHtml(f.name)}')">Run</button>`}
        ${(f.name.endsWith('.zip')||f.name.endsWith('.tar.gz')||f.name.endsWith('.tar'))?
          `<button onclick="openExtractModal('${escapeHtml(fp)}')">📦 Extract</button>`:''}
        <button onclick="setMain('${escapeHtml(f.name)}','${escapeHtml(fp)}')">★ Main</button>
        <button class="danger" onclick="deleteFile('${escapeHtml(fp)}','${escapeHtml(f.name)}')">🗑</button>
      </div>`;
    list.appendChild(row);
  });
}

function renderBreadcrumb(path){
  const el=document.getElementById('breadcrumb');
  const base = USER_PATH || '';
  const rel = path.replace(base,'') || '/';
  el.innerHTML = '/ home / ' + escapeHtml(rel.replace(/\//g,' / '));
}

async function editFile(path, name){
  try{
    const r=await fetch('/api/files/content?path='+encodeURIComponent(path));
    const d=await r.json();
    document.getElementById('editor-title').textContent='✏️ '+name;
    document.getElementById('editor-content').value=d.content||'';
    currentEditPath=path;
    openModal('editor-modal');
  }catch(e){ toast('Cannot open file', true); }
}

async function saveFile(){
  if(!currentEditPath) return;
  const content=document.getElementById('editor-content').value;
  const r=await fetch('/api/files/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path:currentEditPath,content})});
  const d=await r.json();
  toast(d.success?'✅ Saved':'❌ Failed', !d.success);
  if(d.success) closeModal('editor-modal');
}

async function runSingleFile(path, name){
  const dir=path.substring(0,path.lastIndexOf('/'));
  const r=await fetch('/api/file/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path:dir,filename:name})});
  const d=await r.json();
  if(d.success){
    currentProcessId=d.process_id;
    setProcStatus(true);
    document.querySelectorAll('.tab-item').forEach(t=>{ if(t.dataset.tab==='console') t.click(); });
    toast('▶ Running: '+name);
    startConsolePolling();
  } else { toast('❌ '+(d.error||'Failed'), true); }
}

async function setMain(filename, path){
  const r=await fetch('/api/files/set-main',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({filename,path})});
  const d=await r.json();
  toast(d.success?'★ Main file set: '+filename:'Failed', !d.success);
}

async function deleteFile(path, name){
  if(!confirm('Delete "'+name+'"?')) return;
  const r=await fetch('/api/files/delete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path})});
  const d=await r.json();
  toast(d.success?'🗑 Deleted':'Failed', !d.success);
  if(d.success) loadFiles(currentPath);
}

async function createDir(){
  const n=prompt('Folder name:'); if(!n) return;
  const p=currentPath.replace(/\/*$/,'')+'/'+n;
  const r=await fetch('/api/files/folder',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path:p})});
  const d=await r.json();
  toast(d.success?'📁 Created':'Failed', !d.success);
  if(d.success) loadFiles(currentPath);
}

async function newFile(){
  const n=prompt('File name:'); if(!n) return;
  const p=currentPath.replace(/\/*$/,'')+'/'+n;
  const r=await fetch('/api/files/create',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path:p,content:''})});
  const d=await r.json();
  toast(d.success?'📄 Created':'Failed', !d.success);
  if(d.success){ loadFiles(currentPath); editFile(p,n); }
}

async function uploadFiles(inp){
  const files=inp.files; if(!files.length) return;
  let ok=0, fail=0;
  for(const f of files){
    const fd=new FormData();
    fd.append('file',f);
    fd.append('path',currentPath);
    const r=await fetch('/api/files/upload',{method:'POST',body:fd});
    const d=await r.json();
    if(d.success){
      ok++;
    } else {
      fail++;
      const errMsg = (d.error||'Upload failed');
      if(errMsg.startsWith('SECURITY_ALERT|')){
        const threats = errMsg.replace('SECURITY_ALERT|','');
        showSecurityAlert(f.name, threats);
      } else {
        toast('❌ '+errMsg, true);
      }
    }
  }
  if(ok>0) toast('⬆ تم الرفع: '+ok+' ملف', false);
  loadFiles(currentPath);
  inp.value='';
}

function showSecurityAlert(fname, threats){
  const overlay=document.createElement('div');
  overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:999999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(8px)';
  overlay.innerHTML=`<div style="background:#0d1117;border:2px solid #f85149;border-radius:20px;padding:36px 32px;max-width:440px;width:92%;text-align:center;box-shadow:0 0 60px rgba(248,81,73,.4),0 0 120px rgba(248,81,73,.15)">
    <div style="font-size:64px;margin-bottom:12px;animation:pulse 1s ease-in-out infinite">🚨</div>
    <div style="color:#f85149;font-size:22px;font-weight:900;margin-bottom:10px;letter-spacing:1px">تحذير أمني!</div>
    <div style="background:rgba(248,81,73,.08);border:1px solid rgba(248,81,73,.3);border-radius:10px;padding:14px;margin-bottom:16px">
      <div style="color:#ff9999;font-size:14px;font-weight:700;margin-bottom:6px">⚠️ بطل عبط يا حبيبي عشان متتحظرش!</div>
      <div style="color:#8b949e;font-size:12px;margin-bottom:8px">الملف: <span style="color:#f85149;font-family:monospace">${escapeHtml(fname)}</span></div>
      <div style="color:#8b949e;font-size:12px">المشكلة: <span style="color:#ffcc00;font-family:monospace;font-size:11px">${escapeHtml(threats)}</span></div>
    </div>
    <div style="color:#484f58;font-size:11px;margin-bottom:16px">⛔ تم إبلاغ الأدمن بالأمر تلقائياً</div>
    <button onclick="this.closest('div').parentElement.remove()" style="padding:12px 32px;background:linear-gradient(135deg,#b62324,#f85149);border:none;border-radius:10px;color:#fff;font-weight:800;cursor:pointer;font-size:15px;letter-spacing:.5px;box-shadow:0 4px 20px rgba(248,81,73,.4)">حسناً، فهمت ✓</button>
  </div>`;
  document.body.appendChild(overlay);
}


async function uploadAndExtract(inp){
  const f=inp.files[0]; if(!f) return;
  toast('⬆ Uploading archive...', false, true);
  const fd=new FormData();
  fd.append('file',f);
  fd.append('path',currentPath);
  const r=await fetch('/api/files/upload',{method:'POST',body:fd});
  const d=await r.json();
  if(!d.success){ toast('❌ Upload failed', true); return; }
  const archivePath=currentPath.replace(/\/*$/,'')+'/'+d.filename;
  const destPath=currentPath.replace(/\/*$/,'')+'/'+d.filename.replace(/\.(zip|tar\.gz|tar|rar|gz)$/i,'');
  const er=await fetch('/api/files/extract',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({archive:archivePath,dest:destPath})});
  const ed=await er.json();
  toast(ed.success?`📦 Extracted: ${ed.extracted} files`:'❌ Extract failed: '+(ed.error||''), !ed.success);
  loadFiles(currentPath);
  inp.value='';
}

function openExtractModal(srcPath){
  document.getElementById('extract-src').value=srcPath;
  document.getElementById('extract-dest').value='';
  openModal('extract-modal');
}

async function doExtract(){
  const src=document.getElementById('extract-src').value;
  const destIn=document.getElementById('extract-dest').value.trim();
  const dest=destIn || src.replace(/\.(zip|tar\.gz|tar|rar|gz)$/i,'');
  const r=await fetch('/api/files/extract',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({archive:src,dest})});
  const d=await r.json();
  toast(d.success?`📦 Extracted: ${d.extracted} files`:'❌ '+(d.error||'Failed'), !d.success);
  if(d.success){ closeModal('extract-modal'); loadFiles(currentPath); }
}

// ─── DB ───
async function createDB(){
  const n=document.getElementById('db-name').value.trim(); if(!n) return;
  const r=await fetch('/api/files/create',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({path:currentPath+'/'+n+'.json',content:'{}'})});
  const d=await r.json();
  toast(d.success?'🗄 DB created':'Failed', !d.success);
}

// ─── Schedules ───
async function addSchedule(){
  const name=document.getElementById('sch-name').value.trim();
  const cmd=document.getElementById('sch-cmd').value.trim();
  const cron=document.getElementById('sch-cron').value.trim();
  if(!name||!cmd) return;
  const r=await fetch('/api/schedules/add',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name,command:cmd,schedule:cron})});
  const d=await r.json();
  toast(d.success?'⏰ Schedule added':'Failed', !d.success);
}

// ─── NODE.JS ───
// ─── Node.js ───────────────────────────────────────────────────────────────

// ─── Hosting live URL preview ────────────────────────────────────────────────
document.addEventListener('input', e => {
  if(e.target.id === 'netlify-name'){
    const v = e.target.value.trim() || 'your-site';
    const el = document.getElementById('netlify-url-preview');
    if(el) el.textContent = v + '.netlify.app';
  }
  if(e.target.id === 'vercel-name'){
    const v = e.target.value.trim() || 'your-project';
    const el = document.getElementById('vercel-url-preview');
    if(el) el.textContent = v + '.vercel.app';
  }
});

// ─── Hosting: Netlify + Vercel ──────────────────────────────────────────────
async function netlifyTest(){
  const token = document.getElementById('netlify-token').value.trim();
  if(!token){ toast('ادخل Netlify Token', true); return; }
  const out = document.getElementById('netlify-out');
  out.style.display='block'; out.className='deploy-out';
  out.textContent='🔌 Testing token...';
  try{
    const r = await fetch('/api/hosting/netlify/test',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
    const d = await r.json();
    if(d.success) out.textContent='✅ Token valid — Account: '+escapeHtml(d.email||'OK');
    else { out.textContent='❌ '+escapeHtml(d.error||'Invalid token'); out.className='deploy-out err'; }
  }catch(e){ out.textContent='❌ '+e; out.className='deploy-out err'; }
}

async function netlifyDeploy(){
  const token = document.getElementById('netlify-token').value.trim();
  const zip   = document.getElementById('netlify-zip').value.trim();
  const name  = document.getElementById('netlify-name').value.trim();
  if(!token||!zip){ toast('ادخل Token والـ ZIP path', true); return; }
  const out = document.getElementById('netlify-out');
  out.style.display='block'; out.className='deploy-out';
  out.textContent='⏳ Deploying to Netlify...';
  try{
    const r = await fetch('/api/hosting/netlify/deploy',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({token,zip_path:zip,name})});
    const d = await r.json();
    if(d.success){
      out.textContent='✅ Deployed!\n🔗 URL: '+escapeHtml(d.url)+'\n📋 Site ID: '+escapeHtml(d.site_id||'');
      loadDeployments();
    } else { out.textContent='❌ '+escapeHtml(d.error||'Failed'); out.className='deploy-out err'; }
  }catch(e){ out.textContent='❌ '+e; out.className='deploy-out err'; }
}

async function vercelTest(){
  const token = document.getElementById('vercel-token').value.trim();
  if(!token){ toast('ادخل Vercel Token', true); return; }
  const out = document.getElementById('vercel-out');
  out.style.display='block'; out.className='deploy-out';
  out.textContent='🔌 Testing token...';
  try{
    const r = await fetch('/api/hosting/vercel/test',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
    const d = await r.json();
    if(d.success) out.textContent='✅ Token valid — '+escapeHtml(d.username||'OK');
    else { out.textContent='❌ '+escapeHtml(d.error||'Invalid token'); out.className='deploy-out err'; }
  }catch(e){ out.textContent='❌ '+e; out.className='deploy-out err'; }
}

async function vercelDeploy(){
  const token = document.getElementById('vercel-token').value.trim();
  const zip   = document.getElementById('vercel-zip').value.trim();
  const name  = document.getElementById('vercel-name').value.trim();
  if(!token||!zip){ toast('ادخل Token والـ ZIP path', true); return; }
  const out = document.getElementById('vercel-out');
  out.style.display='block'; out.className='deploy-out';
  out.textContent='⏳ Deploying to Vercel...';
  try{
    const r = await fetch('/api/hosting/vercel/deploy',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({token,zip_path:zip,name})});
    const d = await r.json();
    if(d.success){
      out.textContent='✅ Deployed!\n🔗 URL: '+escapeHtml(d.url)+'\n📋 Deployment: '+escapeHtml(d.deployment_id||'');
      loadDeployments();
    } else { out.textContent='❌ '+escapeHtml(d.error||'Failed'); out.className='deploy-out err'; }
  }catch(e){ out.textContent='❌ '+e; out.className='deploy-out err'; }
}

async function loadDeployments(){
  const el = document.getElementById('deployments-list');
  if(!el) return;
  el.innerHTML = '<div style="color:var(--text2);font-size:12px">⏳ Loading...</div>';
  try{
    const r = await fetch('/api/hosting/deployments');
    const d = await r.json();
    if(!(d.deployments||[]).length){
      el.innerHTML='<div style="color:var(--text3);font-size:12px;padding:8px">No deployments yet.</div>';
      return;
    }
    el.innerHTML = d.deployments.map(dep=>`
      <div style="display:flex;align-items:center;justify-content:space-between;
        padding:10px 12px;background:var(--bg3);border:1px solid var(--border);
        border-radius:8px;margin-bottom:6px;gap:10px;flex-wrap:wrap">
        <div>
          <div style="font-size:12px;font-weight:700;color:var(--text)">
            ${dep.platform==='netlify'?'▲':'▶'} ${escapeHtml(dep.name||dep.site_id||dep.deployment_id||'—')}
          </div>
          <div style="font-size:11px;color:var(--text2);margin-top:2px">${escapeHtml(dep.platform)} · ${escapeHtml(dep.time||'')}</div>
        </div>
        <a href="${escapeHtml(dep.url)}" target="_blank"
          style="color:#58a6ff;font-size:11px;font-family:monospace;word-break:break-all">
          ${escapeHtml(dep.url)}
        </a>
      </div>`).join('');
  }catch(e){ el.innerHTML='<div style="color:var(--red);font-size:12px">Error loading</div>'; }
}

// ─── Commands tab ────────────────────────────────────────────────────────────
function toggleCmdGroup(key){
  const body  = document.getElementById('pg-'+key);
  const arrow = document.getElementById('pg-'+key+'-arrow');
  if(!body) return;
  const open = body.style.display !== 'none';
  body.style.display  = open ? 'none' : 'block';
  if(arrow) arrow.textContent = open ? '▼' : '▲';
}

function sendCmdToTerminal(cmd){
  if(!activeTerminalId) return;
  const inp = document.getElementById('cmd-field-'+activeTerminalId);
  if(inp){
    inp.value = cmd;
    focusTerminal(activeTerminalId);
    document.querySelectorAll('.tab-item').forEach(t=>{
      if(t.dataset.tab==='console') t.click();
    });
  }
}




// ─── Users (master) ───
function onPlanChange(){
  const plan = document.getElementById('u-plan').value;
  const wrap = document.getElementById('u-custom-days-wrap');
  if(wrap) wrap.style.display = plan==='custom' ? 'block' : 'none';
}

async function addUser(){
  const plan = document.getElementById('u-plan').value;
  const data={
    username:    document.getElementById('u-name').value.trim(),
    password:    document.getElementById('u-pass').value,
    tg_username: (document.getElementById('u-tg').value||'').trim().replace('@',''),
    max_sessions:parseInt(document.getElementById('u-max').value)||1,
    max_servers: parseInt(document.getElementById('u-maxsrv').value)||1,
    main_file:   document.getElementById('u-main').value||'main.py',
    plan:        plan,
    expiry_days: plan==='custom' ? (parseInt(document.getElementById('u-days').value)||7) : undefined
  };
  if(!data.username||!data.password){ toast('Fill all fields', true); return; }
  const r=await fetch('/api/users/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const d=await r.json();
  toast(d.success?'✅ User added':'❌ '+(d.error||''), !d.success);
  if(d.success) loadUsers();
}

const PLAN_LABELS = {free_trial:'🆓 Free Trial',paid_20:'⭐ 20 Day',paid_30:'💎 30 Day',custom:'🎯 Custom'};

async function loadUsers(){
  try{
    const r=await fetch('/api/users/list');
    const d=await r.json();
    const el=document.getElementById('users-list'); if(!el) return;
    el.innerHTML='';
    (d.users||[]).forEach(u=>{
      const card=document.createElement('div');
      card.className='section-card';
      card.style.marginBottom='10px';
      const isActive=u.active!==false;
      const expStr = u.expiry ? (() => {
        const diff = Math.ceil((new Date(u.expiry) - new Date()) / 86400000);
        return diff > 0 ? `<span style="color:${diff<3?'var(--red)':'var(--green)'}">⏳ ${diff} يوم متبقي</span>` : '<span style="color:var(--red)">❌ منتهي</span>';
      })() : '';
      const planLabel = PLAN_LABELS[u.plan||'free_trial'] || u.plan || '—';
      // password hash display (first 16 chars)
      const pwDisplay = u.password_hash ? u.password_hash.substring(0,16)+'...' : '—';
      card.innerHTML=`
        <div class="section-body">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap">
            <div>
              <div style="font-size:15px;font-weight:700;color:var(--text)">👤 ${escapeHtml(u.username)}</div>
              <div style="font-size:12px;color:var(--text2);margin-top:4px;display:flex;flex-wrap:wrap;gap:8px">
                ${u.tg_username?`<span>🔵 @${escapeHtml(u.tg_username)}</span>`:''}
                <span>${planLabel}</span>
                ${expStr}
                <span style="color:${isActive?'var(--green)':'var(--yellow)'}">${isActive?'✅ Active':'⏳ Pending'}</span>
              </div>
              <div style="font-size:11px;color:var(--text3);margin-top:6px;font-family:monospace">
                🔑 Hash: ${escapeHtml(pwDisplay)}
                <button onclick="togglePwHash(this,'${escapeHtml(u.password_hash||'')}')" style="background:none;border:1px solid var(--border2);border-radius:4px;color:var(--text2);font-size:10px;padding:1px 6px;cursor:pointer;margin-left:6px">👁 Show</button>
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              ${!isActive?`<button class="btn-action green" onclick="approveUser('${escapeHtml(u.username)}')">✅ Approve</button>`:''}
              <button class="btn-action gray" onclick="openEditUser('${escapeHtml(u.username)}','${u.max_sessions||1}','${u.max_servers||1}','${escapeHtml(u.main_file||'main.py')}')">✏️ Edit</button>
              <button class="btn-action danger" onclick="deleteUser('${escapeHtml(u.username)}')">🗑</button>
            </div>
          </div>
        </div>`;
      el.appendChild(card);
    });
  }catch(e){}
}

function togglePwHash(btn, fullHash){
  const prev = btn.previousSibling || btn.parentNode.childNodes[0];
  if(btn.dataset.showing==='1'){
    btn.previousElementSibling ? (btn.previousElementSibling.textContent = '🔑 Hash: '+fullHash.substring(0,16)+'...') : null;
    btn.textContent='👁 Show';
    btn.dataset.showing='0';
  } else {
    btn.previousElementSibling ? (btn.previousElementSibling.textContent = '🔑 Hash: '+fullHash) : null;
    btn.textContent='🙈 Hide';
    btn.dataset.showing='1';
  }
}

async function approveUser(username){
  const r=await fetch('/api/users/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username})});
  const d=await r.json();
  toast(d.success?`✅ ${username} approved`:'Failed', !d.success);
  if(d.success) loadUsers();
}

function openEditUser(name, maxS, maxSrv, mainF){
  document.getElementById('eu-name').value=name;
  document.getElementById('eu-pass').value='';
  document.getElementById('eu-max').value=maxS;
  document.getElementById('eu-maxsrv').value=maxSrv;
  document.getElementById('eu-main').value=mainF;
  document.getElementById('eu-days').value=30;
  openModal('edit-user-modal');
}

async function saveEditUser(){
  const data={
    username:document.getElementById('eu-name').value,
    password:document.getElementById('eu-pass').value||undefined,
    max_sessions:parseInt(document.getElementById('eu-max').value)||1,
    max_servers:parseInt(document.getElementById('eu-maxsrv').value)||1,
    main_file:document.getElementById('eu-main').value,
    expiry_days:parseInt(document.getElementById('eu-days').value)||30
  };
  const r=await fetch('/api/users/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const d=await r.json();
  toast(d.success?'✅ Updated':'Failed', !d.success);
  if(d.success){ closeModal('edit-user-modal'); loadUsers(); }
}

async function deleteUser(username){
  if(!confirm(`Delete user "${username}" and all files?`)) return;
  const r=await fetch('/api/users/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username})});
  const d=await r.json();
  toast(d.success?'🗑 Deleted':'Failed', !d.success);
  if(d.success) loadUsers();
}

// ─── Backups ───
async function createBackup(){
  toast('💾 Creating backup...', false, true);
  const r=await fetch('/api/backups/create',{method:'POST'});
  const d=await r.json();
  toast(d.success?'✅ Backup created':'❌ Failed', !d.success);
  if(d.success) loadBackups();
}

async function loadBackups(){
  try{
    const r=await fetch('/api/backups/list');
    const d=await r.json();
    const el=document.getElementById('backups-list'); if(!el) return;
    if(!(d.backups||[]).length){ el.innerHTML='<div style="color:var(--text3);padding:10px">No backups found.</div>'; return; }
    el.innerHTML='';
    d.backups.forEach(b=>{
      el.innerHTML+=`<div class="zip-item"><div><div class="z-name">📦 ${escapeHtml(b.name)}</div><div class="z-size">${escapeHtml(b.size||'')}</div></div><button class="btn-action gray" style="font-size:11px" onclick="window.open('/api/backups/download?name=${encodeURIComponent(b.name)}','_blank')">⬇ Download</button></div>`;
    });
  }catch(e){}
}

// ─── Ports ───
async function addPort(){
  const port=parseInt(document.getElementById('new-port').value);
  const note=document.getElementById('new-port-note').value.trim();
  if(!port){ toast('Enter port number', true); return; }
  const r=await fetch('/api/ports/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({port,note})});
  const d=await r.json();
  toast(d.success?'✅ Port added':'❌ '+(d.error||''), !d.success);
  if(d.success) loadPorts();
}

async function loadPorts(){
  try{
    const r=await fetch('/api/ports/list');
    const d=await r.json();
    const el=document.getElementById('ports-list'); if(!el) return;
    if(!(d.ports||[]).length){ el.innerHTML='<div style="color:var(--text3);padding:10px">No extra ports configured.</div>'; return; }
    el.innerHTML='';
    d.ports.forEach(p=>{
      el.innerHTML+=`<div class="zip-item"><div><div class="z-name">🔌 Port ${p.port}</div><div class="z-size">${escapeHtml(p.note||'')} · ${escapeHtml(p.status||'idle')}</div></div><button class="btn-action danger" style="font-size:11px" onclick="deletePort(${p.port})">Delete</button></div>`;
    });
  }catch(e){}
}

async function deletePort(port){
  if(!confirm(`Delete port ${port}?`)) return;
  const r=await fetch('/api/ports/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({port})});
  const d=await r.json();
  toast(d.success?'Deleted':'Failed', !d.success);
  if(d.success) loadPorts();
}

async function scanPorts(){
  const host=document.getElementById('scan-host').value.trim();
  const ports=document.getElementById('scan-ports').value.split(',').map(p=>parseInt(p.trim())).filter(Boolean);
  if(!host||!ports.length){ toast('Enter host and ports', true); return; }
  const r=await fetch('/api/network/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host,ports})});
  const d=await r.json();
  const el=document.getElementById('scan-results');
  el.innerHTML=(d.results||[]).map(p=>`<div style="display:flex;gap:8px;padding:4px 0;font-size:12px"><span style="color:${p.open?'var(--green)':'var(--red)'}">●</span><span style="color:var(--text)">Port ${p.port}</span><span style="color:${p.open?'var(--green)':'var(--red)'}"> — ${p.open?'OPEN':'CLOSED'}</span></div>`).join('');
}

// ─── Settings ───
async function changePassword(){
  const cur=document.getElementById('cur-pass').value;
  const nw=document.getElementById('new-pass').value;
  if(!cur||!nw){ toast('Fill all fields', true); return; }
  const r=await fetch('/api/master/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:cur,new_password:nw})});
  const d=await r.json();
  toast(d.success?'✅ Password changed':'❌ Wrong password', !d.success);
}

async function loadSysinfo(){
  const r=await fetch('/api/sysinfo');
  const d=await r.json();
  document.getElementById('sysinfo-box').textContent=d.info||'';
}

async function setStartupFile(){
  const f=document.getElementById('startup-file').value.trim(); if(!f) return;
  const r=await fetch('/api/files/set-main',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f,path:''})});
  const d=await r.json();
  toast(d.success?'🚀 Startup set: '+f:'Failed', !d.success);
}

async function installPip(){
  const p=document.getElementById('pip-pkg').value.trim(); if(!p) return;
  toast('📦 Installing '+p+'...',false,true);
  const r=await fetch('/api/packages/install/pip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({package:p})});
  const d=await r.json();
  toast(d.success?'✅ Installed: '+p:'❌ Failed', !d.success);
}

async function installNpm(){
  const p=document.getElementById('npm-pkg').value.trim(); if(!p) return;
  toast('📦 npm install '+p+'...',false,true);
  const r=await fetch('/api/packages/install/npm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({package:p})});
  const d=await r.json();
  toast(d.success?'✅ Installed: '+p:'❌ Failed', !d.success);
}

// ─── Activity ───
async function loadActivity(){
  try{
    const r=await fetch('/api/activity');
    const d=await r.json();
    const el=document.getElementById('activity-list'); if(!el) return;
    if(!(d.events||[]).length){ el.innerHTML='<div style="color:var(--text3);padding:10px">No activity yet.</div>'; return; }
    el.innerHTML='';
    d.events.slice(0,100).forEach(e=>{
      el.innerHTML+=`<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);font-size:12px">
        <span style="color:var(--accent);min-width:60px;flex-shrink:0">${escapeHtml(e.time_text||'').split(' ')[1]||''}</span>
        <span style="color:var(--text2);min-width:80px;flex-shrink:0">${escapeHtml(e.username||'')}</span>
        <span style="color:var(--text)">${escapeHtml(e.action||'')} ${e.details?'<span style="color:var(--text3)">'+escapeHtml(e.details)+'</span>':''}</span>
      </div>`;
    });
  }catch(e){}
}

// ─── Servers Modal ───
function openServersModal(){ loadServersModal(); openModal('servers-modal'); }
async function loadServersModal(){
  const list=document.getElementById('servers-modal-list');
  list.innerHTML='<div style="color:var(--text2);text-align:center;padding:20px">Loading...</div>';
  try{
    if(IS_MASTER){
      const r=await fetch('/api/users/list');
      const d=await r.json();
      if(!(d.users||[]).length){ list.innerHTML='<div style="color:var(--text3);padding:20px;text-align:center">No servers.</div>'; return; }
      list.innerHTML='';
      d.users.forEach(u=>{
        const card=document.createElement('div');
        card.className='srv-card';
        card.innerHTML=`
          <div>
            <div class="srv-name">🖥 ${escapeHtml(u.username)}</div>
            <div class="srv-meta">Sessions: ${u.active_sessions||0}/${u.max_sessions||1} · Servers: ${u.max_servers||1}</div>
          </div>
          <button class="srv-del-btn" onclick="deleteUser('${escapeHtml(u.username)}')">🗑</button>`;
        list.appendChild(card);
      });
    } else {
      const r=await fetch('/api/profile');
      const d=await r.json();
      list.innerHTML=`<div class="srv-card"><div><div class="srv-name">🖥 ${escapeHtml(d.username||'')}</div><div class="srv-meta">Your server</div></div><span style="color:var(--green);font-size:12px;font-weight:600">● Online</span></div>`;
    }
  }catch(e){ list.innerHTML='<div style="color:var(--red);padding:20px">Failed to load</div>'; }
}

// ─── Search ───
function loadSearch(){
  const q=prompt('Search files:'); if(!q) return;
  fetch('/api/exec',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({command:`find "${USER_PATH}" -name "*${q}*" 2>/dev/null | head -30`, cwd:USER_PATH})})
    .then(r=>r.json()).then(d=>{
      if(activeTerminalId){
        const box=document.getElementById('console-output-'+activeTerminalId);
        if(box){ const footer=document.getElementById('term-footer-'+activeTerminalId); while(box.firstChild&&box.firstChild!==footer) box.removeChild(box.firstChild); }
      }
      (d.output||'').split('\n').forEach(l=>{ if(l.trim()) appendConsole(l); });
      document.querySelectorAll('.tab-item').forEach(t=>{ if(t.dataset.tab==='console') t.click(); });
    });
}

// ─── Owner Panel ───
async function loadOwnerPanel(){
  if(!IS_MASTER) return;
  try{
    const [statsR,usersR,maintR,ownerR]=await Promise.all([
      fetch('/api/owner/stats'),fetch('/api/users/list'),
      fetch('/api/owner/maintenance'),fetch('/api/owner/config')
    ]);
    const stats=await statsR.json();
    const users=await usersR.json();
    const maint=await maintR.json();
    const ownerCfg=await ownerR.json();
    document.getElementById('ow-users').textContent=(users.users||[]).length;
    document.getElementById('ow-servers').textContent=stats.total_servers||0;
    document.getElementById('ow-bots').textContent=stats.active_bots||0;
    document.getElementById('ow-zips').textContent=stats.zip_files||0;
    const chk=document.getElementById('maint-toggle-chk');
    if(chk) chk.checked=maint.enabled||false;
    const msgEl=document.getElementById('maint-msg');
    if(msgEl) msgEl.value=maint.message||'';
    const badge=document.getElementById('bot-status-badge');
    const botPanel=document.getElementById('bot-control-panel');
    if(ownerCfg.bot_linked){
      if(badge) badge.innerHTML='<span style="color:var(--green);font-size:13px;font-weight:700">✅ Bot Linked & Active</span>';
      if(botPanel) botPanel.style.display='block';
    } else {
      if(badge) badge.innerHTML='<span style="color:var(--yellow);font-size:13px;font-weight:700">⚠️ Bot Not Linked</span>';
      if(botPanel) botPanel.style.display='none';
    }
    const pnEl=document.getElementById('panel-name-inp');
    const pwEl=document.getElementById('panel-welcome-inp');
    if(pnEl) pnEl.value=ownerCfg.panel_name||'SERVER HUB';
    if(pwEl) pwEl.value=ownerCfg.welcome_msg||'';
    loadOwnerZips();
    loadAnnouncements();
    loadPendingUsers();
  }catch(e){ toast('Failed to load owner panel', true); }
}

async function toggleMaintenance(){
  const chk=document.getElementById('maint-toggle-chk');
  const msg=document.getElementById('maint-msg').value;
  const r=await fetch('/api/owner/maintenance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:chk.checked,message:msg})});
  const d=await r.json();
  toast(d.success?(chk.checked?'🔧 Maintenance ON':'✅ Maintenance OFF'):'Failed', !d.success);
}

async function saveMaintMsg(){
  const chk=document.getElementById('maint-toggle-chk');
  const msg=document.getElementById('maint-msg').value;
  const r=await fetch('/api/owner/maintenance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:chk.checked,message:msg})});
  const d=await r.json();
  toast(d.success?'✅ Saved':'Failed', !d.success);
}

async function linkBot(){
  const token=document.getElementById('tg-token').value.trim();
  const ownerId=document.getElementById('tg-ownerid').value.trim();
  if(!token||!ownerId){ toast('Enter token and owner ID', true); return; }
  const statusEl=document.getElementById('bot-link-status');
  statusEl.textContent='⏳ Linking...';
  const r=await fetch('/api/owner/bot/link',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,owner_id:ownerId})});
  const d=await r.json();
  if(d.success){
    statusEl.style.color='var(--green)';
    statusEl.textContent='✅ Bot linked: @'+(d.bot_username||'');
    toast('✅ Bot linked!');
    loadOwnerPanel();
  } else {
    statusEl.style.color='var(--red)';
    statusEl.textContent='❌ '+(d.error||'Failed');
    toast('❌ '+( d.error||'Failed'), true);
  }
}

async function unlinkBot(){
  if(!confirm('Unlink bot?')) return;
  const r=await fetch('/api/owner/bot/unlink',{method:'POST'});
  const d=await r.json();
  toast(d.success?'Bot unlinked':'Failed', !d.success);
  if(d.success) loadOwnerPanel();
}

async function botAction(action){
  const r=await fetch('/api/owner/bot/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
  const d=await r.json();
  const bc=document.getElementById('bot-console');
  if(bc) bc.textContent+='['+new Date().toLocaleTimeString()+'] '+action+': '+(d.message||d.error||'done')+'\n';
  toast(d.success?'Bot '+action:'Failed', !d.success);
}

async function sendBotCmd(){
  const inp=document.getElementById('bot-cmd-input');
  const cmd=inp.value.trim(); if(!cmd) return;
  inp.value='';
  const r=await fetch('/api/owner/bot/cmd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})});
  const d=await r.json();
  const bc=document.getElementById('bot-console');
  if(bc){ bc.textContent+='» '+cmd+'\n'+(d.output||d.error||'')+'\n'; bc.scrollTop=bc.scrollHeight; }
}

async function refreshBotStats(){
  const r=await fetch('/api/owner/stats');
  const d=await r.json();
  document.getElementById('ow-servers').textContent=d.total_servers||0;
  document.getElementById('ow-bots').textContent=d.active_bots||0;
  toast('Stats refreshed',false,true);
}

async function savePanelSettings(){
  const name=document.getElementById('panel-name-inp').value.trim();
  const msg=document.getElementById('panel-welcome-inp').value.trim();
  const r=await fetch('/api/owner/config/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({panel_name:name,welcome_msg:msg})});
  const d=await r.json();
  toast(d.success?'✅ Settings saved':'Failed', !d.success);
}

async function loadOwnerZips(){
  try{
    const r=await fetch('/api/owner/zips');
    const d=await r.json();
    const list=document.getElementById('owner-zip-list'); if(!list) return;
    if(!(d.zips||[]).length){ list.innerHTML='<div style="color:var(--text3);padding:10px">No ZIP files.</div>'; return; }
    list.innerHTML='';
    d.zips.forEach(z=>{
      list.innerHTML+=`<div class="zip-item"><div><div class="z-name">📦 ${escapeHtml(z.name)}</div><div class="z-size">${escapeHtml(z.user||'')} · ${escapeHtml(z.size||'')}</div></div><div style="display:flex;gap:6px"><button class="btn-action gray" style="font-size:11px" onclick="window.open('/api/owner/zips/download?path=${encodeURIComponent(z.path)}','_blank')">⬇</button><button class="btn-action danger" style="font-size:11px" onclick="deleteOwnerZip('${escapeHtml(z.path)}')">🗑</button></div></div>`;
    });
  }catch(e){}
}

async function downloadAllZips(){ window.open('/api/owner/zips/download-all','_blank'); }

async function deleteOwnerZip(path){
  if(!confirm('Delete ZIP?')) return;
  const r=await fetch('/api/owner/zips/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});
  const d=await r.json();
  toast(d.success?'🗑 Deleted':'Failed', !d.success);
  if(d.success) loadOwnerZips();
}

// ─── Security Alerts ────────────────────────────────────────────────────────
async function loadSecurityAlerts(){
  const el=document.getElementById('security-alerts-list');
  if(!el) return;
  el.innerHTML='<div style="color:var(--text2);padding:10px;text-align:center">⏳ جاري التحميل...</div>';
  try{
    const r=await fetch('/api/security/alerts');
    const d=await r.json();
    if(!(d.alerts||[]).length){
      el.innerHTML='<div style="color:var(--green);padding:12px;text-align:center;font-size:13px">✅ لا توجد تنبيهات أمنية — كل شيء نظيف!</div>';
      return;
    }
    el.innerHTML='';
    d.alerts.forEach(a=>{
      const threats=(a.threats||[]).join(' | ');
      const reviewed=a.reviewed;
      const div=document.createElement('div');
      div.style.cssText=`
        background:${reviewed?'var(--bg2)':'rgba(248,81,73,.05)'};
        border:1px solid ${reviewed?'var(--border)':'rgba(248,81,73,.3)'};
        border-radius:10px;padding:12px 14px;margin-bottom:8px;
      `;
      div.innerHTML=`
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap">
          <div style="flex:1">
            <div style="font-size:13px;font-weight:700;color:${reviewed?'var(--text2)':'#f85149'};margin-bottom:4px">
              ${reviewed?'✅':'🚨'} ${escapeHtml(a.filename||'—')}
              <span style="font-size:10px;color:var(--text3);font-weight:400;margin-left:6px">#${escapeHtml(a.id||'')}</span>
            </div>
            <div style="font-size:11px;color:var(--text2);margin-bottom:4px">
              👤 ${escapeHtml(a.username||'—')} &nbsp;·&nbsp; 🌐 ${escapeHtml(a.ip||'—')} &nbsp;·&nbsp; 🕐 ${escapeHtml(a.time||'—')}
            </div>
            <div style="font-size:11px;color:#ffcc00;font-family:monospace;word-break:break-word">
              ${escapeHtml(threats)}
            </div>
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0">
            ${!reviewed?`<button class="btn-action green" style="font-size:10px;padding:5px 10px"
              onclick="markAlertReviewed('${escapeHtml(a.id)}',this)">✓ تمت المراجعة</button>`:''}
            <button class="btn-action danger" style="font-size:10px;padding:5px 10px"
              onclick="deleteAlert('${escapeHtml(a.id)}',this)">🗑</button>
          </div>
        </div>`;
      el.appendChild(div);
    });
  }catch(e){
    el.innerHTML='<div style="color:var(--red);padding:10px">فشل تحميل التنبيهات</div>';
  }
}

async function markAlertReviewed(id, btn){
  const r=await fetch('/api/security/alerts/review',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const d=await r.json();
  if(d.success){ toast('✅ تمت المراجعة',false,true); loadSecurityAlerts(); }
  else toast('فشل',true);
}

async function deleteAlert(id, btn){
  const r=await fetch('/api/security/alerts/delete',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const d=await r.json();
  if(d.success){ toast('🗑 تم الحذف',false,true); loadSecurityAlerts(); }
  else toast('فشل',true);
}

async function clearSecurityAlerts(){
  if(!confirm('حذف جميع التنبيهات الأمنية؟')) return;
  const r=await fetch('/api/security/alerts/clear',{method:'POST'});
  const d=await r.json();
  toast(d.success?'🗑 تم مسح السجل':'فشل',!d.success);
  if(d.success) loadSecurityAlerts();
}

async function loadAnnouncements(){
  try{
    const r=await fetch('/api/owner/announcements');
    const d=await r.json();
    const list=document.getElementById('ann-list'); if(!list) return;
    if(!(d.list||[]).length){ list.innerHTML='<div style="color:var(--text3);padding:8px">No announcements.</div>'; return; }
    list.innerHTML='';
    d.list.forEach((a,i)=>{
      list.innerHTML+=`<div class="zip-item"><div><div class="z-name">${escapeHtml(a.text)}</div><div class="z-size">${escapeHtml(a.time||'')}</div></div><button class="btn-action danger" style="font-size:11px" onclick="deleteAnn(${i})">🗑</button></div>`;
    });
  }catch(e){}
}

async function addAnnouncement(){
  const txt=document.getElementById('ann-txt').value.trim(); if(!txt) return;
  const r=await fetch('/api/owner/announcements/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})});
  const d=await r.json();
  toast(d.success?'📢 Added':'Failed', !d.success);
  if(d.success){ document.getElementById('ann-txt').value=''; loadAnnouncements(); }
}

async function deleteAnn(idx){
  const r=await fetch('/api/owner/announcements/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx})});
  const d=await r.json();
  toast(d.success?'Deleted':'Failed', !d.success);
  if(d.success) loadAnnouncements();
}

async function ownerBroadcast(){
  const txt=document.getElementById('ann-txt').value.trim();
  if(!txt){ toast('Enter message first', true); return; }
  const r=await fetch('/api/owner/broadcast',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:txt})});
  const d=await r.json();
  toast(d.success?`📡 Sent to ${d.count||0} users`:'Failed', !d.success);
}

async function loadPendingUsers(){
  try{
    const r=await fetch('/api/users/pending');
    const d=await r.json();
    const el=document.getElementById('pending-users-list'); if(!el) return;
    if(!(d.users||[]).length){ el.innerHTML='<div style="color:var(--text3);padding:10px">No pending registrations.</div>'; return; }
    el.innerHTML='';
    d.users.forEach(u=>{
      el.innerHTML+=`<div class="pending-card">
        <div><div class="p-user">📋 ${escapeHtml(u.username)} ${u.tg_username?`<span style="color:#60a5fa;font-size:11px">🔵 @${escapeHtml(u.tg_username)}</span>`:''}</div><div class="p-time">Registered: ${escapeHtml(u.created||'')}</div></div>
        <div style="display:flex;gap:6px">
          <button class="btn-action green" onclick="approveUser('${escapeHtml(u.username)}')">✅ Approve</button>
          <button class="btn-action danger" onclick="deleteUser('${escapeHtml(u.username)}')">❌ Reject</button>
        </div>
      </div>`;
    });
  }catch(e){}
}

async function ownerAction(action){
  if(action!=='restart_panel'&&!confirm('Confirm: '+action+'?')) return;
  const r=await fetch('/api/owner/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
  const d=await r.json();
  toast(d.success?'✅ Done: '+action:'Failed', !d.success);
}

function fmtExpiry(exp){
  if(!exp||exp==='∞') return '∞';
  try{
    const d=new Date(exp);
    const diff=Math.ceil((d-new Date())/(1000*86400));
    return diff>0?`Expires in ${diff} days`:'❌ Expired';
  }catch(e){ return exp; }
}

// ─── AI Chat ───
const AI_API_KEY = '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';
const AI_BASE_URL = 'https://integrate.api.nvidia.com/v1';
const AI_MODEL = 'openai/gpt-oss-120b';
let aiHistory = [];
let aiStreaming = false;

function aiKeyDown(e){
  if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendAiMessage(); }
}

function aiQuick(txt){
  document.getElementById('ai-input').value = txt;
  document.getElementById('ai-input').focus();
}

function clearAiChat(){
  aiHistory = [];
  const box = document.getElementById('ai-messages');
  box.innerHTML = `<div class="ai-msg ai-assistant"><div class="ai-bubble"><span class="ai-avatar">🤖</span><div class="ai-text">تم مسح المحادثة. كيف يمكنني مساعدتك؟</div></div></div>`;
}

function renderAiText(raw){
  // basic markdown: code blocks, inline code, bold
  return raw
    .replace(/```(\w*)\n?([\s\S]*?)```/g, (_,lang,code)=>`<pre><code>${escapeHtml(code.trim())}</code></pre>`)
    .replace(/`([^`]+)`/g, (_,c)=>`<code>${escapeHtml(c)}</code>`)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g,'<br>');
}

function appendAiMsg(role, text, isStreaming=false){
  const box = document.getElementById('ai-messages');
  const isUser = role==='user';
  const div = document.createElement('div');
  div.className = `ai-msg ${isUser?'ai-user':'ai-assistant'}`;
  div.id = isStreaming ? 'ai-streaming-msg' : '';
  div.innerHTML = `<div class="ai-bubble">
    <span class="ai-avatar">${isUser?'👤':'🤖'}</span>
    <div class="ai-text" id="${isStreaming?'ai-stream-text':''}">${isUser?escapeHtml(text):renderAiText(text)}</div>
  </div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function showAiTyping(){
  const box = document.getElementById('ai-messages');
  const div = document.createElement('div');
  div.className = 'ai-msg ai-assistant';
  div.id = 'ai-typing-indicator';
  div.innerHTML = `<div class="ai-bubble"><span class="ai-avatar">🤖</span><div class="ai-text"><div class="ai-typing"><span></span><span></span><span></span></div></div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function removeAiTyping(){
  const t = document.getElementById('ai-typing-indicator');
  if(t) t.remove();
}

async function sendAiMessage(){
  if(aiStreaming) return;
  const inp = document.getElementById('ai-input');
  const msg = inp.value.trim();
  if(!msg) return;
  inp.value = '';
  inp.style.height = 'auto';

  appendAiMsg('user', msg);
  aiHistory.push({role:'user', content: msg});

  aiStreaming = true;
  const btn = document.getElementById('ai-send-btn');
  btn.disabled = true;
  btn.textContent = '⏳';

  showAiTyping();

  try{
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({messages: aiHistory})
    });

    if(!resp.ok){
      removeAiTyping();
      const err = await resp.json();
      appendAiMsg('assistant', '❌ خطأ: ' + (err.error||'فشل الاتصال'));
      aiStreaming = false; btn.disabled=false; btn.textContent='➤ إرسال';
      return;
    }

    removeAiTyping();

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let reasoningText = '';

    const msgDiv = appendAiMsg('assistant', '', true);
    const textEl = document.getElementById('ai-stream-text');

    while(true){
      const {done, value} = await reader.read();
      if(done) break;
      const chunk = decoder.decode(value, {stream:true});
      const lines = chunk.split('\n');
      for(const line of lines){
        if(!line.startsWith('data:')) continue;
        const data = line.slice(5).trim();
        if(data==='[DONE]') break;
        try{
          const j = JSON.parse(data);
          const delta = j.choices?.[0]?.delta || {};
          if(delta.reasoning_content){
            reasoningText += delta.reasoning_content;
            const rb = document.getElementById('ai-reasoning');
            const tb = document.getElementById('ai-thinking-box');
            if(rb){ rb.textContent = reasoningText; rb.scrollTop=rb.scrollHeight; }
            if(tb) tb.style.display='block';
          }
          if(delta.content){
            fullText += delta.content;
            if(textEl) textEl.innerHTML = renderAiText(fullText);
            document.getElementById('ai-messages').scrollTop = 999999;
          }
        }catch(e){}
      }
    }
    if(msgDiv) msgDiv.id='';
    const textFinal = document.getElementById('ai-stream-text');
    if(textFinal) textFinal.id='';

    // hide thinking after done
    setTimeout(()=>{
      const tb = document.getElementById('ai-thinking-box');
      if(tb) tb.style.display='none';
      const rb = document.getElementById('ai-reasoning');
      if(rb) rb.textContent='';
    }, 2000);

    aiHistory.push({role:'assistant', content: fullText});
    if(aiHistory.length > 20) aiHistory = aiHistory.slice(-20);

  }catch(err){
    removeAiTyping();
    appendAiMsg('assistant','❌ خطأ في الاتصال: '+err.message);
  }

  aiStreaming = false;
  btn.disabled = false;
  btn.textContent = '➤ إرسال';
}

// ─── Init ───
loadProfile().then(()=>{ loadStats(); loadFiles(); initTerminals(); });
statsInterval = setInterval(loadStats, 5000);
</script>

</body></html>
'''

# ─────────────────────────────────────────────────────────────────────────────
#  20.  Flask Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    username = session.get('username')
    is_master = (username == MASTER_USERNAME)
    return render_template_string(get_html_template(is_master, username),
                                  session=session, user_path=get_user_path(username))

# ─── /ping — keep-alive for Render + cron-job.org ───────────────────────────
@app.route('/ping')
def ping():
    """Lightweight keep-alive endpoint.
    Use on cron-job.org: GET https://your-app.onrender.com/ping every 5–10 min
    to prevent Render free tier from sleeping.
    """
    return jsonify({
        'status': 'ok',
        'service': 'ELMODMEN SERVER HUB',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'uptime': 'running'
    }), 200

@app.route('/health')
def health():
    """Health check endpoint (alternative to /ping)."""
    return 'OK', 200


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template_string(AUTH_TEMPLATE, error=None, error_type=None)
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    h = hashlib.sha256(password.encode()).hexdigest()
    
    if username == MASTER_USERNAME and h == MASTER_PASSWORD_HASH:
        session.permanent = True
        session['logged_in'] = True
        session['username'] = username
        register_session(username)
        log_activity(username, 'auth.login', 'Master login')
        return redirect('/')
    
    users = load_users()
    if username in users and users[username].get('password') == h:
        if not users[username].get('active', False):
            log_activity(username, 'auth.login.denied', 'Pending approval')
            return render_template_string(AUTH_TEMPLATE,
                error='⚠️ Your account is pending Admin approval. Contact @Y0YY12',
                error_type='login')
        if can_user_login(username):
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            register_session(username)
            ensure_user_folder(username)
            log_activity(username, 'auth.login', 'User login')
            return redirect('/')
        else:
            return render_template_string(AUTH_TEMPLATE,
                error='❌ Session limit reached or account expired.',
                error_type='login')
    
    log_activity(username or '-', 'auth.login.failed', 'Invalid credentials')
    return render_template_string(AUTH_TEMPLATE, error='❌ Invalid credentials', error_type='login')

@app.route('/register', methods=['POST'])
def register_page():
    username    = request.form.get('username','').strip()
    password    = request.form.get('password','')
    confirm     = request.form.get('confirm_password','')
    tg_username = request.form.get('tg_username','').strip().lstrip('@')

    if not username or not password:
        return render_template_string(AUTH_TEMPLATE, error='❌ يرجى ملء جميع الحقول المطلوبة', error_type='register')
    if not tg_username:
        return render_template_string(AUTH_TEMPLATE, error='❌ يرجى إدخال يوزر التيليجرام', error_type='register')
    if password != confirm:
        return render_template_string(AUTH_TEMPLATE, error='❌ كلمات المرور غير متطابقة', error_type='register')
    if len(username) < 3:
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم 3 أحرف على الأقل', error_type='register')
    if len(password) < 4:
        return render_template_string(AUTH_TEMPLATE, error='❌ كلمة المرور 4 أحرف على الأقل', error_type='register')
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم: حروف وأرقام وـ فقط', error_type='register')

    users = load_users()
    if username in users:
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم محجوز مسبقاً', error_type='register')

    # 7 days free trial
    expiry_dt = (datetime.now() + timedelta(days=7)).isoformat()
    users[username] = {
        'password':     hashlib.sha256(password.encode()).hexdigest(),
        'tg_username':  tg_username,
        'max_sessions': 1,
        'max_servers':  1,
        'main_file':    'main.py',
        'created':      datetime.now().isoformat(),
        'expiry':       expiry_dt,
        'plan':         'free_trial',
        'active':       False  # requires admin approval
    }
    # persist immediately to DB / KV
    save_users(users)
    ensure_user_folder(username)
    log_activity(username, 'auth.register', f'tg=@{tg_username} | awaiting approval')
    return render_template_string(AUTH_TEMPLATE,
        error=f'✅ تم إرسال طلب التسجيل! انتظر موافقة الأدمن.\nيوزر تيليجرامك: @{tg_username}',
        error_type='register')

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], 'auth.logout', '')
        unregister_session(session['username'])
    session.clear()
    return redirect('/login')

# ─── API: Profile & System ───
@app.route('/api/profile')
@login_required
def get_profile():
    u = session['username']
    p = get_user_path(u)
    size = 0
    if os.path.exists(p):
        for r,d,f in os.walk(p):
            for fl in f:
                fp = os.path.join(r,fl)
                if os.path.exists(fp):
                    size += os.path.getsize(fp)
    users = load_users()
    ud = users.get(u, {})
    return jsonify({
        'username': u,
        'is_master': u == MASTER_USERNAME,
        'user_path': p,
        'created': ud.get('created','') if isinstance(ud,dict) else '',
        'expiry': ud.get('expiry','∞') if isinstance(ud,dict) else '∞',
        'disk_usage_gb': size / (1024**3)
    })

@app.route('/api/system')
@login_required
def system_info():
    return jsonify(get_system_stats())

@app.route('/api/sysinfo')
@login_required
def sysinfo():
    return jsonify({'info': f"Platform: {platform.platform()}\nCPU: {psutil.cpu_percent()}%\nMemory: {psutil.virtual_memory().percent}%\nDisk: {psutil.disk_usage('/').percent}%"})

@app.route('/api/system/action', methods=['POST'])
@login_required
def system_action_api():
    a = (request.json or {}).get('action')
    try:
        if a == 'clean':
            gc.collect()
        log_activity(session['username'], 'system.action', a or '')
        return jsonify({'success':True,'action':a})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

# ─── API: Activity ───
@app.route('/api/activity')
@login_required
def activity_api():
    data = load_json_file(ACTIVITY_FILE, {'events':[]})
    events = data.get('events',[])
    if session.get('username') != MASTER_USERNAME:
        events = [e for e in events if e.get('username') == session.get('username')]
    return jsonify({'events': events[:200]})

# ─── API: Files ───
@app.route('/api/files/main-file')
@login_required
def get_main_file_api():
    u = session['username']
    if u == MASTER_USERNAME:
        mf = MASTER_CONFIG.get('main_file','main.py')
    else:
        users = load_users()
        mf = users.get(u,{}).get('main_file','main.py') if isinstance(users.get(u),dict) else 'main.py'
    return jsonify({'success':True,'main_file':mf})

@app.route('/api/files')
@login_required
def list_files_api():
    p = request.args.get('path', get_user_path(session['username']))
    if not is_path_allowed(session['username'], p):
        return jsonify({'success':False,'error':'forbidden'}), 403
    files = []
    try:
        for n in sorted(os.listdir(p), key=lambda x:(not os.path.isdir(os.path.join(p,x)),x.lower())):
            fp = os.path.join(p,n)
            files.append({'name':n,'is_dir':os.path.isdir(fp),
                          'size':f"{os.path.getsize(fp)//1024} KB" if os.path.isfile(fp) else ''})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)}), 500
    return jsonify({'files':files})

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file_api():
    f = request.files.get('file')
    p = request.form.get('path', get_user_path(session['username']))
    if not f:
        return jsonify({'success':False,'error':'No file'}), 400
    if not is_path_allowed(session['username'], p):
        return jsonify({'success':False,'error':'Forbidden'}), 403
    try:
        filename = secure_filename(f.filename) if f.filename else 'uploaded_file'
        if not filename: filename = 'uploaded_file'
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        # Block dangerous extensions
        if ext in BLOCKED_EXTENSIONS:
            log_activity(session['username'], 'security.blocked_ext', filename)
            return jsonify({'success':False,'error':f'❌ نوع الملف .{ext} محظور لأسباب أمنية'}), 403
        os.makedirs(p, exist_ok=True)
        sp = os.path.join(p, filename)
        f.save(sp)
        # Deep content scan
        threats = scan_file_content(sp)
        if threats:
            os.remove(sp)
            threat_list = ' | '.join(threats[:5])
            log_activity(session['username'], 'security.malware_blocked', f'{filename}: {threat_list}')

            # ── حفظ التنبيه في قاعدة بيانات لوحة الأدمن ──
            alert_rec = save_security_alert(
                username=session['username'],
                filename=filename,
                threats=threats[:5],
                ip=request.remote_addr
            )

            # ── إشعار الأدمن عبر تيليجرام ──
            try:
                users_data = load_users()
                ud = users_data.get(session['username'], {})
                tg_user = ud.get('tg_username', 'غير معروف') if isinstance(ud, dict) else 'غير معروف'
                cfg = load_owner_config()
                if cfg.get('bot_linked') and cfg.get('telegram_token') and cfg.get('telegram_owner_id'):
                    threats_fmt = '\n'.join(f'   • {t}' for t in threats[:5])
                    alert_msg = (
                        f"🚨 *تحذير أمني — محاولة رفع ملف خطير!*\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"👤 *اليوزر:* `{session['username']}`\n"
                        f"📱 *تيليجرام:* `@{tg_user}`\n"
                        f"📄 *الملف:* `{filename}`\n"
                        f"🌐 *IP:* `{request.remote_addr}`\n"
                        f"🕐 *الوقت:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
                        f"🔍 *التهديدات المكتشفة:*\n{threats_fmt}\n\n"
                        f"⚠️ تم حذف الملف تلقائياً — راجع قسم الأمن في لوحة التحكم."
                    )
                    requests.post(
                        f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
                        json={'chat_id': cfg['telegram_owner_id'], 'text': alert_msg,
                              'parse_mode': 'Markdown'},
                        timeout=8
                    )
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'SECURITY_ALERT|' + threat_list}), 403
        log_activity(session['username'], 'file.upload', filename)
        return jsonify({'success':True,'filename':filename})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)}), 500

@app.route('/api/files/folder', methods=['POST'])
@login_required
def create_folder_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path','')):
        return jsonify({'success':False}), 403
    os.makedirs(d['path'], exist_ok=True)
    log_activity(session['username'], 'file.mkdir', d['path'])
    return jsonify({'success':True})

@app.route('/api/files/create', methods=['POST'])
@login_required
def create_file_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path','')):
        return jsonify({'success':False}), 403
    with open(d['path'], 'w', encoding='utf-8') as f:
        f.write(d.get('content',''))
    log_activity(session['username'], 'file.create', d['path'])
    return jsonify({'success':True})

@app.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file_api():
    d = request.json or {}
    p = d.get('path','')
    if not is_path_allowed(session['username'], p):
        return jsonify({'success':False}), 403
    if os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p): os.remove(p)
    log_activity(session['username'], 'file.delete', p)
    return jsonify({'success':True})

@app.route('/api/files/content')
@login_required
def get_file_content():
    p = request.args.get('path')
    if not p or not is_path_allowed(session['username'], p):
        return jsonify({'success':False}), 403
    try:
        with open(p,'r',encoding='utf-8',errors='ignore') as f:
            return jsonify({'content':f.read()})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

@app.route('/api/files/save', methods=['POST'])
@login_required
def save_file_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path','')):
        return jsonify({'success':False}), 403
    with open(d['path'],'w',encoding='utf-8') as f:
        f.write(d.get('content',''))
    log_activity(session['username'], 'file.write', d['path'])
    return jsonify({'success':True})

@app.route('/api/files/set-main', methods=['POST'])
@login_required
def set_main_file_api():
    d = request.json or {}
    filename = d.get('filename','')
    username = session['username']
    if not filename:
        return jsonify({'success':False,'error':'No filename'})
    users = load_users()
    if username == MASTER_USERNAME:
        MASTER_CONFIG['main_file'] = filename
        save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
    elif username in users:
        users[username]['main_file'] = filename
        save_users(users)
    log_activity(username, 'file.set-main', filename)
    return jsonify({'success':True,'main_file':filename})

@app.route('/api/files/extract', methods=['POST'])
@login_required
def extract_api():
    d = request.json or {}
    archive = d.get('archive','')
    dest    = d.get('dest','')
    if not archive or not is_path_allowed(session['username'], archive):
        return jsonify({'success':False,'error':'Forbidden or invalid path'}), 403
    if not dest:
        dest = re.sub(r'\.(zip|tar\.gz|tar|gz|rar)$','',archive,flags=re.I)
    result = safe_extract(archive, dest, session['username'])
    return jsonify(result)

# ─── API: Run files ───
@app.route('/api/file/run', methods=['POST'])
@login_required
def run_file_api():
    d = request.json or {}
    filepath = os.path.join(d.get('path',''), d.get('filename',''))
    if not os.path.exists(filepath):
        return jsonify({'success':False,'error':'File not found'})
    if not is_path_allowed(session['username'], d.get('path','')):
        return jsonify({'success':False,'error':'Forbidden'})
    if d.get('filename','').lower().endswith('.zip'):
        extract_dir = os.path.join(d['path'], d['filename'].replace('.zip',''))
        os.makedirs(extract_dir, exist_ok=True)
        main = extract_and_find_main(filepath, extract_dir)
        if main: filepath = main
        else: return jsonify({'success':False,'error':'Main file not found in ZIP'})
    installed = auto_install_dependencies(filepath)
    cmd = get_run_command(filepath)

    # ── Use pty for proper terminal emulation (fixes TERM, input(), readline) ──
    try:
        import pty, fcntl, termios
        master_fd, slave_fd = pty.openpty()
        # set TERM so curses/readline works
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['PYTHONUNBUFFERED'] = '1'
        env['COLUMNS'] = '200'
        env['LINES']   = '40'
        kwargs = dict(
            shell=True, cwd=os.path.dirname(filepath),
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            env=env, close_fds=True
        )
        if hasattr(os,'setsid'): kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(cmd, **kwargs)
        os.close(slave_fd)   # parent doesn't need slave end
        use_pty = True
    except Exception:
        # fallback to pipe mode if pty unavailable
        master_fd = None
        use_pty   = False
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['PYTHONUNBUFFERED'] = '1'
        kwargs = dict(shell=True, cwd=os.path.dirname(filepath),
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        if hasattr(os,'setsid'): kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(cmd, **kwargs)

    pid = f"{session['username']}_{d.get('filename','f')}_{int(time.time())}"
    file_processes[pid] = {
        'process': p, 'filename': d.get('filename',''),
        'username': session['username'], 'output': [],
        'use_pty': use_pty, 'master_fd': master_fd
    }

    def read_pty_output(pid, fd):
        """Read from pty master fd and store lines."""
        import select
        buf = b''
        while True:
            try:
                if fd is None or file_processes.get(pid,{}).get('process') is None:
                    break
                r, _, _ = select.select([fd], [], [], 0.3)
                if r:
                    data = os.read(fd, 4096)
                    if not data:
                        break
                    buf += data
                    # split on newlines, keep partial line in buf
                    lines = buf.split(b'\n')
                    buf = lines[-1]
                    for ln in lines[:-1]:
                        decoded = ln.decode('utf-8', errors='replace').rstrip('\r')
                        # strip ANSI escape codes for clean display
                        clean = re.sub(r'\x1b\[[0-9;]*[mGKHF]|\x1b\[[\d;]*[A-Za-z]', '', decoded)
                        if clean or decoded:
                            file_processes[pid]['output'].append(clean or decoded)
                            if len(file_processes[pid]['output']) > 2000:
                                file_processes[pid]['output'].pop(0)
                else:
                    if file_processes.get(pid,{}).get('process') and \
                       file_processes[pid]['process'].poll() is not None:
                        break
            except (OSError, ValueError):
                break
        try: os.close(fd)
        except Exception: pass

    if use_pty:
        threading.Thread(target=read_pty_output, args=(pid, master_fd), daemon=True).start()
    else:
        threading.Thread(target=read_process_output, args=(pid, p),
                         kwargs={'store': file_processes}, daemon=True).start()

    log_activity(session['username'], 'file.run', f"{d.get('filename','')} ({pid})")
    return jsonify({'success': True, 'process_id': pid, 'installed_result': installed})
    pid = f"{session['username']}_{d.get('filename','f')}_{int(time.time())}"
    file_processes[pid] = {'process':p,'filename':d.get('filename',''),'username':session['username'],'output':[]}
    threading.Thread(target=read_process_output,args=(pid,p),kwargs={'store':file_processes},daemon=True).start()
    log_activity(session['username'],'file.run',f"{d.get('filename','')} ({pid})")
    return jsonify({'success':True,'process_id':pid,'installed_result':installed})

@app.route('/api/file/stop', methods=['POST'])
@login_required
def stop_file_api():
    pid = (request.json or {}).get('process_id')
    if pid in file_processes:
        try:
            if hasattr(os,'killpg'): os.killpg(os.getpgid(file_processes[pid]['process'].pid), signal.SIGKILL)
            else: file_processes[pid]['process'].kill()
        except Exception: pass
        log_activity(session['username'],'file.stop',pid)
        del file_processes[pid]
    return jsonify({'success':True})

@app.route('/api/file/output/<pid>')
@login_required
def get_file_output_api(pid):
    if pid in file_processes:
        info = file_processes[pid]
        out = list(info.get('output',[]))
        info['output'].clear()
        return jsonify({'success':True,'output':out,'is_running':info['process'].poll() is None})
    return jsonify({'success':False,'output':[],'is_running':False})

@app.route('/api/file/output/<pid>/clear', methods=['POST'])
@login_required
def clear_file_output(pid):
    if pid in file_processes:
        file_processes[pid]['output'].clear()
    return jsonify({'success':True})

@app.route('/api/file/input', methods=['POST'])
@login_required
def send_file_input_api():
    d = request.json or {}
    pid  = d.get('process_id')
    text = d.get('input', '')
    if pid in file_processes:
        info = file_processes[pid]
        try:
            if info.get('use_pty') and info.get('master_fd') is not None:
                os.write(info['master_fd'], (text + '\n').encode('utf-8'))
            else:
                info['process'].stdin.write(text + '\n')
                info['process'].stdin.flush()
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': True})

@app.route('/api/file/running')
@login_required
def get_running_files_api():
    user = session['username']
    running, dead = [], []
    for pid, info in file_processes.items():
        if info['username']==user or user==MASTER_USERNAME:
            if info['process'].poll() is None:
                running.append({'process_id':pid,'filename':info['filename'],'username':info['username']})
            else:
                dead.append(pid)
    for d in dead: file_processes.pop(d,None)
    return jsonify({'success':True,'running':running})

# ─── API: Exec ───
@app.route('/api/exec', methods=['POST'])
@login_required
def execute_command_api():
    d = request.json or {}
    cmd = d.get('command','').strip()
    cwd = d.get('cwd', get_user_path(session['username']))
    if not cmd:
        return jsonify({'output':'','success':True})

    # ── Smart command rewriting ──
    # pkg install → try apt-get first, fallback to apt
    if re.match(r'^pkg\s+install\s+', cmd):
        pkg = cmd.split('install',1)[1].strip()
        cmd = f'apt-get install -y {pkg} 2>&1 || apt install -y {pkg} 2>&1'
    # pkg update
    elif re.match(r'^pkg\s+update', cmd):
        cmd = 'apt-get update 2>&1'
    # pkg remove
    elif re.match(r'^pkg\s+remove\s+', cmd):
        pkg = cmd.split('remove',1)[1].strip()
        cmd = f'apt-get remove -y {pkg} 2>&1'
    # normalize python/pip to python3/pip3
    cmd_lower = cmd.lower().strip()
    if re.match(r'^python\s+', cmd):
        cmd = 'python3 ' + cmd[7:]
    elif cmd == 'python':
        cmd = 'python3 --version'
    if re.match(r'^pip\s+', cmd):
        cmd = 'pip3 ' + cmd[4:]
    elif cmd == 'pip':
        cmd = 'pip3 --version'

    # Block dangerous terminal commands
    BLOCKED_CMDS = ['rm -rf /', 'mkfs', ':(){:|:&};:', 'dd if=/dev/zero', 'wget.*|.*bash',
                    'curl.*|.*bash', '> /etc/passwd', 'chmod 777 /']
    for bc in BLOCKED_CMDS:
        if re.search(bc, cmd, re.IGNORECASE):
            log_activity(session['username'], 'security.blocked_cmd', cmd[:100])
            return jsonify({'output':'🚨 أمر محظور لأسباب أمنية', 'success': False})

    # ── Detect if command runs a script that likely needs interactive stdin ──
    def _is_interactive_script(c):
        """Check if command runs a Python/Node/PHP script file."""
        m = re.match(r'^(?:python3?|node|php)\s+(.+?)(?:\s|$)', c.strip())
        if not m: return False, None
        fpath = m.group(1).strip().strip('"\'')
        if not os.path.isabs(fpath):
            fpath = os.path.join(cwd, fpath)
        return os.path.isfile(fpath), fpath

    is_interactive, script_path = _is_interactive_script(cmd)

    log_activity(session['username'], 'exec', cmd[:120])

    # ── Interactive script → launch as pty process ──
    if is_interactive:
        try:
            import pty
            master_fd, slave_fd = pty.openpty()
            env = os.environ.copy()
            env.update({'TERM':'xterm-256color','PYTHONUNBUFFERED':'1',
                        'COLUMNS':'200','LINES':'40'})
            kwargs = dict(shell=True, cwd=cwd,
                          stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
                          env=env, close_fds=True)
            if hasattr(os,'setsid'): kwargs['preexec_fn'] = os.setsid
            p = subprocess.Popen(cmd, **kwargs)
            os.close(slave_fd)
            fname = os.path.basename(script_path) if script_path else 'script'
            pid = f"{session['username']}_{fname}_{int(time.time())}"
            file_processes[pid] = {
                'process':p, 'filename':fname, 'username':session['username'],
                'output':[], 'use_pty':True, 'master_fd':master_fd
            }
            def _read(pid, fd):
                import select
                buf = b''
                while True:
                    try:
                        r2,_,_ = select.select([fd],[],[],0.3)
                        if r2:
                            data = os.read(fd, 4096)
                            if not data: break
                            buf += data
                            lines = buf.split(b'\n')
                            buf = lines[-1]
                            for ln in lines[:-1]:
                                dec = ln.decode('utf-8','replace').rstrip('\r')
                                clean = re.sub(r'\x1b\[[0-9;]*[mGKHF]|\x1b\[[\d;]*[A-Za-z]','',dec)
                                if clean is not None:
                                    file_processes[pid]['output'].append(clean)
                                    if len(file_processes[pid]['output'])>2000:
                                        file_processes[pid]['output'].pop(0)
                        else:
                            if file_processes.get(pid,{}).get('process') and \
                               file_processes[pid]['process'].poll() is not None:
                                break
                    except (OSError,ValueError): break
                try: os.close(fd)
                except Exception: pass
            threading.Thread(target=_read, args=(pid,master_fd), daemon=True).start()
            return jsonify({'success':True, 'interactive':True, 'process_id':pid,
                            'message':f'▶ Started interactive process — use input box to type'})
        except Exception as e:
            pass   # fall through to normal run

    # ── Normal one-shot command ──
    try:
        env = os.environ.copy()
        env.update({'PYTHONUNBUFFERED':'1','TERM':'xterm-256color'})
        r = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True,
            timeout=120, env=env
        )
        output = r.stdout + r.stderr
        if not output.strip():
            output = '✅ Command executed (no output)'
        return jsonify({'output': output, 'success': r.returncode == 0, 'code': r.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'output':'⏱ Timeout (120s) — قد تكون العملية لا تزال تعمل في الخلفية', 'success': False})
    except Exception as e:
        return jsonify({'output': f'❌ Error: {str(e)}', 'success': False})


# ─── API: Hosting (Netlify + Vercel) ────────────────────────────────────────
import urllib.request, urllib.error

HOSTING_DEPLOYMENTS_FILE = os.path.join(BASE_PATH, 'deployments.json')
init_json_file(HOSTING_DEPLOYMENTS_FILE, {'deployments': []})

def load_deployments_db():
    return load_json_file(HOSTING_DEPLOYMENTS_FILE, {'deployments': []})

def save_deployment(platform, name, url, site_id='', deployment_id=''):
    data = load_deployments_db()
    data['deployments'].insert(0, {
        'platform': platform, 'name': name, 'url': url,
        'site_id': site_id, 'deployment_id': deployment_id,
        'username': '',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    data['deployments'] = data['deployments'][:100]
    save_json_file(HOSTING_DEPLOYMENTS_FILE, data)

def _netlify_req(method, path, token, body=None, ctype=None, timeout=60):
    url = 'https://api.netlify.com/api/v1/' + path.lstrip('/')
    headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'panel/1.0'}
    if ctype: headers['Content-Type'] = ctype
    req = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw.decode('utf-8', 'replace')) if raw else {}
    except urllib.error.HTTPError as e:
        msg = (e.read() or b'').decode('utf-8', 'replace')
        raise RuntimeError(f'Netlify {e.code}: {msg[:300]}')

def _vercel_req(method, path, token, body=None, ctype='application/json', timeout=120):
    url = 'https://api.vercel.com/' + path.lstrip('/')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': ctype, 'User-Agent': 'panel/1.0'}
    req = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw.decode('utf-8', 'replace')) if raw else {}
    except urllib.error.HTTPError as e:
        msg = (e.read() or b'').decode('utf-8', 'replace')
        raise RuntimeError(f'Vercel {e.code}: {msg[:300]}')

@app.route('/api/hosting/netlify/test', methods=['POST'])
@login_required
def netlify_test_api():
    token = (request.json or {}).get('token', '').strip()
    if not token: return jsonify({'success': False, 'error': 'No token'})
    try:
        d = _netlify_req('GET', '/user', token, timeout=15)
        return jsonify({'success': True, 'email': d.get('email', '')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/netlify/deploy', methods=['POST'])
@login_required
def netlify_deploy_api():
    d = request.json or {}
    token    = d.get('token', '').strip()
    zip_path = d.get('zip_path', '').strip()
    name     = d.get('name', '').strip()
    if not token or not zip_path:
        return jsonify({'success': False, 'error': 'Token and ZIP path required'})
    if not is_path_allowed(session['username'], os.path.dirname(zip_path)):
        return jsonify({'success': False, 'error': 'Forbidden'})
    if not os.path.exists(zip_path):
        return jsonify({'success': False, 'error': 'ZIP file not found'})
    try:
        # create site
        site_name = re.sub(r'[^a-z0-9-]', '-', (name or f"panel-{int(time.time())}").lower())[:63]
        site = _netlify_req('POST', '/sites',  token,
                            body=json.dumps({'name': site_name}).encode(),
                            ctype='application/json', timeout=30)
        site_id = site.get('id', '')
        # deploy zip
        with open(zip_path, 'rb') as f:
            zip_bytes = f.read()
        dep = _netlify_req('POST', f'/sites/{site_id}/deploys', token,
                           body=zip_bytes, ctype='application/zip', timeout=180)
        # get url
        url = ''
        for k in ('ssl_url', 'url', 'deploy_ssl_url'):
            v = (dep or site or {}).get(k, '')
            if v: url = v; break
        if not url:
            url = site.get('default_domain', '') or f'https://{site_name}.netlify.app'
        save_deployment('netlify', site_name, url, site_id=site_id)
        log_activity(session['username'], 'hosting.netlify.deploy', site_name)
        return jsonify({'success': True, 'url': url, 'site_id': site_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/vercel/test', methods=['POST'])
@login_required
def vercel_test_api():
    token = (request.json or {}).get('token', '').strip()
    if not token: return jsonify({'success': False, 'error': 'No token'})
    try:
        d = _vercel_req('GET', '/v2/user', token, timeout=15)
        user = d.get('user', d)
        return jsonify({'success': True, 'username': user.get('username', user.get('name', 'OK'))})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/vercel/deploy', methods=['POST'])
@login_required
def vercel_deploy_api():
    d = request.json or {}
    token    = d.get('token', '').strip()
    zip_path = d.get('zip_path', '').strip()
    name     = d.get('name', '').strip()
    if not token or not zip_path:
        return jsonify({'success': False, 'error': 'Token and ZIP path required'})
    if not is_path_allowed(session['username'], os.path.dirname(zip_path)):
        return jsonify({'success': False, 'error': 'Forbidden'})
    if not os.path.exists(zip_path):
        return jsonify({'success': False, 'error': 'ZIP file not found'})
    try:
        proj_name = re.sub(r'[^a-z0-9-]', '-', (name or f"panel-{int(time.time())}").lower())[:63]
        # prepare files from zip
        import zipfile as _zf
        import base64 as _b64
        allowed = {'.html', '.css', '.js', '.json', '.txt', '.md', '.svg', '.ico', '.png', '.jpg', '.woff', '.woff2'}
        files = []
        with _zf.ZipFile(zip_path, 'r') as zf:
            names = [n for n in zf.namelist() if not n.endswith('/') and not n.startswith('__MACOSX')]
            # strip top folder if all files share one
            tops = list({n.split('/')[0] for n in names if '/' in n})
            strip = tops[0] + '/' if len(tops) == 1 and all(n.startswith(tops[0]+'/') for n in names if '/') else ''
            for n in names[:50]:
                ext = os.path.splitext(n)[1].lower()
                if ext not in allowed: continue
                data = zf.read(n)
                rel  = n[len(strip):] if strip and n.startswith(strip) else n
                files.append({'file': rel, 'data': _b64.b64encode(data).decode(), 'encoding': 'base64'})
        if not files:
            return jsonify({'success': False, 'error': 'No deployable files in ZIP (HTML/CSS/JS only)'})
        payload = json.dumps({'name': proj_name, 'files': files}).encode()
        dep = _vercel_req('POST', '/v13/deployments', token, body=payload, timeout=180)
        dep_id = dep.get('id', '')
        url = dep.get('url', '') or dep.get('alias', [''])[0] if dep.get('alias') else dep.get('url','')
        if url and not url.startswith('http'): url = 'https://' + url
        if not url: url = f'https://{proj_name}.vercel.app'
        save_deployment('vercel', proj_name, url, deployment_id=dep_id)
        log_activity(session['username'], 'hosting.vercel.deploy', proj_name)
        return jsonify({'success': True, 'url': url, 'deployment_id': dep_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/hosting/deployments')
@login_required
def list_deployments_api():
    data = load_deployments_db()
    return jsonify(data)



# ─── API: Security Alerts ───
@app.route('/api/security/alerts')
@master_required
def get_security_alerts_api():
    data = load_security_alerts()
    return jsonify(data)

@app.route('/api/security/alerts/review', methods=['POST'])
@master_required
def review_security_alert_api():
    alert_id = (request.json or {}).get('id','')
    data = load_security_alerts()
    for a in data.get('alerts',[]):
        if a.get('id') == alert_id:
            a['reviewed'] = True
            break
    save_json_file(SECURITY_ALERTS_FILE, data)
    log_activity(session['username'], 'security.alert.reviewed', alert_id)
    return jsonify({'success': True})

@app.route('/api/security/alerts/delete', methods=['POST'])
@master_required
def delete_security_alert_api():
    alert_id = (request.json or {}).get('id','')
    data = load_security_alerts()
    data['alerts'] = [a for a in data.get('alerts',[]) if a.get('id') != alert_id]
    save_json_file(SECURITY_ALERTS_FILE, data)
    return jsonify({'success': True})

@app.route('/api/security/alerts/clear', methods=['POST'])
@master_required
def clear_security_alerts_api():
    save_json_file(SECURITY_ALERTS_FILE, {'alerts': []})
    log_activity(session['username'], 'security.alerts.cleared', '')
    return jsonify({'success': True})

# ─── Static / Web hosting ───
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(BASE_PATH, filename)

@app.route('/web/<username>/')
@app.route('/web/<username>/<path:filename>')
def serve_user_web(username, filename='index.html'):
    user_path = get_user_path(username)
    return send_from_directory(user_path, filename)

@app.route('/api-service/<username>/')
@app.route('/api-service/<username>/<path:filename>')
def serve_user_api_files(username, filename='api.json'):
    user_path = get_user_path(username)
    return send_from_directory(user_path, filename)

# ─── Admin legacy routes ───
@app.route('/admin/users')
def admin_manage_users():
    if not session.get('logged_in') or session.get('username') != MASTER_USERNAME:
        return redirect('/login')
    return redirect('/')

@app.route('/admin/approve/<username>')
def approve_user_legacy(username):
    if not session.get('logged_in') or session.get('username') != MASTER_USERNAME:
        return "Unauthorized", 403
    users = load_users()
    if username in users:
        users[username]['active'] = True
        save_users(users)
        log_activity(MASTER_USERNAME,'user.approve.legacy',username)
        return f'<div style="font-family:sans-serif;text-align:center;margin-top:50px;background:#0b0f17;color:#e6edf3;min-height:100vh;padding:40px"><h3 style="color:#3fb950">✅ Account activated: {html.escape(username)}</h3><a href="/" style="color:#7c5cfc">← Back to panel</a></div>'
    return "User not found"

# ─────────────────────────────────────────────────────────────────────────────
#  21.  Multi-Port Sub-servers
# ─────────────────────────────────────────────────────────────────────────────
def run_extra_port(port, note=''):
    try:
        from flask import Flask as _F
        sub = _F(f'sub_{port}')
        @sub.route('/')
        def _h():
            return f'<div style="font-family:sans-serif;background:#0b0f17;color:#e6edf3;min-height:100vh;display:flex;align-items:center;justify-content:center"><div style="text-align:center"><h1 style="background:linear-gradient(135deg,#7c5cfc,#00bfff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:36px">🚀 SERVER HUB</h1><p style="color:#8b949e;margin-top:8px">Port {port}</p>{(f"<p style=\'color:#484f58\'>{html.escape(note)}</p>") if note else ""}<p style="margin-top:20px"><a style="color:#7c5cfc;text-decoration:none" href="/">Open Panel</a></p></div></div>'
        sub.run(host='0.0.0.0',port=port,debug=False,threaded=True,use_reloader=False)
    except Exception as e:
        print(f'[port {port}] failed: {e}')

def start_configured_extra_ports():
    for p in load_ports():
        try:
            threading.Thread(target=run_extra_port,args=(int(p['port']),p.get('note','')),daemon=True).start()
        except Exception: pass

# ─────────────────────────────────────────────────────────────────────────────
#  22.  Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    G='[32m'; P='[35m'; C='[36m'; Y='[33m'; B='[1m'; R='[0m'
    print(G+r'''
 _____ _     __  __  ___  ____  __  __ _____ _   _
| ____| |   |  \/  |/ _ \|  _ \|  \/  | ____| \ | |
|  _| | |   | |\/| | | | | | | | |\/| |  _| |  \| |
| |___| |___| |  | | |_| | |_| | |  | | |___| |\  |
|_____|_____|_|  |_|\___/|____/|_|  |_|_____|_| \_|'''+R)
    print(P+'\u2554'+'\u2550'*64+'\u2557'+R)
    print(P+'\u2551  \U0001f680  '+B+C+'\U0001d834\U0001d835\U0001d836\U0001d837\U0001d838\U0001d839\U0001d83a\U0001d83b'+R+P+'  \u2015  SERVER HUB v2.0  \u2015  @Y0YY12      \u2551'+R)
    print(P+'\u255a'+'\u2550'*64+'\u255d'+R)
    print(G+'\u250c\u2500\u2500('+P+B+'\U0001d834\U0001d835\U0001d836\U0001d837\U0001d838\U0001d839\U0001d83a\U0001d83b'+R+G+'\u1F19A'+C+'server-hub'+G+')-['+Y+'~'+G+']'+R)
    print(G+'\u2514\u2500'+P+'$'+R+f' Master   : '+B+C+'{MASTER_USERNAME}'+R)
    print(G+'\u2514\u2500'+P+'$'+R+f' Data dir : '+Y+'{BASE_PATH}'+R)

    start_configured_extra_ports()

    port = int(os.environ.get('PORT', MASTER_CONFIG.get('port') or 3178))
    print(f"   🌐 Panel  : http://0.0.0.0:{port}")
    print(f"   🔑 Login  : {MASTER_USERNAME} / Hasnen1@@1 (default)")
    print(f"   📝 Register tab available for new users (requires admin approval)")
    print(f"   ⚡ PHP / Node.js / Python / ZIP all supported")
    print()
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
