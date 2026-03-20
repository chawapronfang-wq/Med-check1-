import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
from datetime import datetime
import sqlite3

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ================= CONFIG =================
st.set_page_config(page_title="MRA OPD", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.main {background-color:#f4f8fb;}
.header {background:linear-gradient(90deg,#0f3057,#008891);padding:20px;border-radius:12px;color:white;}
.card {background:white;padding:18px;border-radius:12px;margin-bottom:15px;box-shadow:0px 4px 12px rgba(0,0,0,0.08);}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin":{"password":"1234"}}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.markdown("## 🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Login failed")

if not st.session_state.login:
    login()
    st.stop()

# ================= DB =================
conn = sqlite3.connect("mra.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS mra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor TEXT,
    score REAL,
    error_count INTEGER,
    level TEXT
)
""")
conn.commit()

# ================= HEADER =================
st.markdown('<div class="header"><h2>🏥 MRA OPD SYSTEM</h2></div>', unsafe_allow_html=True)

menu = st.sidebar.radio("📂 Menu", ["🏠 Home", "📊 Analyze"])

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "🏠 Home":
    st.success("ระบบพร้อมใช้งาน")

# ================= ANALYZE =================
elif menu == "📊 Analyze":

    file = st.file_uploader("Upload file", type=["csv", "xlsx"])

    if file:

        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

        # ================= CHECK FUNCTIONS =================
        def check_range(v,a,b):
            if pd.isna(v): return "Missing"
            if v<a or v>b: return "Invalid"
            return "OK"

        def check_text(v):
            if pd.isna(v): return "Missing"
            if len(str(v))<3: return "Invalid"
            return "OK"

        def check_icd(v):
            if pd.isna(v): return "Missing"
            if re.match(r"^[A-Z][0-9]{2,3}$", str(v)): return "OK"
            return "Invalid"

        # ================= VALIDATION =================
        if "Age" in df.columns:
            df["Age_error"] = df["Age"].apply(lambda x: check_range(x,0,120))

        if "DiagnosisCode" in df.columns:
            df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

        if "DiagnosisText" in df.columns:
            df["DiagnosisText_error"] = df["DiagnosisText"].apply(check_text)

        if "Treatment" in df.columns:
            df["Treatment_error"] = df["Treatment"].apply(check_text)

        if "FollowUp" in df.columns:
            df["FollowUp_error"] = df["FollowUp"].apply(check_text)

        if "Doctor" in df.columns:
            df["Doctor_error"] = df["Doctor"].apply(check_text)

        error_cols = [c for c in df.columns if "_error" in c]

        df["Error_Count"] = df[error_cols].apply(lambda r: sum(v!="OK" for v in r), axis=1)

        # ================= SCORE =================
        criteria = {
            "Diagnosis_error":{"name":"ICD-10","score":30},
            "DiagnosisText_error":{"name":"Diagnosis","score":20},
            "Treatment_error":{"name":"Treatment","score":20},
            "FollowUp_error":{"name":"FollowUp","score":15},
            "Doctor_error":{"name":"Doctor","score":15}
        }

        def calc(row):
            s = 0
            for col,v in criteria.items():
                if row.get(col) == "OK":
                    s += v["score"]
            return s

        df["MRA_Score"] = df.apply(calc, axis=1)

        df["MRA_Level"] = df["MRA_Score"].apply(
            lambda x: "Good 🟢" if x>=90 else "Fair 🟡" if x>=70 else "Poor 🔴"
        )

        # ================= KPI =================
        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Cases", len(df))
        c2.metric("Avg Score", round(df["MRA_Score"].mean(),2))
        c3.metric("Error Avg", round(df["Error_Count"].mean(),2))
        c4.metric("Good %", round(len(df[df["MRA_Level"]=="Good 🟢"])/len(df)*100,2))

        st.bar_chart(df["MRA_Level"].value_counts())

        # ================= FILTER =================
        filtered = df.copy()

        if "Doctor" in df.columns:
            doc = st.selectbox("Doctor", ["All"]+list(df["Doctor"].dropna().unique()))
            if doc!="All":
                filtered = filtered[filtered["Doctor"]==doc]

        level = st.selectbox("Level", ["All","Good 🟢","Fair 🟡","Poor 🔴"])
        if level!="All":
            filtered = filtered[filtered["MRA_Level"]==level]

        # ================= CASE =================
        st.markdown("## Case Detail")

        idx = st.selectbox("Select Case", filtered.index)
        case = filtered.loc[idx]

        detail = []
        total = 0
        got = 0

        for col,v in criteria.items():
            if col in case:
                total += v["score"]
                score = v["score"] if case[col]=="OK" else 0
                got += score
                detail.append([v["name"], v["score"], score, case[col]])

        st.write(f"Score: {got}/{total} ({(got/total*100):.2f}%)")
        st.dataframe(pd.DataFrame(detail, columns=["Item","Full","Got","Status"]))

        # ================= EXPORT PDF =================
        def export_pdf(detail, got, total):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer)

            styles = getSampleStyleSheet()
            content = []

            content.append(Paragraph("MRA OPD REPORT", styles["Title"]))
            content.append(Paragraph(f"Date: {datetime.now()}", styles["Normal"]))
            content.append(Spacer(1, 10))

            table = [["Item","Full","Got","Status"]] + detail

            t = Table(table)
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.grey),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("GRID",(0,0),(-1,-1),0.5,colors.black)
            ]))

            content.append(t)
            doc.build(content)

            buffer.seek(0)
            return buffer

        if st.button("Export PDF"):
            pdf = export_pdf(detail, got, total)
            st.download_button("Download PDF", pdf, "mra_report.pdf")

        # ================= EXPORT EXCEL =================
        def export_excel(df):
            buffer = BytesIO()

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)

            buffer.seek(0)
            return buffer

        if st.button("Export Excel"):
            xls = export_excel(df)
            st.download_button("Download Excel", xls, "mra.xlsx")

        # ================= SAVE DB =================
        if st.button("Save to DB"):
            for _, r in df.iterrows():
                c.execute("""
                INSERT INTO mra (doctor, score, error_count, level)
                VALUES (?, ?, ?, ?)
                """, (
                    r.get("Doctor",""),
                    r["MRA_Score"],
                    r["Error_Count"],
                    r["MRA_Level"]
                ))
            conn.commit()
            st.success("Saved")
