import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Medical System", layout="wide")

# ================= THEME =================
st.markdown("""
<style>
.main {background-color:#eef6fb;}
.card {background:white;padding:20px;border-radius:12px;margin-bottom:15px;}
.login-box {width:350px;margin:auto;padding:30px;background:white;border-radius:12px;text-align:center;}
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
            st.error("Login failed")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.login:
    login()
    st.stop()

# ================= SIDEBAR =================
menu = st.sidebar.radio("📂 เมนู", ["🏠 Home", "📊 ตรวจข้อมูล"])
st.sidebar.info("👤 " + st.session_state.role)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "🏠 Home":
    st.success("✅ System Ready")

# ================= DATA CHECK =================
elif menu == "📊 ตรวจข้อมูล":

    file = st.file_uploader("📁 Upload", type=["xlsx","csv"])

    if file:
        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            df = df.replace("None", None)

            # ===== CHECK FUNCTIONS =====
            def check_range(v, a, b):
                if pd.isna(v): return "Missing"
                if v < a or v > b: return "Invalid"
                return "OK"

            def check_text(v):
                if pd.isna(v): return "Missing"
                if len(str(v)) < 3: return "Invalid"
                return "OK"

            def check_icd(v):
                if pd.isna(v): return "Missing"
                if re.match(r"^[A-Z][0-9]{2,3}$", str(v)):
                    return "OK"
                return "Invalid"

            # ===== APPLY SAFE =====
            if "Age" in df: df["Age_error"] = df["Age"].apply(lambda x: check_range(x,0,120))
            if "DiagnosisCode" in df: df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)
            if "DiagnosisText" in df: df["DiagnosisText_error"] = df["DiagnosisText"].apply(check_text)
            if "Treatment" in df: df["Treatment_error"] = df["Treatment"].apply(check_text)
            if "FollowUp" in df: df["FollowUp_error"] = df["FollowUp"].apply(check_text)
            if "Doctor" in df: df["Doctor_error"] = df["Doctor"].apply(check_text)

            error_cols = [c for c in df.columns if "_error" in c]

            # ===== MRA SCORE =====
            weights = {
                "Diagnosis_error": 0.3,
                "DiagnosisText_error": 0.2,
                "Treatment_error": 0.2,
                "FollowUp_error": 0.15,
                "Doctor_error": 0.15
            }

            def calc(row):
                s,t = 0,0
                for col,w in weights.items():
                    if col in row:
                        v = row[col]
                        if v != "Missing":
                            t += w
                            if v == "OK": s += w
                return (s/t)*100 if t else 0

            df["MRA_Score"] = df.apply(calc, axis=1)
            df["MRA_Level"] = df["MRA_Score"].apply(lambda x: "Good 🟢" if x>=90 else "Fair 🟡" if x>=70 else "Poor 🔴")

            # ===== DASHBOARD =====
            st.metric("Total", len(df))
            st.metric("Avg Score", f"{df['MRA_Score'].mean():.2f}%")
            st.bar_chart(df["MRA_Level"].value_counts())

            # ===== TABLE =====
            st.dataframe(df)

            # ===== DOWNLOAD =====
            st.download_button("📄 All", df.to_csv(index=False), "all.csv")

        except Exception as e:
            st.error(f"❌ {e}")
