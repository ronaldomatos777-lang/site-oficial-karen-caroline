from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session, Response, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo
import sqlite3, json, os, csv, io, html, re, secrets, threading, time, logging

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
USE_POSTGRES = bool(DATABASE_URL)
APP_ENV = os.environ.get('APP_ENV', 'development').strip().lower()
IS_PRODUCTION = APP_ENV == 'production'
SECRET_KEY = os.environ.get('SECRET_KEY', '').strip()
ADMIN_USER = os.environ.get('ADMIN_USER', '').strip()
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '5519974078273').strip()

if IS_PRODUCTION:
    config_errors = []
    if len(SECRET_KEY) < 32:
        config_errors.append('SECRET_KEY deve ter pelo menos 32 caracteres')
    if not ADMIN_USER:
        config_errors.append('ADMIN_USER deve ser definido')
    if len(ADMIN_PASSWORD) < 12:
        config_errors.append('ADMIN_PASSWORD deve ter pelo menos 12 caracteres')
    if not DATABASE_URL:
        config_errors.append('DATABASE_URL deve apontar para o PostgreSQL')
    whatsapp_digits = re.sub(r'\D', '', WHATSAPP_NUMBER)
    if len(whatsapp_digits) not in (12, 13) or not whatsapp_digits.startswith('55'):
        config_errors.append('WHATSAPP_NUMBER deve estar no formato internacional brasileiro')
    if config_errors:
        raise RuntimeError('Configuração de produção inválida: ' + '; '.join(config_errors))
else:
    SECRET_KEY = SECRET_KEY or secrets.token_hex(32)
    ADMIN_USER = ADMIN_USER or 'admin'

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE / 'data'))
DB_PATH = Path(os.environ.get('DB_PATH', DATA_DIR / 'leads.db'))
if not USE_POSTGRES:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=IS_PRODUCTION or os.environ.get('COOKIE_SECURE', '0') == '1',
    SESSION_COOKIE_NAME='karen_admin_session',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

default_origins = (
    'https://www.karencarolineimoveis.com.br,https://karencarolineimoveis.com.br'
    if IS_PRODUCTION else
    'https://www.karencarolineimoveis.com.br,https://karencarolineimoveis.com.br,http://127.0.0.1:5000,http://localhost:5000,null'
)
ALLOWED_ORIGINS = {
    origin.strip().rstrip('/')
    for origin in os.environ.get('ALLOWED_ORIGINS', default_origins).split(',')
    if origin.strip()
}
STATUS_OPTIONS = ['Novo', 'Em contato', 'Visita agendada', 'Proposta', 'Venda', 'Sem interesse']
RATE = {}
RATE_LOCK = threading.Lock()
RATE_LAST_CLEANUP = 0.0
RATE_CLEANUP_INTERVAL = 60
RATE_MAX_WINDOW = 300
RATE_MAX_KEYS = 10000
PUBLIC_PAGES = {
    'index.html',
    'alta-vista.html',
    'casa-prado.html',
    'cores-da-mata.html',
    'parque-alto.html',
    'privacidade.html',
    'seleto-amoreiras.html',
    'universo-parque-alphaville.html',
}
PUBLIC_ROOT_ASSETS = {
    'style.css',
    'script.js',
    'social-links.js',
    'sitemap.xml',
    'karen-caroline-logo-oficial.png',
}
PUBLIC_ASSET_EXTENSIONS = {'.ico', '.png', '.webp'}
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')
IDEMPOTENCY_RE = re.compile(r'^[A-Za-z0-9._:-]{16,100}$')


class DBConnection:
    def __init__(self):
        if USE_POSTGRES:
            self.con = psycopg.connect(
                DATABASE_URL,
                row_factory=dict_row,
                connect_timeout=10,
            )
        else:
            self.con = sqlite3.connect(DB_PATH, timeout=15)
            self.con.row_factory = sqlite3.Row
            self.con.execute('PRAGMA journal_mode=WAL')
            self.con.execute('PRAGMA busy_timeout=15000')

    def execute(self, sql, params=()):
        if USE_POSTGRES:
            sql = sql.replace('?', '%s')
        return self.con.execute(sql, params)

    def commit(self):
        self.con.commit()

    def rollback(self):
        self.con.rollback()

    def close(self):
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.rollback()
            else:
                self.commit()
        finally:
            self.close()
        return False


