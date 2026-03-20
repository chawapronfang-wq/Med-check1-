import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

st.set_page_config(page_title="MRA OPD SYSTEM", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.main {background-color:#f4f8fb;}
.header {
    background:linear-gradient(90deg,#0f3057,#008891);
    padding:22px;
    border-radius:14px;
    color:white;
    font-size:22px;
}
.card {
    background:white;
    padding:15px;
    border-radius:12px;
    box-shadow:0px 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown('<div class="header">🏥 MRA OPD SYSTEM (Hospital Quality Audit)</div>', unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.subheader("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Login failed")

if not st.session_state.login:
    login()
    st.stop()

# ================= UPLOAD =================
file = st.file_uploader("📁 Upload OPD File", type=["csv","xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

    # ================= CHECK FUNCTIONS =================
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

    # ================= APPLY =================
    criteria = {}

    if "DiagnosisCode" in df:
        df["ICD"] = df["DiagnosisCode"].apply(check_icd)
        criteria["ICD"] = 50

    if "DiagnosisText" in df:
        df["TEXT"] = df["DiagnosisText"].apply(check_text)
        criteria["TEXT"] = 50

    status_cols = list(criteria.keys())

    # ================= SCORE =================
    def calc(row):
        full = len(status_cols) * 50
        got = sum(50 for c in status_cols if row.get(c) == "OK")
        percent = (got / full * 100) if full > 0 else 0
        return pd.Series([full, got, percent])

    df[["คะแนนเต็ม", "คะแนนได้", "เปอร์เซ็นต์"]] = df.apply(calc, axis=1)

    # ================= LEVEL =================
    def level(x):
        if x >= 90:
            return "ดี 🟢"
        elif x >= 70:
            return "พอใช้ 🟡"
        else:
            return "ต้องแก้ไข 🔴"

    df["ระดับ"] = df["เปอร์เซ็นต์"].apply(level)

    # ================= FILTER =================
    level_filter = st.selectbox("📊 เลือกระดับ", ["ทั้งหมด","ดี 🟢","พอใช้ 🟡","ต้องแก้ไข 🔴"])

    show = df.copy()
    if level_filter != "ทั้งหมด":
        show = show[show["ระดับ"] == level_filter]

    # ================= DASHBOARD =================
    c1, c2, c3 = st.columns(3)

    c1.metric("จำนวนเคส", len(show))
    c2.metric("คะแนนเฉลี่ย", f"{show['คะแนนได้'].mean():.2f}")
    c3.metric("% คุณภาพ", f"{show['เปอร์เซ็นต์'].mean():.2f}")

    st.bar_chart(show["ระดับ"].value_counts())

    # ================= ROW COLOR =================
    def row_color(row):
        if row["ระดับ"] == "ดี 🟢":
            return ["background-color:#d4edda"] * len(row)
        elif row["ระดับ"] == "พอใช้ 🟡":
            return ["background-color:#fff3cd"] * len(row)
        else:
            return ["background-color:#f8d7da"] * len(row)

    st.markdown("## 📋 ตารางตรวจสอบ")

    st.dataframe(show.style.apply(row_color, axis=1), use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 รายละเอียดเคส")

    idx = st.selectbox("เลือกเคส", show.index)
    st.write(show.loc[idx])

    # ================= STATUS TEXT =================
    st.markdown("## 🧾 สถานะข้อมูล")

    def status(v):
        if v == "Missing":
            return "❗ ข้อมูลหาย (ควรแก้ไข)"
        if v == "Invalid":
            return "⚠️ รูปแบบไม่ถูกต้อง"
        if v == "OK":
            return "✅ ถูกต้อง"
        return "ไม่อยู่ในเกณฑ์ประเมิน"

    for c in status_cols:
        st.write(f"{c}: {status(show.loc[idx, c])}")

    # ================= EXPORT EXCEL PRO =================
    def export_excel(df):

        output = io.BytesIO()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error = df[df["ระดับ"] != "ดี 🟢"]

        summary = pd.DataFrame({
            "รายการ": [
                "จำนวนเคส",
                "คะแนนเฉลี่ย",
                "เปอร์เซ็นต์เฉลี่ย",
                "Good",
                "Fair",
                "Poor",
                "Export Date"
            ],
            "ค่า": [
                len(df),
                df["คะแนนได้"].mean(),
                df["เปอร์เซ็นต์"].mean(),
                len(df[df["ระดับ"] == "ดี 🟢"]),
                len(df[df["ระดับ"] == "พอใช้ 🟡"]),
                len(df[df["ระดับ"] == "ต้องแก้ไข 🔴"]),
                now
            ]
        })

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="All_Data")
            error.to_excel(writer, index=False, sheet_name="Error_Cases")
            summary.to_excel(writer, index=False, sheet_name="Summary")

        return output.getvalue()

    st.markdown("## 📤 Export Report")

    st.download_button(
        "⬇️ ดาวน์โหลด MRA OPD Report",
        data=export_excel(show),
        file_name=f"MRA_OPD_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
