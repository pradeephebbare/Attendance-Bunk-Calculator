import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bunkmeter-dev-secret")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
TARGET = 75


def bunk_calc_for_target(total, attended, target):
    if total == 0:
        return None
    pct = (attended / total) * 100

    bunk_count = 0
    future_total = total + 1
    while (attended / future_total) * 100 >= target:
        bunk_count += 1
        future_total += 1

    extra = 0
    ft, fa = total, attended
    while (fa / ft) * 100 < target:
        ft += 1
        fa += 1
        extra += 1

    status = "safe" if pct >= target + 5 else ("warn" if pct >= target else "danger")
    return {
        "pct": round(pct, 2),
        "safe_skips": bunk_count,
        "classes_needed": extra,
        "status": status,
    }


def bunk_calc(total, attended):
    return bunk_calc_for_target(total, attended, TARGET)


def normalise_subjects(raw_subjects):
    cleaned = []
    for row in raw_subjects or []:
        if not isinstance(row, dict):
            continue
        subject = str(row.get("subject", "") or "").strip()
        total = int(row.get("total", 0) or 0)
        attended = int(row.get("attended", 0) or 0)
        if not subject or total <= 0:
            continue
        cleaned.append({"subject": subject, "total": total, "attended": attended})
    return cleaned


def build_summary(subjects, target):
    results = []
    for row in normalise_subjects(subjects):
        calc = bunk_calc_for_target(row["total"], row["attended"], target)
        if calc is not None:
            results.append({**row, **calc})

    if not results:
        return {
            "summary": {
                "overall_pct": 0,
                "overall_status": "danger",
                "safe_skips": 0,
                "classes_needed": 0,
                "total_subjects": 0,
                "safe_count": 0,
                "warn_count": 0,
                "danger_count": 0,
            },
            "subjects": [],
            "chart": {"labels": [], "values": [], "status": [0, 0, 0]},
        }

    total_attended = sum(item["attended"] for item in results)
    total_classes = sum(item["total"] for item in results)
    overall_pct = round((total_attended / total_classes) * 100, 2) if total_classes else 0
    overall_status = "safe" if overall_pct >= target + 5 else ("warn" if overall_pct >= target else "danger")
    safe_count = sum(1 for item in results if item["status"] == "safe")
    warn_count = sum(1 for item in results if item["status"] == "warn")
    danger_count = sum(1 for item in results if item["status"] == "danger")

    return {
        "summary": {
            "overall_pct": overall_pct,
            "overall_status": overall_status,
            "safe_skips": sum(item["safe_skips"] for item in results),
            "classes_needed": sum(item["classes_needed"] for item in results),
            "total_subjects": len(results),
            "safe_count": safe_count,
            "warn_count": warn_count,
            "danger_count": danger_count,
        },
        "subjects": results,
        "chart": {
            "labels": [item["subject"] for item in results],
            "values": [item["pct"] for item in results],
            "status": [safe_count, warn_count, danger_count],
        },
    }


@app.route("/")
def index():
    if not session.get("is_authenticated"):
        return redirect(url_for("login"))
    return render_template("index.html", user_email=session.get("user_email", "Student"))


@app.route("/login")
def login():
    return render_template(
        "login.html",
        supabase_url=SUPABASE_URL,
        supabase_anon_key=SUPABASE_ANON_KEY,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/auth/session", methods=["POST"])
def auth_session():
    payload = request.get_json(force=True, silent=True) or {}
    access_token = payload.get("access_token")
    if not access_token:
        return jsonify({"ok": False, "error": "Missing access token"}), 400

    session["supabase_access_token"] = access_token
    session["user_email"] = payload.get("user_email") or payload.get("email") or "student@bunkmeter.app"
    session["is_authenticated"] = True
    return jsonify({"ok": True, "redirect": url_for("index")})


@app.route("/api/config")
def app_config():
    return jsonify({
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
    })


@app.route("/api/calc", methods=["POST"])
def calc():
    payload = request.get_json(force=True, silent=True) or {}
    target = int(payload.get("target", TARGET))
    subjects = payload.get("subjects", [])
    data = build_summary(subjects, target)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