def db():
    return DBConnection()


def table_columns(con, table):
    if USE_POSTGRES:
        rows = con.execute(
            '''SELECT column_name FROM information_schema.columns
               WHERE table_schema = current_schema() AND table_name = ?''',
            (table,),
        ).fetchall()
        return {row['column_name'] for row in rows}
    return {row['name'] for row in con.execute(f'PRAGMA table_info({table})').fetchall()}


def ensure_column(con, table, column, definition):
    if USE_POSTGRES:
        con.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}')
        return
    if column not in table_columns(con, table):
        con.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')


def init_db():
    id_column = 'BIGSERIAL PRIMARY KEY' if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'
    with db() as con:
        con.execute(f'''CREATE TABLE IF NOT EXISTS leads (
            id {id_column},
            nome TEXT NOT NULL,
            sobrenome TEXT,
            whatsapp TEXT NOT NULL,
            email TEXT,
            empreendimento TEXT NOT NULL,
            origem TEXT,
            interesse TEXT,
            consentimento INTEGER NOT NULL DEFAULT 0,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            criado_em TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Novo',
            observacoes TEXT DEFAULT '',
            atualizado_em TEXT DEFAULT '',
            pagina_url TEXT DEFAULT '',
            pagina_titulo TEXT DEFAULT '',
            referrer TEXT DEFAULT '',
            utm_content TEXT DEFAULT '',
            utm_term TEXT DEFAULT '',
            idempotency_key TEXT
        )''')
        con.execute(f'''CREATE TABLE IF NOT EXISTS interactions (
            id {id_column},
            tipo TEXT NOT NULL,
            empreendimento TEXT,
            origem TEXT,
            pagina_url TEXT,
            pagina_titulo TEXT,
            referrer TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            lead_id {'BIGINT' if USE_POSTGRES else 'INTEGER'},
            interesse TEXT,
            criado_em TEXT NOT NULL
        )''')
        ensure_column(con, 'leads', 'idempotency_key', 'TEXT')
        ensure_column(con, 'interactions', 'lead_id', 'BIGINT' if USE_POSTGRES else 'INTEGER')
        ensure_column(con, 'interactions', 'interesse', 'TEXT')
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_idempotency_key ON leads (idempotency_key)')


def esc(v):
    return html.escape(str(v or ''))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def valid_whatsapp(value):
    digits = re.sub(r'\D', '', value or '')
    if len(digits) in (10, 11):
        return True
    return len(digits) in (12, 13) and digits.startswith('55')


def valid_email(value):
    return not value or bool(EMAIL_RE.fullmatch(value))


def valid_visit_date(value):
    if not value:
        return True
    try:
        selected = date.fromisoformat(value)
    except ValueError:
        return False
    return selected >= datetime.now(ZoneInfo('America/Sao_Paulo')).date()


def csv_safe(value):
    text = str(value or '')
    if text.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + text
    return text


def client_ip():
    return (request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or request.remote_addr or 'unknown')


def limited(key, limit, window=60):
    global RATE_LAST_CLEANUP
    now = time.time()
    with RATE_LOCK:
        if now - RATE_LAST_CLEANUP >= RATE_CLEANUP_INTERVAL:
            stale_before = now - RATE_MAX_WINDOW
            for stored_key, stored_bucket in list(RATE.items()):
                stored_bucket[:] = [stamp for stamp in stored_bucket if stamp >= stale_before]
                if not stored_bucket:
                    RATE.pop(stored_key, None)
            RATE_LAST_CLEANUP = now
        if key not in RATE and len(RATE) >= RATE_MAX_KEYS:
            oldest_key = min(RATE, key=lambda item: RATE[item][-1] if RATE[item] else 0)
            RATE.pop(oldest_key, None)
        bucket = RATE.setdefault(key, [])
        bucket[:] = [stamp for stamp in bucket if now - stamp < window]
        if len(bucket) >= limit:
            return True
        bucket.append(now)
        return False


