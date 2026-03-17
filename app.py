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

    # ---------------- FILE UPLOAD ----------------
    file = st.file_uploader("📁 อัปโหลดไฟล์ (Excel / CSV)", type=["xlsx","csv"])

    if file:
        try:
            # ---------- READ FILE ----------
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.success("✅ อัปโหลดไฟล์สำเร็จ")
            st.subheader("📋 ตัวอย่างข้อมูล")
            st.dataframe(df.head())

            # ---------- LOGIC CHECK ----------
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

            # ---------- MISSING ----------
            missing = df.isnull().sum()
            st.subheader("📊 Missing ต่อคอลัมน์")
            st.bar_chart(missing)

            # ---------- HIGHLIGHT ----------
            def highlight(val):
                if pd.isnull(val):
                    return "background-color: #ff4d4d"
                return ""

            st.subheader("📋 ตาราง (Highlight ช่องพัง)")
            st.dataframe(df.style.applymap(highlight))

            # ---------- ERROR ROW ----------
            error_df = df[
                df.isnull().any(axis=1) |
                (df.filter(like="_error").any(axis=1))
            ]

            st.subheader("🚨 แถวที่มีปัญหา")
            st.dataframe(error_df)

            # ---------- DOWNLOAD ----------
            st.download_button(
                "📥 ดาวน์โหลด Error",
                error_df.to_csv(index=False),
                file_name="error.csv"
            )

            # ---------- ADMIN ----------
            if st.session_state.role == "admin":
                st.warning("👑 Admin Mode")

        except Exception as e:
            st.error(f"❌ อ่านไฟล์ไม่ได้: {e}")
