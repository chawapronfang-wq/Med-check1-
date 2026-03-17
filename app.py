import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Medical System", layout="wide")

# ================= THEME =================
st.markdown("""
<style>
.main {background-color:#eef6fb;}

.header-box {
    background: linear-gradient(90deg,#0a3d62,#3c91e6);
    padding:20px;
    border-radius:12px;
    color:white;
    margin-bottom:20px;
}

.card {
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0px 4px 12px rgba(0,0,0,0.08);
    margin-bottom:15px;
    transition:0.3s;
}
.card:hover {transform:translateY(-5px);}

.stButton>button {
    background:#3c91e6;
    color:white;
    border-radius:10px;
    height:45px;
}

[data-testid="metric-container"] {
    background:white;
    border-radius:10px;
    padding:15px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.1);
}

.login-box {
    width:350px;
    margin:auto;
    padding:30px;
    background:white;
    border-radius:12px;
    box-shadow:0px 4px 15px rgba(0,0,0,0.1);
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ================= USERS =================
users = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "1234", "role": "user"}
}

if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
def login():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("## 🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("❌ Login failed")

    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.login:
    login()
    st.stop()

# ================= SIDEBAR =================
st.sidebar.markdown("### 🏥 MED CHECK")
menu = st.sidebar.radio("📂 เมนู", ["🏠 Home", "📊 ตรวจข้อมูล"])
st.sidebar.info("👤 User: " + st.session_state.role)

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HEADER =================
st.markdown("""
<div class="header-box">
<h2>🏥 Medical Data Quality System</h2>
</div>
""", unsafe_allow_html=True)

# ================= HOME =================
if menu == "🏠 Home":
    st.success("✅ ระบบพร้อมใช้งาน")

# ================= DATA CHECK =================
elif menu == "📊 ตรวจข้อมูล":

    file = st.file_uploader("📁 อัปโหลดไฟล์", type=["xlsx","csv"])

    if file:
        try:
            # -------- READ --------
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            df = df.replace("None", None)

            # -------- CHECK FUNCTIONS --------
            def check_range(val, min_v, max_v):
                if pd.isna(val): return "Missing"
                if val < min_v or val > max_v: return "Invalid"
                return "OK"

            def check_gender(g):
                if pd.isna(g): return "Missing"
                if g not in ["Male","Female"]: return "Invalid"
                return "OK"

            def check_date(d):
                if pd.isna(d): return "Missing"
                try:
                    pd.to_datetime(d)
                    return "OK"
                except:
                    return "Invalid"

            def check_icd(code):
                if pd.isna(code): return "Missing"
                if re.match(r"^[A-Z][0-9]{2,3}$", str(code)):
                    return "OK"
                return "Invalid"

            # -------- APPLY --------
            if "Age" in df.columns:
                df["Age_error"] = df["Age"].apply(lambda x: check_range(x,0,120))

            if "Weight" in df.columns:
                df["Weight_error"] = df["Weight"].apply(lambda x: check_range(x,1,300))

            if "Height" in df.columns:
                df["Height_error"] = df["Height"].apply(lambda x: check_range(x,50,250))

            if "Gender" in df.columns:
                df["Gender_error"] = df["Gender"].apply(check_gender)

            if "VisitDate" in df.columns:
                df["Date_error"] = df["VisitDate"].apply(check_date)

            if "DiagnosisCode" in df.columns:
                df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

            error_cols = [c for c in df.columns if "_error" in c]

            # -------- ERROR FILTER --------
            error_mask = False
            for col in error_cols:
                error_mask = error_mask | (df[col] != "OK")

            error_df = df[error_mask]
            clean_df = df[~error_mask]

            # ================= DASHBOARD =================
            st.markdown('<div class="card">', unsafe_allow_html=True)

            c1,c2,c3 = st.columns(3)
            c1.metric("ทั้งหมด", len(df))
            c2.metric("ผิดพลาด", len(error_df))
            c3.metric("ถูกต้อง", len(clean_df))

            st.markdown('</div>', unsafe_allow_html=True)

            # ================= QUALITY =================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📈 ความสมบูรณ์ของข้อมูล (%)")

            quality = {}
            for col in error_cols:
                ok = (df[col] == "OK").sum()
                quality[col] = (ok / len(df))*100 if len(df)>0 else 0

            quality_df = pd.DataFrame({
                "Column": list(quality.keys()),
                "Quality (%)": list(quality.values())
            }).sort_values(by="Quality (%)")

            st.bar_chart(quality_df.set_index("Column"))

            overall = np.mean(list(quality.values())) if quality else 0
            st.metric("คุณภาพรวม (%)", f"{overall:.2f}%")

            st.markdown('</div>', unsafe_allow_html=True)

            # ================= TABLE =================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 ตารางข้อมูล")

            def highlight(val):
                if val in ["Missing","Invalid"]:
                    return "background-color:#ff4d4d"
                return ""

            st.dataframe(df.style.applymap(highlight, subset=error_cols))
            st.markdown('</div>', unsafe_allow_html=True)

            # ================= ERROR =================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🚨 ข้อมูลที่มีปัญหา")
            st.dataframe(error_df)
            st.markdown('</div>', unsafe_allow_html=True)

            # ================= DOWNLOAD =================
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.download_button("📄 ทั้งหมด", df.to_csv(index=False), "all.csv")
            st.download_button("🚨 Error", error_df.to_csv(index=False), "error.csv")
            st.download_button("🧹 Clean", clean_df.to_csv(index=False), "clean.csv")
            st.download_button("📊 Quality", quality_df.to_csv(index=False), "quality.csv")

            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ โหลดไฟล์ไม่ได้: {e}")