def admin_required():
    return session.get('admin') is True and session.get('admin_user') == ADMIN_USER


def csrf_token():
    token = session.get('_csrf')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf'] = token
    return token


def csrf_field():
    return f'<input type="hidden" name="csrf_token" value="{esc(csrf_token())}">'


def verify_csrf():
    sent = request.form.get('csrf_token', '')
    saved = session.get('_csrf', '')
    return bool(sent and saved and secrets.compare_digest(sent, saved))


def whatsapp_link(number, name='', empreendimento=''):
    digits = re.sub(r'\D', '', number or '')
    if not digits:
        return '#'
    if len(digits) in (10, 11):
        digits = '55' + digits
    msg = f"Olá {name.strip()}, tudo bem? Vi seu interesse no {empreendimento}. Posso te passar mais informações?"
    return f"https://wa.me/{digits}?text={quote(msg)}"


def admin_css():
    return '''
    :root{--green:#344b3c;--cream:#f7f4ef;--paper:#fff;--gold:#c49a57;--line:#ddd6ca;--ink:#252521;--muted:#756f67}
    *{box-sizing:border-box}body{font-family:Arial,sans-serif;margin:0;background:var(--cream);color:var(--ink)}a{color:inherit}
    .top{padding:20px 4vw;background:var(--green);color:#fff;display:flex;justify-content:space-between;align-items:center;gap:20px;position:sticky;top:0;z-index:10}.top a{color:#fff;margin-left:14px;text-decoration:none}.top small{opacity:.8}.wrap{padding:28px 4vw}.cards{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin-bottom:22px}.card{background:#fff;padding:18px;border:1px solid var(--line)}.card b{display:block;font-size:26px;margin-top:6px}.card span{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
    .filters{background:#fff;border:1px solid var(--line);padding:14px;display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:10px;margin-bottom:16px}.filters input,.filters select,.filters button{padding:11px;border:1px solid var(--line);background:#fff}.filters button{background:var(--green);color:#fff;border-color:var(--green);font-weight:700;cursor:pointer}
    table{border-collapse:collapse;width:100%;background:#fff;min-width:1150px}th,td{padding:12px;border-bottom:1px solid #e6e0d8;text-align:left;font-size:13px;vertical-align:middle}th{background:#eee8df;position:sticky;top:0;z-index:2}.table-wrap{overflow:auto;border:1px solid var(--line)}.muted{color:var(--muted)}.wa{display:inline-block;padding:8px 10px;background:#1f8f4b;color:#fff;text-decoration:none;border-radius:4px;font-weight:700}.detail{display:inline-block;margin-left:6px;padding:8px 10px;background:#eee8df;text-decoration:none;border-radius:4px}.status-form select{padding:7px;border:1px solid var(--line);background:#fff}.empty{padding:35px;text-align:center;color:var(--muted)}
    .login{font-family:Arial;background:#f4efe7;display:grid;place-items:center;min-height:100vh;margin:0;color:#252521}.box{background:#fff;padding:40px;width:min(420px,90vw);box-shadow:0 20px 60px #0002}.box h1{margin-top:0}.box input,.box button{width:100%;padding:14px;margin-top:12px;box-sizing:border-box}.box button{background:var(--green);color:#fff;border:0;font-weight:700;cursor:pointer}.err{color:#a22}
    .insights{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 18px}.insights .panel{padding:18px}.insights h2{font-size:16px;margin:0 0 12px}.rank{display:flex;justify-content:space-between;gap:20px;padding:8px 0;border-bottom:1px solid #eee8df;font-size:13px}.rank:last-child{border:0}.lead-detail{max-width:1000px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{background:#fff;border:1px solid var(--line);padding:24px}.panel h2{margin-top:0}.data-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.data-item span{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px}.data-item b{font-size:15px}.edit-form textarea,.edit-form select{width:100%;padding:12px;border:1px solid var(--line);font:14px Arial;box-sizing:border-box}.edit-form textarea{min-height:180px;resize:vertical}.edit-form button{margin-top:12px;padding:12px 18px;border:0;background:var(--green);color:#fff;font-weight:700;cursor:pointer}.back{display:inline-block;margin-bottom:14px;text-decoration:none}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}.actions a{padding:10px 13px;text-decoration:none;border-radius:4px;background:#eee8df}.actions a.primary{background:#1f8f4b;color:#fff}
    @media(max-width:1050px){.insights{grid-template-columns:1fr}.cards{grid-template-columns:repeat(3,1fr)}.filters{grid-template-columns:1fr 1fr}.lead-detail{grid-template-columns:1fr}}
    @media(max-width:620px){.cards{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.data-grid{grid-template-columns:1fr}}
    '''


