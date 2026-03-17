import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Medical Data Checker", layout="wide")

# ------------------ LOGIN SYSTEM ------------------
users = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "1234", "role": "user"}
}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.login = True
            st.session_state.role = users[username]["role"]
            st.success("เข้าสู่ระบบสำเร็จ")
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านผิด")

if not st.session_state.login:
    login()
    st.stop()

# ------------------ SIDEBAR ------------------
menu = st.sidebar.radio("เมนู", ["🏠 Home", "📊 ตรวจข้อมูล", "ℹ️ About"])

# ------------------ HOME ------------------
if menu == "🏠 Home":
    st.title("🏥 Medical Data Checker")
    st.write("ระบบตรวจสอบความถูกต้องของข้อมูลสุขภาพ")
    st.info("อัปโหลดไฟล์ Excel เพื่อตรวจสอบ Missing / Error")

# ------------------ ABOUT ------------------
elif menu == "ℹ️ About":
    st.title("ℹ️ เกี่ยวกับระบบ")
    st.write("""
    ระบบนี้ใช้สำหรับ:
    - ตรวจสอบข้อมูลผู้ป่วย
    - หา Missing Data
    - สรุป Error
    """)

# ------------------ MAIN APP ------------------
elif menu == "📊 ตรวจข้อมูล":

    st.title("📊 ตรวจสอบข้อมูล")

    uploaded_file = st.file_uploader("📁 อัปโหลดไฟล์ Excel", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.subheader("📋 ข้อมูลตัวอย่าง")
        st.dataframe(df.head())

        # ------------------ CHECK MISSING ------------------
        missing = df.isnull().sum()

        # ------------------ PIE CHART ------------------
        st.subheader("📊 สัดส่วน Missing Data")

        fig1, ax1 = plt.subplots()
        ax1.pie(missing, labels=missing.index, autopct='%1.1f%%')
        st.pyplot(fig1)

        # ------------------ BAR CHART ------------------
        st.subheader("📊 จำนวน Missing ต่อคอลัมน์")

        fig2, ax2 = plt.subplots()
        ax2.bar(missing.index, missing.values)
        plt.xticks(rotation=45)
        st.pyplot(fig2)

        # ------------------ ERROR TABLE ------------------
        st.subheader("🚨 แถวที่มี Missing")
        error_df = df[df.isnull().any(axis=1)]
        st.dataframe(error_df)

        # ------------------ DOWNLOAD ------------------
        st.download_button(
            "📥 ดาวน์โหลดข้อมูล Error",
            error_df.to_csv(index=False),
            file_name="error_data.csv"
        )

        # ------------------ ROLE CONTROL ------------------
        if st.session_state.role == "admin":
            st.warning("👑 คุณเป็น Admin สามารถเห็นข้อมูลทั้งหมด")
