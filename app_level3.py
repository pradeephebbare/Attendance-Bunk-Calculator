import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io
import math
from datetime import date

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BunkMeter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.stApp { background: #060610; color: #dde0f0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0c0c1e !important;
    border-right: 1px solid #1a1a35;
}

h1,h2,h3 { font-family: 'Outfit', sans-serif; font-weight: 800; }

.tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #404068;
    margin-bottom: 0.4rem;
}

/* KPI Cards */
.kpi {
    background: #0e0e20;
    border: 1px solid #1e1e38;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.kpi-accent { position:absolute; top:0;left:0;right:0;height:3px; border-radius:14px 14px 0 0; }
.kpi-val { font-size: 2.2rem; font-weight: 800; line-height: 1; margin: 0.2rem 0; }
.kpi-sub { font-size: 0.78rem; color: #555580; margin-top: 0.2rem; }

/* Subject cards */
.sub-card {
    background: #0e0e20;
    border: 1px solid #1e1e38;
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.7rem;
}
.sub-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; }
.sub-name { font-weight: 700; font-size: 1rem; }
.pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    letter-spacing: 0.1em;
}
.pill-safe   { background:#00ff9020; color:#00ff90; border:1px solid #00ff9040; }
.pill-warn   { background:#ffb30020; color:#ffb300; border:1px solid #ffb30040; }
.pill-danger { background:#ff335520; color:#ff3355; border:1px solid #ff335540; }

.bar-bg { background:#181830; border-radius:999px; height:10px; margin:0.4rem 0; overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; }

.stat-row { display:flex; gap:1.5rem; margin-top:0.5rem; }
.stat-item { font-size:0.8rem; }
.stat-label { color:#404068; font-size:0.7rem; font-family:'JetBrains Mono',monospace; text-transform:uppercase; }

.divider { border:none; border-top:1px solid #1a1a30; margin:1.2rem 0; }

.stButton>button {
    background: linear-gradient(135deg,#2d6fff,#00c9ff) !important;
    color:#fff !important; border:none !important;
    border-radius:8px !important;
    font-family:'Outfit',sans-serif !important;
    font-weight:700 !important;
    padding: 0.5rem 1.3rem !important;
}
.stButton>button:hover { opacity:0.85 !important; }

.upload-hint {
    background:#0a0a1e;
    border:1px dashed #2a2a50;
    border-radius:12px;
    padding:1.2rem;
    text-align:center;
    color:#404068;
    font-size:0.85rem;
    margin-bottom:1rem;
}

.tip {
    background:#0a1525;
    border-left: 3px solid #2d6fff;
    border-radius:0 8px 8px 0;
    padding:0.7rem 1rem;
    font-size:0.82rem;
    color:#6090c0;
    margin-top:0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ─── Core Logic (your bunk_calc) ──────────────────────────────────────────────
TARGET = 75

def bunk_calc(total, attended):
    if total == 0:
        return None
    pct = (attended / total) * 100

    # Safe skips — your fixed loop
    bunk_count = 0
    future_total = total + 1
    while (attended / future_total) * 100 >= TARGET:
        bunk_count += 1
        future_total += 1

    # Classes needed to recover
    extra = 0
    ft, fa = total, attended
    while (fa / ft) * 100 < TARGET:
        ft += 1
        fa += 1
        extra += 1

    status = "safe" if pct >= TARGET + 5 else ("warn" if pct >= TARGET else "danger")
    return {
        "pct": round(pct, 2),
        "safe_skips": bunk_count,
        "classes_needed": extra,
        "status": status,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────
STATUS_COLOR = {"safe": "#00ff90", "warn": "#ffb300", "danger": "#ff3355"}
STATUS_LABEL = {"safe": "SAFE ✓", "warn": "BORDERLINE", "danger": "SHORTAGE ✗"}
BAR_GRADIENT = {
    "safe":   "linear-gradient(90deg,#00ff90,#00c9ff)",
    "warn":   "linear-gradient(90deg,#ffb300,#ff6d00)",
    "danger": "linear-gradient(90deg,#ff3355,#c000ff)",
}

def pill_html(status):
    return f'<span class="pill pill-{status}">{STATUS_LABEL[status]}</span>'

def bar_html(pct, status):
    w = min(max(pct, 0), 100)
    return f"""<div class="bar-bg"><div class="bar-fill" style="width:{w}%;background:{BAR_GRADIENT[status]};"></div></div>"""


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 BunkMeter")
    st.markdown("*How many can you really skip?*")
    st.markdown("---")

    min_pct = st.slider("Minimum Required %", 50, 85, 75, step=5)
    TARGET = min_pct

    st.markdown("---")
    mode = st.radio("Input Mode", ["✏️ Manual Entry", "📂 Upload File"])

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.72rem;color:#303055;font-family:JetBrains Mono,monospace;line-height:1.8;'>
    FORMULA<br>
    safe_skips = loop until<br>
    &nbsp;&nbsp;att/(total+n) &lt; 75%<br><br>
    needed = loop until<br>
    &nbsp;&nbsp;(att+n)/(tot+n) ≥ 75%
    </div>
    """, unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("# BunkMeter 🎓")
st.markdown('<p style="color:#303055;font-family:JetBrains Mono,monospace;font-size:0.8rem;margin-top:-0.8rem;">COLLEGE ATTENDANCE PREDICTOR — LEVEL 3</p>', unsafe_allow_html=True)

subjects = []

# ─── Manual Entry ─────────────────────────────────────────────────────────────
if mode == "✏️ Manual Entry":
    if "rows" not in st.session_state:
        st.session_state.rows = [
            {"subject": "Mathematics", "attended": 45, "total": 56},
            {"subject": "Physics",     "attended": 28, "total": 40},
            {"subject": "Chemistry",   "attended": 32, "total": 38},
        ]

    st.markdown('<div class="tag">Add / Edit Subjects</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    with c1: nn = st.text_input("Subject", placeholder="e.g. Data Structures", key="nn")
    with c2: na = st.number_input("Attended", 0, 300, 0, key="na")
    with c3: nt = st.number_input("Total",    1, 300, 30, key="nt")
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Add") and nn.strip():
            st.session_state.rows.append({"subject": nn.strip(), "attended": na, "total": nt})
            st.rerun()

    to_del = None
    for i, row in enumerate(st.session_state.rows):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1: st.session_state.rows[i]["subject"]  = st.text_input("", value=row["subject"],  key=f"s{i}", label_visibility="collapsed")
        with c2: st.session_state.rows[i]["attended"] = st.number_input("", 0, 300, row["attended"], key=f"a{i}", label_visibility="collapsed")
        with c3: st.session_state.rows[i]["total"]    = st.number_input("", 1, 300, row["total"],    key=f"t{i}", label_visibility="collapsed")
        with c4:
            if st.button("✕", key=f"d{i}"): to_del = i
    if to_del is not None:
        st.session_state.rows.pop(to_del)
        st.rerun()

    subjects = st.session_state.rows

# ─── Upload Mode ──────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="upload-hint">
        Upload a CSV or Excel file with columns: <b>Subject, Attended, Total</b>
    </div>""", unsafe_allow_html=True)

    # Template download
    tpl = pd.DataFrame({"Subject": ["Mathematics","Physics","Chemistry"],
                        "Attended": [45, 28, 32], "Total": [56, 40, 38]})
    buf = io.BytesIO()
    tpl.to_excel(buf, index=False)
    st.download_button("⬇ Download Template", buf.getvalue(),
                       "template.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    f = st.file_uploader("", type=["csv","xlsx"], label_visibility="collapsed")
    if f:
        try:
            df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
            df.columns = [c.strip().lower() for c in df.columns]
            rename = {}
            for c in df.columns:
                if "sub" in c: rename[c] = "subject"
                if "att" in c: rename[c] = "attended"
                if "tot" in c: rename[c] = "total"
            df = df.rename(columns=rename)
            subjects = df[["subject","attended","total"]].to_dict("records")
            st.success(f"✓ Loaded {len(subjects)} subjects")
        except Exception as e:
            st.error(f"Error: {e}")


# ─── Results ──────────────────────────────────────────────────────────────────
if subjects:
    results = []
    for s in subjects:
        r = bunk_calc(s["total"], s["attended"])
        if r:
            results.append({**s, **r})

    if not results:
        st.warning("No valid data to analyse.")
        st.stop()

    # ── KPI Row ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="tag">Overview</div>', unsafe_allow_html=True)

    total_att = sum(r["attended"] for r in results)
    total_cls = sum(r["total"]    for r in results)
    overall   = round(total_att / total_cls * 100, 2) if total_cls else 0
    ov_status = "safe" if overall >= TARGET + 5 else ("warn" if overall >= TARGET else "danger")
    ov_color  = STATUS_COLOR[ov_status]

    danger_n = sum(1 for r in results if r["status"] == "danger")
    warn_n   = sum(1 for r in results if r["status"] == "warn")
    total_skips = sum(r["safe_skips"] for r in results)
    total_needed = sum(r["classes_needed"] for r in results)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-accent" style="background:{ov_color};"></div>
            <div class="tag">Overall Attendance</div>
            <div class="kpi-val" style="color:{ov_color};">{overall}%</div>
            <div class="kpi-sub">{total_att} of {total_cls} classes</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        sk_color = "#00ff90" if total_skips > 0 else "#ff3355"
        st.markdown(f"""<div class="kpi">
            <div class="kpi-accent" style="background:{sk_color};"></div>
            <div class="tag">Total Safe Skips</div>
            <div class="kpi-val" style="color:{sk_color};">{total_skips}</div>
            <div class="kpi-sub">across all subjects</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        nd_color = "#ff3355" if total_needed > 0 else "#00ff90"
        st.markdown(f"""<div class="kpi">
            <div class="kpi-accent" style="background:{nd_color};"></div>
            <div class="tag">Classes Still Needed</div>
            <div class="kpi-val" style="color:{nd_color};">{total_needed}</div>
            <div class="kpi-sub">to reach {TARGET}% in weak subjects</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-accent" style="background:#2d6fff;"></div>
            <div class="tag">Subjects Tracked</div>
            <div class="kpi-val" style="color:#2d6fff;">{len(results)}</div>
            <div class="kpi-sub">{danger_n} shortage · {warn_n} borderline</div>
        </div>""", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="tag">Charts</div>', unsafe_allow_html=True)

    col_chart, col_pie = st.columns([3, 2])

    with col_chart:
        # Bar chart — attendance % per subject
        names  = [r["subject"]  for r in results]
        pcts   = [r["pct"]      for r in results]
        colors = [STATUS_COLOR[r["status"]] for r in results]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=names, y=pcts,
            marker_color=colors,
            marker_line_width=0,
            text=[f"{p}%" for p in pcts],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color="#dde0f0"),
        ))
        fig_bar.add_hline(y=TARGET, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                          annotation_text=f"{TARGET}% required",
                          annotation_font_color="rgba(255,255,255,0.5)",
                          annotation_font_size=10)
        fig_bar.update_layout(
            title=dict(text="Attendance % by Subject", font=dict(family="Outfit", size=14, color="#7070a0")),
            paper_bgcolor="#0e0e20", plot_bgcolor="#0e0e20",
            font=dict(family="Outfit", color="#7070a0"),
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#1a1a30", range=[0, 110]),
            margin=dict(t=40, b=20, l=10, r=10),
            showlegend=False,
            height=300,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_pie:
        # Pie — safe vs borderline vs shortage
        safe_n = sum(1 for r in results if r["status"] == "safe")
        pie_vals   = [safe_n, warn_n, danger_n]
        pie_labels = ["Safe", "Borderline", "Shortage"]
        pie_colors = ["#00ff90", "#ffb300", "#ff3355"]

        fig_pie = go.Figure(go.Pie(
            labels=pie_labels, values=pie_vals,
            marker=dict(colors=pie_colors, line=dict(color="#060610", width=3)),
            textfont=dict(family="JetBrains Mono", size=11),
            hole=0.55,
        ))
        fig_pie.update_layout(
            title=dict(text="Subject Status Split", font=dict(family="Outfit", size=14, color="#7070a0")),
            paper_bgcolor="#0e0e20",
            font=dict(family="Outfit", color="#7070a0"),
            legend=dict(font=dict(size=11)),
            margin=dict(t=40, b=10, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Skips vs Needed bar chart
    fig_skip = go.Figure()
    fig_skip.add_trace(go.Bar(
        name="Safe Skips", x=names,
        y=[r["safe_skips"] for r in results],
        marker_color="#00ff90", marker_line_width=0,
    ))
    fig_skip.add_trace(go.Bar(
        name="Classes Needed", x=names,
        y=[r["classes_needed"] for r in results],
        marker_color="#ff3355", marker_line_width=0,
    ))
    fig_skip.update_layout(
        title=dict(text="Safe Skips vs Classes Needed per Subject", font=dict(family="Outfit", size=14, color="#7070a0")),
        barmode="group",
        paper_bgcolor="#0e0e20", plot_bgcolor="#0e0e20",
        font=dict(family="Outfit", color="#7070a0"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1a1a30"),
        legend=dict(font=dict(size=11)),
        margin=dict(t=40, b=20, l=10, r=10),
        height=280,
    )
    st.plotly_chart(fig_skip, use_container_width=True)

    # ── Subject Dashboard ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="tag">Subject Dashboard</div>', unsafe_allow_html=True)

    for r in results:
        color = STATUS_COLOR[r["status"]]
        skip_msg = (f"🟢 You can skip <b>{r['safe_skips']}</b> more class{'es' if r['safe_skips']!=1 else ''} safely"
                    if r["safe_skips"] > 0
                    else f"🔴 Attend <b>{r['classes_needed']}</b> consecutive class{'es' if r['classes_needed']!=1 else ''} to recover")

        st.markdown(f"""
        <div class="sub-card">
            <div class="sub-header">
                <span class="sub-name">{r['subject']}</span>
                {pill_html(r['status'])}
            </div>
            <div style="font-size:1.8rem;font-weight:800;color:{color};line-height:1;">{r['pct']}%</div>
            {bar_html(r['pct'], r['status'])}
            <div style="font-size:0.75rem;color:#303055;font-family:JetBrains Mono,monospace;margin-bottom:0.5rem;">
                {r['attended']} attended / {r['total']} total &nbsp;·&nbsp; need {TARGET}%
            </div>
            <div style="font-size:0.85rem;color:#c0c8e8;">{skip_msg}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="tag">Export Report</div>', unsafe_allow_html=True)

    export_df = pd.DataFrame([{
        "Subject":        r["subject"],
        "Attended":       r["attended"],
        "Total":          r["total"],
        "Attendance %":   r["pct"],
        "Safe Skips":     r["safe_skips"],
        "Classes Needed": r["classes_needed"],
        "Status":         STATUS_LABEL[r["status"]],
        "Date":           str(date.today()),
    } for r in results])

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇ Download CSV", export_df.to_csv(index=False).encode(),
                           "bunkmeter_report.csv", "text/csv")
    with c2:
        xl = io.BytesIO()
        export_df.to_excel(xl, index=False)
        st.download_button("⬇ Download Excel", xl.getvalue(),
                           "bunkmeter_report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#303055;">
        <div style="font-size:3rem;">📊</div>
        <div style="font-weight:700;font-size:1.1rem;margin-top:0.5rem;">No data yet</div>
        <div style="font-size:0.85rem;margin-top:0.3rem;">Add subjects manually or upload a file to get started.</div>
    </div>""", unsafe_allow_html=True)