def layout(title, body):
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{esc(title)}</title><style>{admin_css()}</style></head><body>{body}</body></html>'''


def admin_header(subtitle=''):
    return f'''<div class="top"><div><b>CRM Karen Caroline Imóveis</b><div><small>{esc(subtitle)}</small></div></div><div><a href="/admin/leads">Leads</a><a href="/admin/exportar.csv">Exportar CSV</a><a href="/admin/sair">Sair</a></div></div>'''


@app.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
    resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    resp.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.is_secure:
        resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    if request.path.startswith('/admin'):
        resp.headers['Cache-Control'] = 'no-store'
    elif request.path.startswith('/assets/') or request.path.endswith(('.css','.js','.webp','.png','.svg','.woff2')):
        resp.headers['Cache-Control'] = 'public, max-age=604800'
    if request.path.startswith('/api/'):
        origin = request.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            resp.headers['Access-Control-Allow-Origin'] = origin
            resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp


@app.get('/health')
def health():
    try:
        with db() as con:
            con.execute('SELECT 1').fetchone()
    except Exception:
        app.logger.error('Falha na verificação de saúde do banco de dados.')
        return {'ok': False}, 503
    return {'ok': True}


@app.get('/api/config')
def public_config():
    return jsonify(whatsapp_number=re.sub(r'\D', '', WHATSAPP_NUMBER))


@app.get('/whatsapp')
def public_whatsapp():
    digits = re.sub(r'\D', '', WHATSAPP_NUMBER)
    if not digits:
        abort(503)
    message = request.args.get('text', '').strip()[:2000]
    suffix = f'?text={quote(message)}' if message else ''
    return redirect(f'https://wa.me/{digits}{suffix}')


@app.post('/api/events')
def events():
    if limited(f'events:{client_ip()}', 120, 60):
        return jsonify(ok=False, error='Muitas requisições.'), 429
    data = request.get_json(silent=True) or {}
    tipo = str(data.get('tipo','')).strip()[:80]
    if not tipo:
        return jsonify(ok=False), 400
    try:
        lead_id = int(data['lead_id']) if data.get('lead_id') not in (None, '') else None
    except (TypeError, ValueError):
        lead_id = None
    with db() as con:
        con.execute('''INSERT INTO interactions (tipo,empreendimento,origem,pagina_url,pagina_titulo,referrer,utm_source,utm_medium,utm_campaign,lead_id,interesse,criado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
            tipo, str(data.get('empreendimento','')).strip()[:160], str(data.get('origem','')).strip()[:160], str(data.get('pagina_url','')).strip()[:1000], str(data.get('pagina_titulo','')).strip()[:300], str(data.get('referrer','')).strip()[:1000], str(data.get('utm_source','')).strip()[:160], str(data.get('utm_medium','')).strip()[:160], str(data.get('utm_campaign','')).strip()[:300], lead_id, str(data.get('interesse','')).strip()[:300], now_iso()))
        con.commit()
    return jsonify(ok=True)


