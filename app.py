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
.header {
    background:linear-gradient(90deg,#0f3057,#008891);
    padding:20px;border-radius:12px;color:white;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin":{"password":"1234"}}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.markdown("## 🔐 เข้าสู่ระบบ")
    u = st.text_input("ชื่อผู้ใช้")
    p = st.text_input("รหัสผ่าน", type="password")

    if st.button("เข้าสู่ระบบ"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ เข้าสู่ระบบไม่สำเร็จ")

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
st.markdown("""
<div class="header">
<h2>🏥 ระบบตรวจสอบเวชระเบียนผู้ป่วยนอก (MRA OPD)</h2>
</div>
""", unsafe_allow_html=True)

# ================= MENU =================
menu = st.sidebar.radio("📂 เมนู", ["🏠 หน้าแรก", "📊 ตรวจสอบข้อมูล"])

if st.sidebar.button("ออกจากระบบ"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "🏠 หน้าแรก":
    st.success("✅ ระบบพร้อมใช้งานสำหรับตรวจสอบเวชระเบียนผู้ป่วยนอก (MRA OPD)")

# ================= ANALYZE =================
elif menu == "📊 ตรวจสอบข้อมูล":

    file = st.file_uploader("📁 อัปโหลดไฟล์ข้อมูล (Excel / CSV)", type=["csv","xlsx"])

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
            "DiagnosisText_error":{"name":"คำวินิจฉัย","score":20},
            "Treatment_error":{"name":"การรักษา","score":20},
            "FollowUp_error":{"name":"การนัดติดตาม","score":15},
            "Doctor_error":{"name":"แพทย์","score":15}
        }

        def calc(row):
            s = 0
            for col,v in criteria.items():
                if row.get(col) == "OK":
                    s += v["score"]
            return s

        df["MRA_Score"] = df.apply(calc, axis=1)

        df["MRA_Level"] = df["MRA_Score"].apply(
            lambda x: "ดี 🟢" if x>=90 else "พอใช้ 🟡" if x>=70 else "ต้องปรับปรุง 🔴"
        )

        # ================= KPI =================
        c1,c2,c3,c4 = st.columns(4)

        c1.metric("จำนวนเคส", len(df))
        c2.metric("คะแนนเฉลี่ย", round(df["MRA_Score"].mean(),2))
        c3.metric("Error เฉลี่ย", round(df["Error_Count"].mean(),2))
        c4.metric("ผ่านเกณฑ์ (%)",
                  round(len(df[df["MRA_Level"]=="ดี 🟢"])/len(df)*100,2))

        st.bar_chart(df["MRA_Level"].value_counts())

        # ================= FILTER =================
        filtered = df.copy()

        if "Doctor" in df.columns:
            doc = st.selectbox("👨‍⚕️ เลือกแพทย์", ["ทั้งหมด"]+list(df["Doctor"].dropna().unique()))
            if doc != "ทั้งหมด":
                filtered = filtered[filtered["Doctor"]==doc]

        level = st.selectbox("📊 ระดับผลการประเมิน", ["ทั้งหมด","ดี 🟢","พอใช้ 🟡","ต้องปรับปรุง 🔴"])
        if level != "ทั้งหมด":
            filtered = filtered[filtered["MRA_Level"]==level]

        # ================= HIGHLIGHT =================
        def color_highlight(val):
            if val == "Missing":
                return "background-color:#FFD6D6;color:#B00020;font-weight:bold"
            if val == "Invalid":
                return "background-color:#FFE5B4;color:#8A4B00;font-weight:bold"
            if val == "OK":
                return "background-color:#D4F8D4;color:#0B6B0B;font-weight:bold"
            return ""

        st.markdown("## 🔍 ตารางตรวจสอบข้อมูล")

        st.dataframe(
            filtered.style.map(color_highlight, subset=error_cols),
            use_container_width=True
        )

        # ================= CASE DETAIL =================
        st.markdown("## 🧾 รายละเอียดรายเคส")

        idx = st.selectbox("เลือกเคส", filtered.index)
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

        st.write(f"📊 คะแนน: {got}/{total} ({(got/total*100):.2f}%)")
        st.dataframe(pd.DataFrame(detail, columns=["หัวข้อ","คะแนนเต็ม","คะแนนที่ได้","สถานะ"]))

        # ================= PDF =================
        def export_pdf(detail, got, total):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer)

            styles = getSampleStyleSheet()
            content = []

            content.append(Paragraph("รายงาน MRA OPD", styles["Title"]))
            content.append(Paragraph(f"วันที่: {datetime.now()}", styles["Normal"]))
            content.append(Spacer(1, 10))

            table = [["หัวข้อ","เต็ม","ได้","สถานะ"]] + detail

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

        if st.button("📄 ออกรายงาน PDF"):
            pdf = export_pdf(detail, got, total)
            st.download_button("ดาวน์โหลด PDF", pdf, "mra_report.pdf")

        # ================= EXCEL =================
        def export_excel(df):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="ข้อมูล", index=False)
            buffer.seek(0)
            return buffer

        if st.button("📊 ออก Excel"):
            xls = export_excel(df)
            st.download_button("ดาวน์โหลด Excel", xls, "mra.xlsx")

        # ================= SAVE DB =================
        if st.button("💾 บันทึกลงฐานข้อมูล"):
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
            st.success("บันทึกสำเร็จ")
