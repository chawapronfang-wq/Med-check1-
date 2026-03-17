import streamlit as st
import pandas as pd

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

# ---------------- MENU ----------------
menu = st.sidebar.radio("เมนู", ["🏠 Home", "📊 ตรวจข้อมูล"])

if menu == "🏠 Home":
    st.title("🏥 Medical Data Checker")
    st.success("ระบบพร้อมใช้งาน")

elif menu == "📊 ตรวจข้อมูล":

    st.title("📊 ตรวจสอบข้อมูล")

    file = st.file_uploader("📁 อัปโหลดไฟล์ (Excel / CSV)", type=["xlsx","csv"])

    if file:
        try:
            # -------- READ FILE --------
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.success("✅ อัปโหลดสำเร็จ")
            st.dataframe(df.head())

            # -------- LOGIC CHECK --------
            def check_logic(df):
                df = df.copy()

                if "Age" in df.columns:
                    df["Age_error"] = df["Age"] < 0

                if "Weight" in df.columns:
                    df["Weight_error"] = df["Weight"] < 0

                if "Gender" in df.columns:
                    df["Gender_error"] = ~df["Gender"].isin(["Male","Female"])

                return df

            df = check_logic(df)

            # -------- DASHBOARD --------
            st.subheader("📊 Missing ต่อคอลัมน์")
            st.bar_chart(df.isnull().sum())

            # -------- HIGHLIGHT --------
            def highlight(val):
                if pd.isnull(val):
                    return "background-color:#ff4d4d"
                return ""

            st.subheader("📋 ตารางข้อมูล")
            st.dataframe(df.style.applymap(highlight))

            # -------- ERROR FILTER --------
            error_mask = df.isnull().any(axis=1)
            error_cols = [c for c in df.columns if "_error" in c]

            if len(error_cols) > 0:
                error_mask = error_mask | df[error_cols].any(axis=1)

            error_df = df[error_mask]
            clean_df = df[~error_mask]

            st.subheader("🚨 ข้อมูลที่มีปัญหา")
            st.dataframe(error_df)

            # -------- DOWNLOAD (SAFE) --------
            st.subheader("📥 ดาวน์โหลดข้อมูล")

            st.download_button(
                "📄 ดาวน์โหลดทั้งหมด",
                df.to_csv(index=False),
                file_name="all_data.csv"
            )

            st.download_button(
                "🚨 ดาวน์โหลด Error",
                error_df.to_csv(index=False),
                file_name="error_data.csv"
            )

            st.download_button(
                "🧹 ดาวน์โหลดข้อมูลถูกต้อง",
                clean_df.to_csv(index=False),
                file_name="clean_data.csv"
            )

            # -------- SUMMARY --------
            summary = pd.DataFrame({
                "Column": df.columns,
                "Missing": df.isnull().sum().values
            })

            st.download_button(
                "📊 ดาวน์โหลด Summary",
                summary.to_csv(index=False),
                file_name="summary.csv"
            )

            # -------- QUALITY --------
            total = len(df)
            quality = []

            for col in df.columns:
                ok = df[col].notnull().sum()
                percent = (ok / total) * 100 if total > 0 else 0
                quality.append(percent)

            quality_df = pd.DataFrame({
                "Column": df.columns,
                "Quality (%)": quality
            })

            st.download_button(
                "📈 ดาวน์โหลดคุณภาพ",
                quality_df.to_csv(index=False),
                file_name="quality.csv"
            )

            # -------- ADMIN --------
            if st.session_state.role == "admin":
                st.warning("👑 Admin Mode")

        except Exception as e:
            st.error(f"❌ อ่านไฟล์ไม่ได้: {e}")