@app.post('/api/leads')
def leads_api():
    if limited(f'leads:{client_ip()}', 12, 300):
        return jsonify(ok=False, error='Muitas tentativas. Aguarde alguns minutos.'), 429
    data = request.get_json(silent=True) or {}
    if str(data.get('website','')).strip():
        return jsonify(ok=True, message='Cadastro recebido.'), 200
    nome = str(data.get('nome','')).strip()[:120]
    sobrenome = str(data.get('sobrenome','')).strip()[:120]
    whatsapp = str(data.get('whatsapp','')).strip()[:40]
    email_ = str(data.get('email','')).strip()[:254]
    empreendimento = str(data.get('empreendimento','Site geral')).strip()[:180]
    consent = str(data.get('consentimento','')).lower() in {'1','true','on','sim','yes'}
    if not nome or not whatsapp or not consent:
        return jsonify(ok=False, error='Preencha nome, WhatsApp e aceite o consentimento para contato.'), 400
    if not valid_whatsapp(whatsapp):
        return jsonify(ok=False, error='Informe um WhatsApp válido com DDD.'), 400
    if not valid_email(email_):
        return jsonify(ok=False, error='Informe um e-mail válido.'), 400
    visit_date = str(data.get('data_visita','')).strip()
    if not valid_visit_date(visit_date):
        return jsonify(ok=False, error='Escolha uma data de visita válida, a partir de hoje.'), 400
    idempotency_key = str(data.get('idempotency_key','')).strip()
    if not idempotency_key:
        idempotency_key = secrets.token_urlsafe(24)
    elif not IDEMPOTENCY_RE.fullmatch(idempotency_key):
        return jsonify(ok=False, error='Identificador da solicitação inválido.'), 400
    origem = str(data.get('origem','site')).strip()[:160]
    interesse = str(data.get('interesse','')).strip()[:300]
    now = now_iso()
    with db() as con:
        insert_sql = '''INSERT INTO leads (nome,sobrenome,whatsapp,email,empreendimento,origem,interesse,consentimento,utm_source,utm_medium,utm_campaign,criado_em,status,atualizado_em,pagina_url,pagina_titulo,referrer,utm_content,utm_term,idempotency_key) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT (idempotency_key) DO NOTHING'''
        cur = con.execute(insert_sql, (
            nome,sobrenome,whatsapp,email_,empreendimento,origem,interesse,1,str(data.get('utm_source','')).strip()[:160],str(data.get('utm_medium','')).strip()[:160],str(data.get('utm_campaign','')).strip()[:300],now,'Novo',now,str(data.get('pagina_url','')).strip()[:1000],str(data.get('pagina_titulo','')).strip()[:300],str(data.get('referrer','')).strip()[:1000],str(data.get('utm_content','')).strip()[:300],str(data.get('utm_term','')).strip()[:300],idempotency_key))
        duplicate = cur.rowcount == 0
        lead_row = con.execute('SELECT id FROM leads WHERE idempotency_key=?', (idempotency_key,)).fetchone()
        lead_id = lead_row['id']
    resp = {'ok': True, 'lead_id': lead_id, 'duplicate': duplicate, 'message': 'Cadastro realizado com sucesso.'}
    return jsonify(resp)


