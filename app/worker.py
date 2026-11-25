import subprocess
import sys
from .database import connection
from .search import find_sites

def run_job(job_id):
    with connection() as db:
        job = db.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
        if not job:
            return
        db.execute("UPDATE jobs SET status='a_pesquisar' WHERE id=%s", (job_id,))
        db.commit()
    try:
        urls = find_sites(job["pesquisa"], job["limite"])
        if not urls:
            raise RuntimeError("Sem resultados de pesquisa. Tenta outra expressão ou outro motor de pesquisa.")
        with connection() as db:
            db.execute("UPDATE jobs SET status='a_rastrear',discovered=%s WHERE id=%s", (len(urls),job_id))
            db.commit()
        import json
        cmd = [sys.executable, "-m", "app.run_spider", json.dumps(urls), job["pesquisa"], str(job["profundidade"]), "100"]
        result = subprocess.run(cmd, timeout=21600, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout)[-1500:])
        with connection() as db:
            total = db.execute("SELECT COUNT(*) AS n FROM contacts WHERE pesquisa=%s", (job["pesquisa"],)).fetchone()["n"]
            db.execute("UPDATE jobs SET status='concluido',saved=%s,finished_at=NOW() WHERE id=%s", (total,job_id))
            db.commit()
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE jobs SET status='erro',error=%s,finished_at=NOW() WHERE id=%s", (str(exc)[:2000],job_id))
            db.commit()
