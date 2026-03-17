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
            st.error("❌ ผิด")

if not st.session_state.login:
    login()
    st.stop()

# ---------------- MENU ----------------
menu = st.sidebar.radio("เมนู", ["Home", "ตรวจข้อมูล"])

# ---------------- HOME ----------------
if menu == "Home":
    st.title("🏥 Medical Data Checker")

# ---------------- MAIN ----------------
elif menu == "ตรวจข้อมูล":

    file = st.file_uploader("📁 อัปโหลด Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)

        # ---------------- LOGIC CHECK ----------------
        def check_logic(df):
            df = df.copy()

            if "Age" in df.columns:
                df["Age_error"] = df["Age"] < 0

            if "Weight" in df.columns:
                df["Weight_error"] = df["Weight"] < 0

            if "Gender" in df.columns:
                df["Gender_error"] = ~df["Gender"].isin(["Male", "Female"])

            return df

        df = check_logic(df)

        # ---------------- MISSING ----------------
        missing_total = df.isnull().sum().sum()
        total_cells = df.size
        complete = total_cells - missing_total

        st.subheader("📊 สัดส่วนข้อมูล")
        chart_data = pd.DataFrame({
            "Status": ["Missing", "Complete"],
            "Count": [missing_total, complete]
        })
        st.bar_chart(chart_data.set_index("Status"))

        # ---------------- HIGHLIGHT ----------------
        def highlight(val):
            if pd.isnull(val):
                return "background-color: red"
            return ""

        st.subheader("📋 ตารางข้อมูล (ไฮไลต์)")
        st.dataframe(df.style.applymap(highlight))

        # ---------------- ERROR ROW ----------------
        error_df = df[
            df.isnull().any(axis=1) |
            (df.filter(like="_error").any(axis=1))
        ]

        st.subheader("🚨 แถวที่มีปัญหา")
        st.dataframe(error_df)

        # ---------------- DOWNLOAD ----------------
        st.download_button(
            "📥 ดาวน์โหลด Error",
            error_df.to_csv(index=False),
            file_name="error.csv"
        )

        if st.session_state.role == "admin":
            st.warning("👑 Admin Mode: เห็น error ทั้งหมด")