@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'GET':
        if admin_required():
            return redirect('/admin/leads')
        body = f'''<div class="login"><form class="box" method="post" action="/admin">{csrf_field()}<h1>CRM Imobiliário</h1><p>Entre com suas credenciais administrativas.</p><input name="usuario" placeholder="Usuário" required autocomplete="username"><input type="password" name="senha" placeholder="Senha" required autocomplete="current-password"><button>Entrar</button></form></div>'''
        return layout('CRM Imobiliário', body)
    if limited(f'login:{client_ip()}', 8, 300):
        return layout('CRM Imobiliário', '<div class="login"><div class="box"><h1>Acesso temporariamente bloqueado</h1><p>Aguarde alguns minutos e tente novamente.</p></div></div>'), 429
    if not verify_csrf():
        return layout('CRM Imobiliário', '<div class="login"><div class="box"><h1>Sessão expirada</h1><p>Atualize a página e tente novamente.</p></div></div>'), 400
    if not ADMIN_PASSWORD:
        return layout('Configuração necessária', '<div class="login"><div class="box"><h1>Configuração necessária</h1><p>Defina a variável ADMIN_PASSWORD no servidor antes de usar o CRM.</p></div></div>'), 503
    usuario = request.form.get('usuario','')
    senha = request.form.get('senha','')
    valid_user = secrets.compare_digest(usuario, ADMIN_USER)
    valid_password = secrets.compare_digest(senha, ADMIN_PASSWORD)
    if valid_user and valid_password:
        session.clear(); session['admin'] = True; session['admin_user'] = ADMIN_USER; session.permanent = True
        return redirect('/admin/leads')
    body = f'''<div class="login"><form class="box" method="post" action="/admin">{csrf_field()}<h1>CRM Imobiliário</h1><p class="err">Usuário ou senha incorretos.</p><input name="usuario" placeholder="Usuário" required autocomplete="username"><input type="password" name="senha" placeholder="Senha" required autocomplete="current-password"><button>Entrar</button></form></div>'''
    return layout('CRM Imobiliário', body), 401


@app.get('/admin/leads')
def admin_leads():
    if not admin_required(): return redirect('/admin')
    q = request.args.get('q','').strip(); status = request.args.get('status','').strip(); emp = request.args.get('empreendimento','').strip()
    where, params = [], []
    if q:
        where.append('(nome LIKE ? OR sobrenome LIKE ? OR whatsapp LIKE ? OR email LIKE ?)'); like=f'%{q}%'; params += [like,like,like,like]
    if status: where.append('status=?'); params.append(status)
    if emp: where.append('empreendimento=?'); params.append(emp)
    sql = 'SELECT * FROM leads' + (' WHERE ' + ' AND '.join(where) if where else '') + ' ORDER BY id DESC'
    with db() as con:
        leads = con.execute(sql, params).fetchall()
        totals = {r['status']: r['n'] for r in con.execute('SELECT status, COUNT(*) n FROM leads GROUP BY status').fetchall()}
        total_all = con.execute('SELECT COUNT(*) n FROM leads').fetchone()['n']
        whatsapp_clicks = con.execute("SELECT COUNT(*) n FROM interactions WHERE tipo='whatsapp_click'").fetchone()['n']
        empreendimentos = [r['empreendimento'] for r in con.execute('SELECT DISTINCT empreendimento FROM leads ORDER BY empreendimento').fetchall()]
        by_project = con.execute('SELECT empreendimento, COUNT(*) n FROM leads GROUP BY empreendimento ORDER BY n DESC LIMIT 8').fetchall()
        by_source = con.execute("SELECT COALESCE(NULLIF(utm_source,''), NULLIF(origem,''), 'Direto') fonte, COUNT(*) n FROM leads GROUP BY fonte ORDER BY n DESC LIMIT 8").fetchall()
    cards = ''.join(f'<div class="card"><span>{esc(label)}</span><b>{totals.get(label,0)}</b></div>' for label in ['Novo','Em contato','Visita agendada','Proposta','Venda'])
    cards += f'<div class="card"><span>Total</span><b>{total_all}</b></div><div class="card"><span>Cliques WhatsApp</span><b>{whatsapp_clicks}</b></div>'
    status_opts='<option value="">Todos os status</option>'+''.join(f'<option value="{esc(s)}" {"selected" if s==status else ""}>{esc(s)}</option>' for s in STATUS_OPTIONS)
    emp_opts='<option value="">Todos os empreendimentos</option>'+''.join(f'<option value="{esc(e)}" {"selected" if e==emp else ""}>{esc(e)}</option>' for e in empreendimentos)
    rows=[]
    for r in leads:
        name=f"{r['nome']} {r['sobrenome'] or ''}".strip(); opts=''.join(f'<option value="{esc(s)}" {"selected" if s==r["status"] else ""}>{esc(s)}</option>' for s in STATUS_OPTIONS); wa=whatsapp_link(r['whatsapp'],name,r['empreendimento'])
        rows.append(f'''<tr><td>{r['id']}</td><td><b>{esc(name)}</b><br><span class="muted">{esc(r['email'] or '-')}</span></td><td>{esc(r['whatsapp'])}</td><td>{esc(r['empreendimento'])}<br><span class="muted">{esc(r['interesse'] or '')}</span></td><td>{esc(r['origem'] or '-')}</td><td class="muted">{esc((r['criado_em'] or '')[:16].replace('T',' '))}</td><td><form class="status-form" method="post" action="/admin/lead/status">{csrf_field()}<input type="hidden" name="id" value="{r['id']}"><select name="status" onchange="this.form.submit()">{opts}</select></form></td><td><a class="wa" target="_blank" rel="noopener" href="{esc(wa)}">WhatsApp</a><a class="detail" href="/admin/lead?id={r['id']}">Detalhes</a></td></tr>''')
    rows_html=''.join(rows) if rows else '<tr><td colspan="8" class="empty">Nenhum lead encontrado.</td></tr>'
    filters=f'''<form class="filters" method="get" action="/admin/leads"><input name="q" value="{esc(q)}" placeholder="Buscar nome, WhatsApp ou e-mail"><select name="status">{status_opts}</select><select name="empreendimento">{emp_opts}</select><button>Filtrar</button></form>'''
    insights = '<div class="insights"><div class="panel"><h2>Leads por empreendimento</h2>' + ''.join(f'<div class="rank"><span>{esc(r["empreendimento"])}</span><b>{r["n"]}</b></div>' for r in by_project) + '</div><div class="panel"><h2>Origem dos leads</h2>' + ''.join(f'<div class="rank"><span>{esc(r["fonte"])}</span><b>{r["n"]}</b></div>' for r in by_source) + '</div></div>'
    body=admin_header(f'{len(leads)} lead(s) exibido(s)')+f'''<div class="wrap"><div class="cards">{cards}</div>{insights}{filters}<div class="table-wrap"><table><thead><tr><th>ID</th><th>Cliente</th><th>WhatsApp</th><th>Empreendimento</th><th>Origem</th><th>Entrada UTC</th><th>Etapa</th><th>Ações</th></tr></thead><tbody>{rows_html}</tbody></table></div></div>'''
    return layout('CRM - Leads',body)


