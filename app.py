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

            # -------- CHECK --------
            if "Age" in df.columns:
                df["Age_error"] = (df["Age"] < 0) | (df["Age"] > 120)

            if "Weight" in df.columns:
                df["Weight_error"] = (df["Weight"] < 0) | (df["Weight"] > 300)

            if "Gender" in df.columns:
                df["Gender_error"] = ~df["Gender"].isin(["Male", "Female"])

            if "VisitDate" in df.columns:
                df["VisitDate"] = pd.to_datetime(df["VisitDate"], errors="coerce")
                df["Date_error"] = df["VisitDate"].isnull()

            # -------- ERROR FILTER --------
            error_cols = [c for c in df.columns if "_error" in c]
            error_mask = df.isnull().any(axis=1)

            if error_cols:
                error_mask = error_mask | df[error_cols].any(axis=1)

            error_df = df[error_mask]
            clean_df = df[~error_mask]

            # -------- SUMMARY --------
            st.subheader("📊 ภาพรวมข้อมูล")

            col1, col2, col3 = st.columns(3)
            col1.metric("ทั้งหมด", len(df))
            col2.metric("ผิดพลาด", len(error_df))
            col3.metric("ถูกต้อง", len(clean_df))

            # -------- DATA QUALITY (%) --------
            st.subheader("📈 ความสมบูรณ์ของข้อมูล (%)")

            total = len(df)
            quality = []

            for col in df.columns:
                notnull = df[col].notnull().sum()
                percent = (notnull / total) * 100 if total > 0 else 0
                quality.append(percent)

            quality_df = pd.DataFrame({
                "Column": df.columns,
                "Quality (%)": quality
            })

            st.bar_chart(quality_df.set_index("Column"))

            # -------- OVERALL QUALITY --------
            overall_quality = (df.notnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            st.metric("คุณภาพข้อมูลรวม (%)", f"{overall_quality:.2f}%")

            # -------- TABLE --------
            st.subheader("📋 ตารางข้อมูล")

            def highlight_row(row):
                if row.isnull().any():
                    return ["background-color:#ffcccc"] * len(row)
                return [""] * len(row)

            st.dataframe(df.style.apply(highlight_row, axis=1))

            # -------- ERROR TABLE --------
            st.subheader("🚨 ข้อมูลที่มีปัญหา")
            st.dataframe(error_df)

            # -------- DOWNLOAD --------
            st.subheader("📥 ดาวน์โหลด")

            st.download_button(
                "📄 ทั้งหมด",
                df.to_csv(index=False),
                "all_data.csv"
            )

            st.download_button(
                "🚨 Error",
                error_df.to_csv(index=False),
                "error_data.csv"
            )

            st.download_button(
                "🧹 Clean",
                clean_df.to_csv(index=False),
                "clean_data.csv"
            )

            quality_export = quality_df.copy()

            st.download_button(
                "📊 Quality Report",
                quality_export.to_csv(index=False),
                "quality_report.csv"
            )

            # -------- ADMIN --------
            if st.session_state.role == "admin":
                st.warning("👑 Admin Mode")

        except Exception as e:
            st.error(f"❌ โหลดไฟล์ไม่ได้: {e}")
