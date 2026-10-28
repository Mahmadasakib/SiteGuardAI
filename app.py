from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "siteguard.db"


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS hazards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                reported_at TEXT NOT NULL,
                acknowledged_by TEXT DEFAULT '',
                resolved_at TEXT DEFAULT ''
            )
        """)


HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SiteGuard AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#f1f5f9;color:#172033}
header{background:#12352b;color:white;padding:25px}
header h1{margin:0}
header p{color:#c9e8d7}
.container{max-width:1050px;margin:25px auto;padding:0 15px}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card,.panel{background:white;padding:20px;border-radius:12px;
box-shadow:0 2px 8px #0001;margin-bottom:16px}
.card{flex:1;min-width:130px}
.number{font-size:30px;font-weight:bold;color:#147d52}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
input,textarea,select{box-sizing:border-box;width:100%;padding:11px;
margin:7px 0 14px;border:1px solid #ccd5df;border-radius:7px}
button{background:#147d52;color:white;border:0;padding:11px 15px;
border-radius:7px;cursor:pointer;margin:3px}
.danger{background:#b42318}
.badge{font-weight:bold;color:#b42318}
small{color:#526174}
@media(max-width:650px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
<h1>🛡️ SiteGuard AI</h1>
<p>Construction Site Safety & Hazard Management</p>
<strong>Team Quantum Coders</strong>
</header>
<div class="container">
<div class="cards">
<div class="card">Total Hazards<h2 class="number">{{ total }}</h2></div>
<div class="card">Open Hazards<h2 class="number">{{ opened }}</h2></div>
<div class="card">Pending Acknowledgement<h2 class="number">{{ pending }}</h2></div>
<div class="card">Resolved<h2 class="number">{{ resolved }}</h2></div>
</div>

<div class="grid">
<section class="panel">
<h2>🚨 Report a Hazard</h2>
<form method="POST" action="/report">
<label>Hazard title</label>
<input name="title" required placeholder="Exposed electrical wire">
<label>Location</label>
<input name="location" required placeholder="Main walkway">
<label>Description</label>
<textarea name="description" required
placeholder="Describe the hazard"></textarea>
<label>Severity</label>
<select name="severity">
<option>Critical</option>
<option>High</option>
<option>Medium</option>
<option>Low</option>
</select>
<button type="submit">Submit Hazard Report</button>
</form>
</section>

<section class="panel">
<h2>🤖 Safety Chatbot</h2>
<form method="POST" action="/chat">
<label>Ask a safety question</label>
<textarea name="question" required
placeholder="What should I do if I see an electrical hazard?"></textarea>
<button>Ask Chatbot</button>
</form>
{% if answer %}
<div style="background:#e8f7ee;padding:12px;border-radius:8px">
<strong>Safety Assistant:</strong><p>{{ answer }}</p>
</div>
{% endif %}
<p><small>Prototype safety guidance. Follow site emergency procedures
and instructions from qualified safety personnel.</small></p>
</section>
</div>

<section class="panel">
<h2>🧠 Safety Agent Activity</h2>
<p>The local workflow checks hazard status and highlights urgent
reports. Supervisor actions are recorded below.</p>
<p><strong>Agent status:</strong> Monitoring saved hazard reports</p>
</section>

<section class="panel">
<h2>📋 Hazard Register</h2>
{% for h in hazards %}
<div style="border-bottom:1px solid #ddd;padding:12px 0">
<h3>#{{ h[0] }} — {{ h[1] }}</h3>
<p><strong>Location:</strong> {{ h[2] }}</p>
<p>{{ h[3] }}</p>
<p><strong>Severity:</strong>
<span class="badge">{{ h[4] }}</span>
| <strong>Status:</strong> {{ h[5] }}</p>
<p><small>Reported: {{ h[6] }}</small></p>
<p><strong>Acknowledged by:</strong>
{{ h[7] if h[7] else 'Pending' }}</p>
{% if h[5] != 'Resolved' %}
<form method="POST" action="/ack/{{ h[0] }}">
<input name="supervisor" required placeholder="Supervisor name">
<button>Acknowledge</button>
</form>
<form method="POST" action="/resolve/{{ h[0] }}">
<button class="danger">Mark Resolved</button>
</form>
{% endif %}
</div>
{% else %}
<p>No hazards reported yet. Submit a test report above.</p>
{% endfor %}
</section>
</div>
</body>
</html>
"""


def get_hazards():
    with sqlite3.connect(DB) as con:
        return con.execute(
            "SELECT * FROM hazards ORDER BY id DESC"
        ).fetchall()


@app.route("/")
def home():
    hazards = get_hazards()
    total = len(hazards)
    opened = sum(h[5] != "Resolved" for h in hazards)
    resolved = sum(h[5] == "Resolved" for h in hazards)
    pending = sum(
        h[5] != "Resolved" and not h[7] for h in hazards
    )
    return render_template_string(
        HTML, hazards=hazards, total=total, opened=opened,
        resolved=resolved, pending=pending, answer=""
    )


@app.route("/report", methods=["POST"])
def report():
    title = request.form["title"].strip()
    location = request.form["location"].strip()
    description = request.form["description"].strip()
    severity = request.form["severity"]

    if severity not in ["Critical", "High", "Medium", "Low"]:
        severity = "High"

    with sqlite3.connect(DB) as con:
        con.execute("""
            INSERT INTO hazards
            (title, location, description, severity, reported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, location, description, severity,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    return redirect("/")


@app.route("/ack/<int:hid>", methods=["POST"])
def acknowledge(hid):
    name = request.form["supervisor"].strip()
    with sqlite3.connect(DB) as con:
        con.execute("""
            UPDATE hazards SET acknowledged_by=?
            WHERE id=? AND status!='Resolved'
        """, (name, hid))
    return redirect("/")


@app.route("/resolve/<int:hid>", methods=["POST"])
def resolve(hid):
    with sqlite3.connect(DB) as con:
        con.execute("""
            UPDATE hazards SET status='Resolved', resolved_at=?
            WHERE id=?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hid))
    return redirect("/")


@app.route("/chat", methods=["POST"])
def chat():
    q = request.form["question"].lower()

    if any(w in q for w in ["electric", "wire", "shock"]):
        answer = (
            "Keep away from the suspected electrical hazard. Do not "
            "touch the wire or attempt repairs. Warn nearby people "
            "from a safe distance, notify the responsible supervisor "
            "immediately, and follow the site's emergency procedures."
        )
    elif any(w in q for w in ["fire", "smoke"]):
        answer = (
            "Raise the site's alarm, move away using the designated "
            "safe route, and contact the emergency response team. "
            "Do not attempt to fight a fire unless trained and it is "
            "safe to do so."
        )
    elif any(w in q for w in ["helmet", "ppe", "protective"]):
        answer = (
            "Follow site PPE rules. Use the protective equipment "
            "required for your task and report damaged or missing "
            "equipment to your supervisor."
        )
    else:
        answer = (
            "Report the hazard using the form on this page. Keep a "
            "safe distance, warn others if safe, and notify the "
            "responsible supervisor. Follow official site procedures."
        )

    hazards = get_hazards()
    return render_template_string(
        HTML, hazards=hazards, total=len(hazards),
        opened=sum(h[5] != "Resolved" for h in hazards),
        resolved=sum(h[5] == "Resolved" for h in hazards),
        pending=sum(h[5] != "Resolved" and not h[7] for h in hazards),
        answer=answer
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)