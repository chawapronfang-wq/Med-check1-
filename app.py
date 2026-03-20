import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

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
.good {color:green;font-weight:bold;}
.fair {color:orange;font-weight:bold;}
.poor {color:red;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown('<div class="header"><h2>🏥 ระบบตรวจสอบเวชระเบียน (MRA OPD)</h2></div>', unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin": "1234", "user": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.subheader("🔐 เข้าสู่ระบบ")
    u = st.text_input("ชื่อผู้ใช้")
    p = st.text_input("รหัสผ่าน", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ เข้าสู่ระบบไม่สำเร็จ")

if not st.session_state.login:
    login()
    st.stop()

# ================= MENU =================
menu = st.sidebar.radio("📂 เมนู", ["🏠 หน้าแรก", "📊 ตรวจข้อมูล"])

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "🏠 หน้าแรก":
    st.success("✅ ระบบพร้อมใช้งาน")

# ================= DATA CHECK =================
elif menu == "📊 ตรวจข้อมูล":

    file = st.file_uploader("📁 อัปโหลดไฟล์ (CSV / Excel)", type=["csv", "xlsx"])

    if file:

        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

        # ================= CHECK FUNCTIONS =================
        def check_range(v, a, b):
            if pd.isna(v):
                return "Missing"
            if v < a or v > b:
                return "Invalid"
            return "OK"

        def check_text(v):
            if pd.isna(v):
                return "Missing"
            if len(str(v)) < 3:
                return "Invalid"
            return "OK"

        def check_icd(v):
            if pd.isna(v):
                return "Missing"
            return "OK" if re.match(r"^[A-Z][0-9]{2,3}$", str(v)) else "Invalid"

        # ================= APPLY RULES =================
        if "Age" in df:
            df["Age_error"] = df["Age"].apply(lambda x: check_range(x, 0, 120))

        if "DiagnosisCode" in df:
            df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

        if "DiagnosisText" in df:
            df["DiagnosisText_error"] = df["DiagnosisText"].apply(check_text)

        if "Treatment" in df:
            df["Treatment_error"] = df["Treatment"].apply(check_text)

        if "FollowUp" in df:
            df["FollowUp_error"] = df["FollowUp"].apply(check_text)

        if "Doctor" in df:
            df["Doctor_error"] = df["Doctor"].apply(check_text)

        # ================= ERROR COL =================
        error_cols = [c for c in df.columns if "_error" in c]

        # ================= COUNT ERROR =================
        df["Error_Count"] = df[error_cols].apply(lambda r: sum(v != "OK" for v in r), axis=1)

        # ================= SCORE =================
        criteria = {
            "Diagnosis_error": 30,
            "DiagnosisText_error": 20,
            "Treatment_error": 20,
            "FollowUp_error": 15,
            "Doctor_error": 15
        }

        def calc(row):
            score = 100
            for col in criteria:
                if col in row and row[col] != "OK":
                    score -= criteria[col]
            return max(score, 0)

        df["MRA_Score"] = df.apply(calc, axis=1)

        df["MRA_Level"] = df["MRA_Score"].apply(
            lambda x: "ดี 🟢" if x >= 90 else "พอใช้ 🟡" if x >= 70 else "ต้องแก้ไข 🔴"
        )

        # ================= FILTER =================
        level = st.selectbox("📊 เลือกระดับ", ["All", "ดี 🟢", "พอใช้ 🟡", "ต้องแก้ไข 🔴"])

        filtered = df.copy()
        if level != "All":
            filtered = filtered[filtered["MRA_Level"] == level]

        # ================= DASHBOARD =================
        c1, c2, c3 = st.columns(3)
        c1.metric("📄 จำนวนเคส", len(filtered))
        c2.metric("📊 คะแนนเฉลี่ย", f"{filtered['MRA_Score'].mean():.2f}")
        c3.metric("⚠️ Error เฉลี่ย", f"{filtered['Error_Count'].mean():.2f}")

        st.bar_chart(filtered["MRA_Level"].value_counts())

        # ================= CASE DETAIL =================
        st.markdown("## 🔍 วิเคราะห์รายเคส")

        idx = st.selectbox("เลือกเคส", filtered.index)
        case = filtered.loc[idx]

        st.write("### 🧾 รายละเอียดเคส")
        st.json(case.to_dict())

        # ================= COLOR HIGHLIGHT TABLE =================
        def color(v):
            if v == "Missing":
                return "background-color:orange;color:white"
            if v == "Invalid":
                return "background-color:red;color:white"
            return "background-color:#e8f5e9"

        st.markdown("## 🎯 ตาราง Error Highlight")

        st.dataframe(
            filtered.style.applymap(color, subset=error_cols),
            use_container_width=True
        )

        # ================= RANKING =================
        st.markdown("## 🏆 Ranking")

        st.dataframe(filtered.sort_values("MRA_Score", ascending=False).head(10))
        st.dataframe(filtered.sort_values("MRA_Score").head(10))

        # ================= PDF EXPORT =================
        def export_pdf():
            doc = SimpleDocTemplate("mra_report.pdf")
            styles = getSampleStyleSheet()

            content = []
            content.append(Paragraph("รายงานตรวจสอบเวชระเบียน MRA OPD", styles["Title"]))
            content.append(Spacer(1, 10))

            table_data = [["หัวข้อ", "คะแนนเต็ม", "ได้", "สถานะ"]]

            for col in criteria:
                if col in case:
                    full = criteria[col]
                    score = full if case[col] == "OK" else 0
                    table_data.append([col, full, score, case[col]])

            content.append(Table(table_data))
            doc.build(content)

        if st.button("📄 Export PDF"):
            export_pdf()
            with open("mra_report.pdf", "rb") as f:
                st.download_button("⬇️ ดาวน์โหลด PDF", f, file_name="MRA_Report.pdf")
