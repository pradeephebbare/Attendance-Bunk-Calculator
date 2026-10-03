import io
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─── App Setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BunkMeter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    :root {
        --bg: #07111f;
        --bg-2: #0b1628;
        --panel: rgba(10, 18, 30, 0.92);
        --panel-strong: rgba(12, 22, 36, 0.98);
        --line: rgba(148, 163, 184, 0.15);
        --text: #e6edf9;
        --muted: #98a9c6;
        --primary: #5eead4;
        --primary-2: #60a5fa;
        --danger: #fb7185;
        --warn: #fbbf24;
        --safe: #4ade80;
        --shadow: 0 18px 40px rgba(15, 23, 42, 0.38);
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background: radial-gradient(circle at top left, rgba(96, 165, 250, 0.18), transparent 30%),
                    radial-gradient(circle at top right, rgba(94, 234, 212, 0.18), transparent 30%),
                    linear-gradient(180deg, #050b14 0%, #091827 100%);
        color: var(--text);
    }

    .stApp {
        background: transparent;
    }

    section[data-testid="stSidebar"] {
        background: rgba(7, 15, 24, 0.9) !important;
        border-right: 1px solid var(--line);
        box-shadow: inset -1px 0 0 rgba(148,163,184,0.06);
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4 {
        color: var(--text) !important;
        letter-spacing: -0.04em;
        font-weight: 800 !important;
    }

    .section-kicker {
        font-size: 0.72rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: var(--muted);
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.7rem;
    }

    .glass-panel {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(10, 17, 29, 0.96));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.1rem 1.2rem;
        box-shadow: var(--shadow);
    }

    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--text) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #60a5fa, #5eead4) !important;
        color: #05131e !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.2rem !important;
        box-shadow: 0 12px 28px rgba(96, 165, 250, 0.25);
    }

    .stButton > button:hover {
        opacity: 0.96 !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        width: 100%;
        background: rgba(96, 165, 250, 0.09) !important;
        border: 1px solid rgba(96, 165, 250, 0.28) !important;
        color: var(--text) !important;
        border-radius: 12px !important;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        font-size: 0.7rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        border: 1px solid rgba(255,255,255,0.12);
    }

    .pill-safe { background: rgba(74, 222, 128, 0.12); color: var(--safe); border-color: rgba(74, 222, 128, 0.32); }
    .pill-warn { background: rgba(251, 191, 36, 0.12); color: var(--warn); border-color: rgba(251, 191, 36, 0.32); }
    .pill-danger { background: rgba(251, 113, 133, 0.12); color: var(--danger); border-color: rgba(251, 113, 133, 0.32); }

    .subject-card {
        background: linear-gradient(180deg, rgba(11, 20, 35, 0.9), rgba(9, 16, 27, 0.85));
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 18px;
        padding: 1rem 1rem 0.8rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 10px 20px rgba(2, 6, 23, 0.1);
    }

    .subject-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
    }

    .subject-name {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--text);
    }

    .percent-big {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.35rem;
    }

    .mini-bar {
        width: 100%;
        height: 10px;
        background: rgba(148, 163, 184, 0.12);
        border-radius: 999px;
        overflow: hidden;
        margin: 0.4rem 0 0.6rem;
    }

    .mini-bar > div {
        height: 100%;
        border-radius: inherit;
    }

    .muted-text {
        color: var(--muted);
        font-size: 0.8rem;
    }

    .metric-callout {
        background: rgba(96, 165, 250, 0.08);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 14px;
        padding: 0.65rem 0.8rem;
        margin-top: 0.35rem;
        color: var(--muted);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Core Logic (same as requested) ───────────────────────────────────────────
TARGET = 75


def bunk_calc(total, attended):
    if total == 0:
        return None
    pct = (attended / total) * 100

    bunk_count = 0
    future_total = total + 1
    while (attended / future_total) * 100 >= TARGET:
        bunk_count += 1
        future_total += 1

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


STATUS_META = {
    "safe": {"label": "Safe", "color": "#4ade80", "bg": "rgba(74, 222, 128, 0.12)"},
    "warn": {"label": "Borderline", "color": "#fbbf24", "bg": "rgba(251, 191, 36, 0.12)"},
    "danger": {"label": "Shortage", "color": "#fb7185", "bg": "rgba(251, 113, 133, 0.12)"},
}


def safe_title(value):
    return "Safe" if value >= TARGET + 5 else ("Borderline" if value >= TARGET else "Shortage")


def subject_row_to_dict(row):
    if row is None:
        return None
    subject = str(row.get("subject", "")).strip()
    total = int(row.get("total", 0) or 0)
    attended = int(row.get("attended", 0) or 0)
    if not subject or total <= 0:
        return None
    return {"subject": subject, "total": total, "attended": attended}


def render_subject_cards(results):
    for item in results:
        color = STATUS_META[item["status"]]["color"]
        width = min(max(item["pct"], 0), 100)
        if item["safe_skips"] > 0:
            message = f"You can skip <b>{item['safe_skips']}</b> more class{'es' if item['safe_skips'] != 1 else ''} safely."
        else:
            message = f"Attend <b>{item['classes_needed']}</b> consecutive class{'es' if item['classes_needed'] != 1 else ''} to recover."

        st.markdown(
            f"""
            <div class="subject-card">
                <div class="subject-header">
                    <div class="subject-name">{item['subject']}</div>
                    <span class="status-pill pill-{item['status']}">{STATUS_META[item['status']]['label']}</span>
                </div>
                <div class="percent-big" style="color: {color};">{item['pct']}%</div>
                <div class="mini-bar"><div style="width: {width}%; background: linear-gradient(90deg, {color}, #60a5fa);"></div></div>
                <div class="muted-text">{item['attended']} attended / {item['total']} total &nbsp;&nbsp;•&nbsp;&nbsp; target {TARGET}%</div>
                <div class="metric-callout">{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 BunkMeter")
    st.markdown("<div class='section-kicker'>College Attendance Predictor</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted-text'>Plan your skips, protect your attendance, and stay above the target.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    TARGET = st.slider("Minimum required %", 50, 90, 75, step=5)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    mode = st.radio("Input mode", ["Manual Entry", "Upload File"], horizontal=True)

    st.markdown("---")
    st.markdown(
        """
        <div class='muted-text'>
            Safe skips = keep increasing future total until<br>
            attendance % falls below the target.<br><br>
            Needed classes = keep adding future classes until<br>
            the attendance reaches the required threshold.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Main Header ───────────────────────────────────────────────────────────────
st.markdown("# BunkMeter 🎓")
st.markdown("<div class='section-kicker'>Smart attendance planner</div>", unsafe_allow_html=True)

# ─── Default Data ──────────────────────────────────────────────────────────────
if "rows" not in st.session_state:
    st.session_state.rows = [
        {"subject": "Mathematics", "attended": 45, "total": 56},
        {"subject": "Physics", "attended": 28, "total": 40},
        {"subject": "Chemistry", "attended": 32, "total": 38},
    ]

# ─── Manual Input ─────────────────────────────────────────────────────────────
if mode == "Manual Entry":
    st.markdown("<div class='section-kicker'>Add / edit subjects</div>", unsafe_allow_html=True)

    with st.form("add_subject_form"):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1:
            subject_name = st.text_input("Subject", placeholder="Enter subject name", label_visibility="collapsed")
        with c2:
            attended_value = st.number_input("Attended", min_value=0, max_value=500, value=0, step=1, label_visibility="collapsed")
        with c3:
            total_value = st.number_input("Total", min_value=1, max_value=500, value=30, step=1, label_visibility="collapsed")
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            add_submitted = st.form_submit_button("Add")

        if add_submitted and subject_name.strip():
            st.session_state.rows.append({
                "subject": subject_name.strip(),
                "attended": int(attended_value),
                "total": int(total_value),
            })
            st.rerun()

    if st.session_state.rows:
        df = pd.DataFrame(st.session_state.rows)
        edited_df = st.data_editor(
            df,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "subject": st.column_config.TextColumn("Subject", width="large"),
                "attended": st.column_config.NumberColumn("Attended", min_value=0, max_value=500, step=1),
                "total": st.column_config.NumberColumn("Total", min_value=1, max_value=500, step=1),
            },
        )
        cleaned = edited_df.where(pd.notna(edited_df), None)
        cleaned = cleaned.dropna(how="all")
        if not cleaned.empty:
            st.session_state.rows = cleaned.to_dict("records")
        else:
            st.session_state.rows = []

    subjects = [subject_row_to_dict(row) for row in st.session_state.rows]
    subjects = [s for s in subjects if s is not None]

# ─── Upload File ──────────────────────────────────────────────────────────────
else:
    st.markdown(
        """
        <div class='glass-panel' style='margin-bottom: 1rem; text-align: center; color: #98a9c6;'>
            Upload a CSV or Excel file with columns: <b>Subject, Attended, Total</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    template = pd.DataFrame(
        {
            "Subject": ["Mathematics", "Physics", "Chemistry"],
            "Attended": [45, 28, 32],
            "Total": [56, 40, 38],
        }
    )
    template_buffer = io.BytesIO()
    template.to_excel(template_buffer, index=False)
    st.download_button(
        "Download template",
        template_buffer.getvalue(),
        "attendance_template.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx"], label_visibility="collapsed")
    subjects = []
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            df.columns = [str(col).strip().lower() for col in df.columns]
            rename_map = {}
            for col in df.columns:
                if "sub" in col:
                    rename_map[col] = "subject"
                if "att" in col:
                    rename_map[col] = "attended"
                if "tot" in col:
                    rename_map[col] = "total"
            df = df.rename(columns=rename_map)
            if {"subject", "attended", "total"}.issubset(df.columns):
                raw_subjects = df[["subject", "attended", "total"]].to_dict("records")
                subjects = [subject_row_to_dict(row) for row in raw_subjects]
                subjects = [s for s in subjects if s is not None]
                st.success(f"Loaded {len(subjects)} subject(s) from the uploaded file.")
            else:
                st.error("Upload file must contain Subject, Attended, and Total columns.")
        except Exception as exc:
            st.error(f"Unable to read the uploaded file: {exc}")

# ─── Results Dashboard ─────────────────────────────────────────────────────────
if subjects:
    results = []
    for row in subjects:
        calc = bunk_calc(row["total"], row["attended"])
        if calc is not None:
            results.append({**row, **calc})

    if not results:
        st.warning("No valid attendance data found.")
        st.stop()

    total_attended = sum(item["attended"] for item in results)
    total_classes = sum(item["total"] for item in results)
    overall_pct = round((total_attended / total_classes) * 100, 2) if total_classes else 0
    overall_status = safe_title(overall_pct)
    overall_color = STATUS_META["safe" if overall_status == "Safe" else "warn" if overall_status == "Borderline" else "danger"]["color"]

    safe_count = sum(1 for item in results if item["status"] == "safe")
    warn_count = sum(1 for item in results if item["status"] == "warn")
    danger_count = sum(1 for item in results if item["status"] == "danger")
    total_skips = sum(item["safe_skips"] for item in results)
    total_needed = sum(item["classes_needed"] for item in results)

    st.markdown("<div class='section-kicker'>Overview</div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Overall attendance", f"{overall_pct}%", delta=f"{overall_status}")
    with k2:
        st.metric("Safe skips", total_skips, delta="across all subjects")
    with k3:
        st.metric("Classes needed", total_needed, delta=f"to reach {TARGET}%")
    with k4:
        st.metric("Subjects", len(results), delta=f"{danger_count} shortage / {warn_count} borderline")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    col_chart, col_pie = st.columns([3, 2])
    with col_chart:
        names = [item["subject"] for item in results]
        values = [item["pct"] for item in results]
        bar_colors = [STATUS_META[item["status"]]["color"] for item in results]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=names,
                y=values,
                marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
                text=[f"{v}%" for v in values],
                textposition="outside",
                textfont=dict(color="#e6edf9", size=11, family="JetBrains Mono"),
            )
        )
        fig.add_hline(
            y=TARGET,
            line_dash="dot",
            line_color="rgba(255,255,255,0.42)",
            annotation_text=f"{TARGET}% required",
            annotation_font_color="rgba(255,255,255,0.7)",
            annotation_font_size=10,
        )
        fig.update_layout(
            paper_bgcolor="#0b1628",
            plot_bgcolor="#0b1628",
            font=dict(family="Outfit", color="#ccd8ee"),
            margin=dict(t=30, r=20, b=20, l=10),
            height=330,
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)", range=[0, 110]),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

    with col_pie:
        fig_pie = go.Figure(
            go.Pie(
                labels=["Safe", "Borderline", "Shortage"],
                values=[safe_count, warn_count, danger_count],
                hole=0.55,
                marker=dict(colors=["#4ade80", "#fbbf24", "#fb7185"], line=dict(color="#0b1628", width=3)),
                textinfo="label+percent",
                textfont=dict(color="#e6edf9", family="JetBrains Mono", size=12),
            )
        )
        fig_pie.update_layout(
            paper_bgcolor="#0b1628",
            margin=dict(t=30, r=10, b=10, l=10),
            legend=dict(font=dict(size=11)),
            height=330,
            font=dict(family="Outfit", color="#ccd8ee"),
        )
        st.plotly_chart(fig_pie, width="stretch")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Insights</div>", unsafe_allow_html=True)
    skip_fig = go.Figure()
    skip_fig.add_trace(go.Bar(name="Safe skips", x=[item["subject"] for item in results], y=[item["safe_skips"] for item in results], marker_color="#4ade80"))
    skip_fig.add_trace(go.Bar(name="Classes needed", x=[item["subject"] for item in results], y=[item["classes_needed"] for item in results], marker_color="#fb7185"))
    skip_fig.update_layout(
        barmode="group",
        paper_bgcolor="#0b1628",
        plot_bgcolor="#0b1628",
        margin=dict(t=25, r=10, b=20, l=10),
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)"),
        legend=dict(font=dict(size=11)),
        font=dict(family="Outfit", color="#ccd8ee"),
    )
    st.plotly_chart(skip_fig, width="stretch")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Subject dashboard</div>", unsafe_allow_html=True)
    render_subject_cards(results)

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Export report</div>", unsafe_allow_html=True)
    export_df = pd.DataFrame(
        [
            {
                "Subject": item["subject"],
                "Attended": item["attended"],
                "Total": item["total"],
                "Attendance %": item["pct"],
                "Safe Skips": item["safe_skips"],
                "Classes Needed": item["classes_needed"],
                "Status": STATUS_META[item["status"]]["label"],
                "Date": str(date.today()),
            }
            for item in results
        ]
    )

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download CSV",
            export_df.to_csv(index=False).encode(),
            "bunkmeter_report.csv",
            "text/csv",
        )
    with c2:
        xl_buffer = io.BytesIO()
        export_df.to_excel(xl_buffer, index=False)
        st.download_button(
            "Download Excel",
            xl_buffer.getvalue(),
            "bunkmeter_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.markdown(
        """
        <div style='text-align:center; padding: 3rem 1rem; color: #98a9c6;'>
            <div style='font-size: 3rem;'>📊</div>
            <div style='font-size: 1.3rem; font-weight: 700; margin-top: 0.8rem;'>No subject data yet</div>
            <div style='margin-top: 0.4rem; font-size: 0.9rem;'>Add subjects manually or upload a file to begin tracking attendance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