@app.get('/admin/lead')
def admin_lead():
    if not admin_required(): return redirect('/admin')
    try: lead_id=int(request.args.get('id','0'))
    except ValueError: lead_id=0
    with db() as con: r=con.execute('SELECT * FROM leads WHERE id=?',(lead_id,)).fetchone()
    if not r: abort(404)
    name=f"{r['nome']} {r['sobrenome'] or ''}".strip(); wa=whatsapp_link(r['whatsapp'],name,r['empreendimento']); opts=''.join(f'<option value="{esc(s)}" {"selected" if s==r["status"] else ""}>{esc(s)}</option>' for s in STATUS_OPTIONS)
    body=admin_header(f'Lead #{r["id"]}')+f'''<div class="wrap"><a class="back" href="/admin/leads">← Voltar para leads</a><div class="lead-detail"><section class="panel"><h2>{esc(name)}</h2><div class="data-grid"><div class="data-item"><span>WhatsApp</span><b>{esc(r['whatsapp'])}</b></div><div class="data-item"><span>E-mail</span><b>{esc(r['email'] or '-')}</b></div><div class="data-item"><span>Empreendimento</span><b>{esc(r['empreendimento'])}</b></div><div class="data-item"><span>Interesse</span><b>{esc(r['interesse'] or '-')}</b></div><div class="data-item"><span>Origem</span><b>{esc(r['origem'] or '-')}</b></div><div class="data-item"><span>Cadastro</span><b>{esc((r['criado_em'] or '')[:19].replace('T',' '))}</b></div><div class="data-item"><span>UTM source</span><b>{esc(r['utm_source'] or '-')}</b></div><div class="data-item"><span>UTM campaign</span><b>{esc(r['utm_campaign'] or '-')}</b></div><div class="data-item"><span>UTM medium</span><b>{esc(r['utm_medium'] or '-')}</b></div><div class="data-item"><span>Página</span><b>{esc(r['pagina_titulo'] or '-')}</b></div><div class="data-item"><span>URL</span><b style="word-break:break-all">{esc(r['pagina_url'] or '-')}</b></div><div class="data-item"><span>Referência</span><b style="word-break:break-all">{esc(r['referrer'] or '-')}</b></div></div><div class="actions"><a class="primary" target="_blank" rel="noopener" href="{esc(wa)}">Abrir WhatsApp</a>{f'<a href="mailto:{esc(r["email"])}">Enviar e-mail</a>' if r['email'] else ''}</div></section><section class="panel"><h2>Andamento comercial</h2><form class="edit-form" method="post" action="/admin/lead/update">{csrf_field()}<input type="hidden" name="id" value="{r['id']}"><label>Etapa do funil</label><select name="status">{opts}</select><p><label>Observações</label></p><textarea name="observacoes">{esc(r['observacoes'] or '')}</textarea><button>Salvar alterações</button></form><p class="muted">Última atualização: {esc((r['atualizado_em'] or '-').replace('T',' ')[:19])}</p></section></div></div>'''
    return layout(f'Lead {name}',body)


