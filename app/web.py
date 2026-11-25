import csv
import io
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from .database import connection, init_db
from .worker import run_job

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="Crawler IA - Escolas", lifespan=lifespan)

PAGE = '''<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Crawler IA — Escolas</title>
<style>body{font:16px system-ui;background:#f4f6fb;color:#172036;max-width:1000px;margin:45px auto;padding:0 20px}h1{color:#253a7b}.panel{background:white;padding:25px;border-radius:14px;box-shadow:0 2px 12px #0001;margin-bottom:20px}input{padding:11px;border:1px solid #bec6d5;border-radius:7px;max-width:100%}button,.btn{background:#263f97;color:white;border:0;padding:12px 20px;border-radius:7px;cursor:pointer;text-decoration:none;display:inline-block}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px;border-bottom:1px solid #dde2ed}small{color:#626e84}</style></head><body>
<h1>Crawler IA · Escolas e Creches</h1><p>Pesquisa de sites públicos, recolha de contactos institucionais e exportação para Keila. Os resultados devem ser revistos antes de qualquer utilização.</p>
<section class="panel"><h2>Nova pesquisa</h2><form method="post" action="/jobs"><p><input name="pesquisa" placeholder="Ex.: escolas primárias Lisboa" required size="55" maxlength="200"></p><p>Resultados da pesquisa: <input type="number" name="limite" value="15" min="1" max="100" style="width:80px"> &nbsp; Profundidade: <input type="number" name="profundidade" value="2" min="0" max="4" style="width:70px"></p><button>Iniciar pesquisa</button></form><small>O motor Bing é experimental; a API Google exige credenciais próprias.</small></section>
<section class="panel"><h2>Pesquisas recentes</h2><table><thead><tr><th>Termos</th><th>Estado</th><th>Sites</th><th>Emails</th><th>Erro</th></tr></thead><tbody>{jobs}</tbody></table></section>
<section class="panel"><h2>Contactos guardados ({count})</h2><a class="btn" href="/export.csv">Exportar CSV completo</a> <a class="btn" href="/keila.csv">CSV simplificado para Keila</a><p><small>Os emails estão identificados pela fonte original. Não existe envio automático nem inscrição automática na Keila.</small></p><table><thead><tr><th>Escola</th><th>Email</th><th>Fonte</th></tr></thead><tbody>{contacts}</tbody></table></section><script>setTimeout(()=>location.reload(),12000)</script></body></html>'''

@app.get("/", response_class=HTMLResponse)
def index():
    import html
    with connection() as db:
        jobs = db.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 20").fetchall()
        contacts = db.execute("SELECT * FROM contacts ORDER BY id DESC LIMIT 30").fetchall()
        count = db.execute("SELECT COUNT(*) AS n FROM contacts").fetchone()["n"]
    trjobs = "".join("<tr>"+"".join("<td>"+html.escape(str(x))+"</td>" for x in (j["pesquisa"], j["status"], j["discovered"], j["saved"], j["error"][:120]))+"</tr>" for j in jobs)
    trcontacts = "".join("<tr><td>"+html.escape(c["escola"])+"</td><td>"+html.escape(c["email"])+"</td><td>"+html.escape(c["fonte"][:90])+"</td></tr>" for c in contacts)
    return PAGE.replace("{jobs}", trjobs).replace("{contacts}", trcontacts).replace("{count}", str(count))

@app.post("/jobs")
def create_job(pesquisa: str=Form(...), limite: int=Form(15), profundidade: int=Form(2)):
    pesquisa=pesquisa.strip()[:200]
    if not pesquisa:
        return RedirectResponse("/", status_code=303)
    limite=max(1,min(100,limite)); profundidade=max(0,min(4,profundidade))
    with connection() as db:
        job=db.execute("INSERT INTO jobs(pesquisa,limite,profundidade) VALUES(%s,%s,%s) RETURNING id", (pesquisa,limite,profundidade)).fetchone()
        db.commit()
    threading.Thread(target=run_job,args=(job["id"],),daemon=True).start()
    return RedirectResponse("/", status_code=303)

FIELDS = ["email", "escola", "responsavel", "saudacao", "website", "fonte", "pesquisa", "data_recolha", "revisto"]

def csv_out(simple=False):
    with connection() as db:
        rows = db.execute("SELECT * FROM contacts ORDER BY escola,email").fetchall()
    out=io.StringIO()
    fields=["email", "first_name", "last_name", "school", "greeting"] if simple else FIELDS
    writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
    for r in rows:
        if simple:
            writer.writerow({"email":r["email"],"first_name":"","last_name":"","school":r["escola"],"greeting":r["saudacao"]})
        else:
            writer.writerow({key:str(r[key]) if r[key] is not None else "" for key in fields})
    return Response(content="\ufeff"+out.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="{"keila" if simple else "contactos"}.csv"'})

@app.get("/export.csv")
def export_all(): return csv_out(False)

@app.get("/keila.csv")
def export_keila(): return csv_out(True)

@app.get("/health")
def health(): return {"status":"ok"}
