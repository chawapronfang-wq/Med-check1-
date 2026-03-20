import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Medical System", layout="wide")

# ================= UI (PINK THEME) =================
st.markdown("""
<style>
.main {background: linear-gradient(180deg,#f8d7e3,#fbe9f1);}

.navbar {
    display:flex; justify-content:space-between;
    padding:15px 40px; background:white;
    border-radius:20px; margin:20px;
}
.logo {color:#ff4da6; font-weight:bold; font-size:20px;}
.menu a {margin:0 10px; color:#444; text-decoration:none;}
.app-btn {background:#ff4da6;color:white;padding:8px 15px;border-radius:8px;}

.hero-box {background:white;border-radius:25px;margin:20px;padding:40px;}
.hero {display:flex;justify-content:space-between;align-items:center;}
.hero-text h1 {font-size:40px;}
.hero-btn {background:#ff4da6;color:white;padding:10px 20px;border-radius:8px;}

.features {display:flex;justify-content:space-around;margin-top:40px;background:#fde4ee;padding:20px;border-radius:15px;}

#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <div class="logo">💗 BeHealthy</div>
    <div class="menu">
        <a>Home</a><a>About</a><a>Service</a>
        <a>Blog</a><a>Contact</a>
        <span class="app-btn">APPOINTMENT</span>
    </div>
</div>

<div class="hero-box">
    <div class="hero">
        <div class="hero-text">
            <small style="color:#ff4da6;">BE HEALTHY</small>
            <h1>Renew Vitality<br>Is Within Reach</h1>
            <p>Medical Record Audit System (MRA) สำหรับตรวจคุณภาพข้อมูล</p>
            <div class="hero-btn">START</div>
        </div>
        <img src="https://images.unsplash.com/photo-1607746882042-944635dfe10e" width="250">
    </div>

    <div class="features">
        <div>📅 Schedule</div>
        <div>🧠 Smart Check</div>
        <div>💪 Data Quality</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= USERS =================
users = {"admin":{"password":"1234","role":"admin"},"user":{"password":"1234","role":"user"}}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
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

if not st.session_state.login:
    login()
    st.stop()

# ================= SIDEBAR =================
st.sidebar.markdown("### 🏥 MED CHECK")
menu = st.sidebar.radio("📂 เมนู", ["🏠 Home","📊 ตรวจข้อมูล"])
st.sidebar.info("👤 " + st.session_state.role)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "🏠 Home":
    st.success("ระบบพร้อมใช้งาน (System Ready)")

# ================= DATA CHECK =================
elif menu == "📊 ตรวจข้อมูล":

    file = st.file_uploader("📁 Upload file", type=["xlsx","csv"])

    if file:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        df = df.replace("None", None)

        # ===== CHECK FUNCTIONS =====
        def check_range(val, min_v, max_v):
            if pd.isna(val): return "Missing"
            if val < min_v or val > max_v: return "Invalid"
            return "OK"

        def check_icd(code):
            if pd.isna(code): return "Missing"
            if re.match(r"^[A-Z][0-9]{2,3}$", str(code)):
                return "OK"
            return "Invalid"

        def check_text(x):
            if pd.isna(x): return "Missing"
            if len(str(x)) < 3: return "Invalid"
            return "OK"

        # ===== APPLY =====
        if "Age" in df.columns:
            df["Age_error"] = df["Age"].apply(lambda x: check_range(x,0,120))

        if "DiagnosisCode" in df.columns:
            df["Diag_error"] = df["DiagnosisCode"].apply(check_icd)

        if "DiagnosisText" in df.columns:
            df["DiagText_error"] = df["DiagnosisText"].apply(check_text)

        if "FollowUp" in df.columns:
            df["Follow_error"] = df["FollowUp"].apply(check_text)

        error_cols = [c for c in df.columns if "_error" in c]

        # ===== MRA SCORE =====
        def calculate_score(row):
            total, ok = 0, 0
            for col in error_cols:
                val = row[col]
                if val != "Missing":
                    total += 1
                    if val == "OK":
                        ok += 1
            return (ok/total)*100 if total else 0

        df["MRA_Score"] = df.apply(calculate_score, axis=1)

        def level(s):
            return "Good 🟢" if s>=90 else "Fair 🟡" if s>=70 else "Poor 🔴"

        df["Level"] = df["MRA_Score"].apply(level)

        # ===== DASHBOARD =====
        st.subheader("📊 Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Avg Score", f"{df['MRA_Score'].mean():.2f}%")
        c3.metric("Good", (df["Level"]=="Good 🟢").sum())

        # ===== GRAPH =====
        quality = {}
        for col in error_cols:
            quality[col] = (df[col]=="OK").mean()*100

        quality_df = pd.DataFrame({"Column":quality.keys(),"Quality":quality.values()})
        st.bar_chart(quality_df.set_index("Column"))

        # ===== TABLE =====
        st.subheader("📋 Data")
        st.dataframe(df)

        # ===== DOWNLOAD =====
        st.download_button("📥 Download All", df.to_csv(index=False), "all.csv")
        st.download_button("📊 MRA Score", df.to_csv(index=False), "mra_score.csv")