@app.post('/admin/lead/status')
@app.post('/admin/lead/update')
def admin_update():
    if not admin_required(): return redirect('/admin')
    if not verify_csrf(): abort(400)
    try: lead_id=int(request.form.get('id','0'))
    except ValueError: lead_id=0
    status=request.form.get('status','Novo')
    if status not in STATUS_OPTIONS: status='Novo'
    now=now_iso()
    with db() as con:
        if request.path.endswith('/update'):
            con.execute('UPDATE leads SET status=?, observacoes=?, atualizado_em=? WHERE id=?',(status,request.form.get('observacoes','').strip()[:5000],now,lead_id))
        else:
            con.execute('UPDATE leads SET status=?, atualizado_em=? WHERE id=?',(status,now,lead_id))
        con.commit()
    return redirect(f'/admin/lead?id={lead_id}' if request.path.endswith('/update') else '/admin/leads')


@app.get('/admin/exportar.csv')
def export_csv():
    if not admin_required(): return redirect('/admin')
    with db() as con: rows=con.execute('SELECT * FROM leads ORDER BY id DESC').fetchall()
    fields=['id','nome','sobrenome','whatsapp','email','empreendimento','origem','interesse','criado_em','status','observacoes','atualizado_em','utm_source','utm_medium','utm_campaign','utm_content','utm_term','pagina_url','pagina_titulo','referrer']
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=fields); w.writeheader()
    for r in rows: w.writerow({f:csv_safe(r[f]) for f in fields})
    raw=out.getvalue().encode('utf-8-sig')
    return Response(raw,mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=leads-crm.csv'})


@app.get('/admin/sair')
def logout():
    session.clear(); return redirect('/admin')
# ==========================================================
# SEO - ROBOTS.TXT
# Libera o site para Google e outros mecanismos de busca
# ==========================================================

@app.get('/robots.txt')
def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: https://www.karencarolineimoveis.com.br/sitemap.xml
"""
    return Response(
        content,
        mimetype='text/plain'
    )

@app.get('/')
def home():
    index_file = BASE / 'index.html'
    return Response(index_file.read_text(encoding='utf-8'), mimetype='text/html')

@app.get('/<path:path>')
def public_files(path):
    normalized = path.replace('\\', '/')
    if normalized in PUBLIC_PAGES or normalized in PUBLIC_ROOT_ASSETS:
        return send_from_directory(BASE, normalized)
    if normalized.startswith('assets/') and Path(normalized).suffix.lower() in PUBLIC_ASSET_EXTENSIONS:
        return send_from_directory(BASE, normalized)
    abort(404)


init_db()

if __name__ == '__main__':
    port=int(os.environ.get('PORT','5000'))
    app.run(host='0.0.0.0',port=port,debug=False)
