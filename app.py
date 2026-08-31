from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session, Response, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
import sqlite3, json, os, csv, io, html, re, secrets, time

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get('DB_PATH', DATA_DIR / 'leads.db'))

app = Flask(__name__, static_folder=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '1') == '1',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '5519974078273')
ALLOWED_ORIGINS = {o.strip() for o in os.environ.get('ALLOWED_ORIGINS', 'https://www.karencarolineimoveis.com.br,https://karencarolineimoveis.com.br,http://127.0.0.1:5000,http://localhost:5000,null').split(',') if o.strip()}
STATUS_OPTIONS = ['Novo', 'Em contato', 'Visita agendada', 'Proposta', 'Venda', 'Sem interesse']
RATE = {}


def db():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=15000')
    return con


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            utm_term TEXT DEFAULT ''
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            empreendimento TEXT,
            origem TEXT,
            pagina_url TEXT,
            pagina_titulo TEXT,
            referrer TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            criado_em TEXT NOT NULL
        )''')
        con.commit()


def esc(v):
    return html.escape(str(v or ''))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def client_ip():
    return (request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or request.remote_addr or 'unknown')


def limited(key, limit, window=60):
    now = time.time()
    bucket = RATE.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def admin_required():
    return session.get('admin') is True


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
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return resp


@app.get('/health')
def health():
    return {'ok': True, 'service': 'Karen Caroline Imóveis'}


@app.post('/api/events')
def events():
    if limited(f'events:{client_ip()}', 120, 60):
        return jsonify(ok=False, error='Muitas requisições.'), 429
    data = request.get_json(silent=True) or {}
    tipo = str(data.get('tipo','')).strip()[:80]
    if not tipo:
        return jsonify(ok=False), 400
    with db() as con:
        con.execute('''INSERT INTO interactions (tipo,empreendimento,origem,pagina_url,pagina_titulo,referrer,utm_source,utm_medium,utm_campaign,criado_em) VALUES (?,?,?,?,?,?,?,?,?,?)''', (
            tipo, str(data.get('empreendimento','')).strip()[:160], str(data.get('origem','')).strip()[:160], str(data.get('pagina_url','')).strip()[:1000], str(data.get('pagina_titulo','')).strip()[:300], str(data.get('referrer','')).strip()[:1000], str(data.get('utm_source','')).strip()[:160], str(data.get('utm_medium','')).strip()[:160], str(data.get('utm_campaign','')).strip()[:300], now_iso()))
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
    origem = str(data.get('origem','site')).strip()[:160]
    interesse = str(data.get('interesse','')).strip()[:300]
    now = now_iso()
    with db() as con:
        cur = con.execute('''INSERT INTO leads (nome,sobrenome,whatsapp,email,empreendimento,origem,interesse,consentimento,utm_source,utm_medium,utm_campaign,criado_em,status,atualizado_em,pagina_url,pagina_titulo,referrer,utm_content,utm_term) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            nome,sobrenome,whatsapp,email_,empreendimento,origem,interesse,1,str(data.get('utm_source','')).strip()[:160],str(data.get('utm_medium','')).strip()[:160],str(data.get('utm_campaign','')).strip()[:300],now,'Novo',now,str(data.get('pagina_url','')).strip()[:1000],str(data.get('pagina_titulo','')).strip()[:300],str(data.get('referrer','')).strip()[:1000],str(data.get('utm_content','')).strip()[:300],str(data.get('utm_term','')).strip()[:300]))
        lead_id = cur.lastrowid
        con.commit()
    resp = {'ok': True, 'lead_id': lead_id, 'message': 'Cadastro realizado com sucesso.'}
    return jsonify(resp)


@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'GET':
        if admin_required():
            return redirect('/admin/leads')
        body = f'''<div class="login"><form class="box" method="post" action="/admin">{csrf_field()}<h1>CRM Imobiliário</h1><p>Entre com a senha administrativa.</p><input type="password" name="senha" placeholder="Senha" required autocomplete="current-password"><button>Entrar</button></form></div>'''
        return layout('CRM Imobiliário', body)
    if limited(f'login:{client_ip()}', 8, 300):
        return layout('CRM Imobiliário', '<div class="login"><div class="box"><h1>Acesso temporariamente bloqueado</h1><p>Aguarde alguns minutos e tente novamente.</p></div></div>'), 429
    if not verify_csrf():
        return layout('CRM Imobiliário', '<div class="login"><div class="box"><h1>Sessão expirada</h1><p>Atualize a página e tente novamente.</p></div></div>'), 400
    if not ADMIN_PASSWORD:
        return layout('Configuração necessária', '<div class="login"><div class="box"><h1>Configuração necessária</h1><p>Defina a variável ADMIN_PASSWORD no servidor antes de usar o CRM.</p></div></div>'), 503
    senha = request.form.get('senha','')
    if secrets.compare_digest(senha, ADMIN_PASSWORD):
        session.clear(); session['admin'] = True; session.permanent = True
        return redirect('/admin/leads')
    body = f'''<div class="login"><form class="box" method="post" action="/admin">{csrf_field()}<h1>CRM Imobiliário</h1><p class="err">Senha incorreta.</p><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form></div>'''
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
    for r in rows: w.writerow({f:r[f] for f in fields})
    raw=out.getvalue().encode('utf-8-sig')
    return Response(raw,mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=leads-crm.csv'})


@app.get('/admin/sair')
def logout():
    session.clear(); return redirect('/admin')


@app.get('/')
def home():
    index_file = BASE / 'index.html'
    return Response(index_file.read_text(encoding='utf-8'), mimetype='text/html')

@app.get('/<path:path>')
def public_files(path):
    if path.startswith(('data/','__pycache__/')) or path in {'app.py','.env','.env.example'}:
        abort(404)
    return send_from_directory(BASE,path)


init_db()

if __name__ == '__main__':
    port=int(os.environ.get('PORT','5000'))
    app.run(host='0.0.0.0',port=port,debug=False)
