import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Medical Checker", layout="wide")

# ---------------- LOGIN ----------------
users = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "1234", "role": "user"}
}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.title("🔐 เข้าสู่ระบบ")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านผิด")

if not st.session_state.login:
    login()
    st.stop()

# ---------------- UI ----------------
st.markdown("## 🏥 ระบบตรวจสอบคุณภาพข้อมูลผู้ป่วย")
st.caption("Medical Data Quality Dashboard")

menu = st.sidebar.radio("เมนู", ["🏠 Home", "📊 ตรวจข้อมูล"])

if menu == "🏠 Home":
    st.success("✅ ระบบพร้อมใช้งาน")

elif menu == "📊 ตรวจข้อมูล":

    st.title("📊 ตรวจสอบข้อมูล")

    file = st.file_uploader("📁 อัปโหลดไฟล์ (Excel / CSV)", type=["xlsx","csv"])

    if file:
        try:
            # -------- READ --------
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            df = df.replace("None", None)

            st.success("✅ อัปโหลดสำเร็จ")

            # -------- CHECK FUNCTION --------
            def check_icd(code):
                if pd.isna(code):
                    return "Missing"
                if re.match(r"^[A-Z][0-9]{2,3}$", str(code)):
                    return "OK"
                return "Invalid"

            def check_range(val, min_v, max_v):
                if pd.isna(val):
                    return "Missing"
                if val < min_v or val > max_v:
                    return "Invalid"
                return "OK"

            def check_gender(g):
                if pd.isna(g):
                    return "Missing"
                if g not in ["Male", "Female"]:
                    return "Invalid"
                return "OK"

            def check_date(d):
                if pd.isna(d):
                    return "Missing"
                try:
                    pd.to_datetime(d)
                    return "OK"
                except:
                    return "Invalid"

            # -------- APPLY CHECK --------
            if "Age" in df.columns:
                df["Age_error"] = df["Age"].apply(lambda x: check_range(x, 0, 120))

            if "Weight" in df.columns:
                df["Weight_error"] = df["Weight"].apply(lambda x: check_range(x, 1, 300))

            if "Height" in df.columns:
                df["Height_error"] = df["Height"].apply(lambda x: check_range(x, 50, 250))

            if "Gender" in df.columns:
                df["Gender_error"] = df["Gender"].apply(check_gender)

            if "VisitDate" in df.columns:
                df["Date_error"] = df["VisitDate"].apply(check_date)

            if "DiagnosisCode" in df.columns:
                df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

            # -------- ERROR FILTER --------
            error_cols = [c for c in df.columns if "_error" in c]

            error_mask = False
            for col in error_cols:
                error_mask = error_mask | (df[col] != "OK")

            error_df = df[error_mask]
            clean_df = df[~error_mask]

            # -------- SUMMARY --------
            st.subheader("📊 ภาพรวมข้อมูล")

            col1, col2, col3 = st.columns(3)
            col1.metric("ทั้งหมด", len(df))
            col2.metric("ผิดพลาด", len(error_df))
            col3.metric("ถูกต้อง", len(clean_df))

            # -------- QUALITY --------
            st.subheader("📈 ความสมบูรณ์ของข้อมูล (%)")

            quality = {}
            for col in error_cols:
                ok = (df[col] == "OK").sum()
                quality[col] = (ok / len(df)) * 100 if len(df) > 0 else 0

            quality_df = pd.DataFrame({
                "Column": list(quality.keys()),
                "Quality (%)": list(quality.values())
            }).sort_values(by="Quality (%)")

            st.bar_chart(quality_df.set_index("Column"))

            # -------- OVERALL --------
            overall = np.mean(list(quality.values())) if quality else 0
            st.metric("คุณภาพข้อมูลรวม (%)", f"{overall:.2f}%")

            # -------- TABLE --------
            st.subheader("📋 ตารางข้อมูล")

            def highlight(val):
                if val in ["Missing", "Invalid"]:
                    return "background-color:#ff4d4d"
                return ""

            st.dataframe(df.style.applymap(highlight, subset=error_cols))

            # -------- ERROR TABLE --------
            st.subheader("🚨 ข้อมูลที่มีปัญหา")
            st.dataframe(error_df)

            # -------- DOWNLOAD --------
            st.subheader("📥 ดาวน์โหลด")

            st.download_button("📄 ทั้งหมด", df.to_csv(index=False), "all_data.csv")
            st.download_button("🚨 Error", error_df.to_csv(index=False), "error_data.csv")
            st.download_button("🧹 Clean", clean_df.to_csv(index=False), "clean_data.csv")
            st.download_button("📊 Quality Report", quality_df.to_csv(index=False), "quality_report.csv")

            # -------- ADMIN --------
            if st.session_state.role == "admin":
                st.warning("👑 Admin Mode")

        except Exception as e:
            st.error(f"❌ โหลดไฟล์ไม่ได้: {e}")
