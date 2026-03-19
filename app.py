import os, json, time, sqlite3, uuid, traceback
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "app.db")
APP_NAME = os.environ.get("APP_NAME", "vm-app-a")
BROKEN_FLAG = os.environ.get("BROKEN_FLAG", "/tmp/breakdb.flag")

def log(level, message, **kwargs):
    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "app": APP_NAME,
        "msg": message,
        **kwargs
    }
    print(json.dumps(payload), flush=True)

def db_connect():
    # Simula “DB caída” si existe el flag
    if os.path.exists(BROKEN_FLAG):
        raise RuntimeError("DB is intentionally broken (flag file present).")
    return sqlite3.connect(DB_PATH, timeout=2)

@app.route("/health")
def health():
    rid = str(uuid.uuid4())
    log("INFO", "health_check", request_id=rid, path="/health")
    return jsonify(status="ok", app=APP_NAME, request_id=rid)

@app.route("/data")
def data():
    rid = str(uuid.uuid4())
    start = time.time()
    try:
        con = db_connect()
        cur = con.cursor()
        cur.execute("SELECT id, name, created_at FROM items ORDER BY id LIMIT 10")
        rows = [{"id": r[0], "name": r[1], "created_at": r[2]} for r in cur.fetchall()]
        con.close()

        duration_ms = int((time.time() - start) * 1000)
        log("INFO", "data_query_ok", request_id=rid, path="/data", duration_ms=duration_ms, rowcount=len(rows))
        return jsonify(items=rows, duration_ms=duration_ms, request_id=rid)

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        log("ERROR", "data_query_failed",
            request_id=rid, path="/data", duration_ms=duration_ms,
            error=str(e),
            stack=traceback.format_exc()[:2000]
        )
        return jsonify(error="db_query_failed", detail=str(e), request_id=rid), 500

@app.route("/slow")
def slow():
    rid = str(uuid.uuid4())
    ms = int(request.args.get("ms", "500"))
    log("WARN", "slow_endpoint", request_id=rid, ms=ms)
    time.sleep(ms / 1000.0)
    return jsonify(status="slept", ms=ms, request_id=rid)

@app.route("/breakdb", methods=["POST"])
def breakdb():
    rid = str(uuid.uuid4())
    open(BROKEN_FLAG, "w").write("broken")
    log("WARN", "db_broken_enabled", request_id=rid, flag=BROKEN_FLAG)
    return jsonify(status="db_broken_enabled", request_id=rid)

@app.route("/fixdb", methods=["POST"])
def fixdb():
    rid = str(uuid.uuid4())
    if os.path.exists(BROKEN_FLAG):
        os.remove(BROKEN_FLAG)
    log("INFO", "db_broken_disabled", request_id=rid)
    return jsonify(status="db_broken_disabled", request_id=rid)

if __name__ == "__main__":
    # dev only
    app.run(host="0.0.0.0", port=8080)