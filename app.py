import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="MRA OPD", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.main {background-color:#f4f8fb;}
.header {
    background:linear-gradient(90deg,#0f3057,#008891);
    padding:20px;border-radius:12px;color:white;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown('<div class="header"><h2>🏥 ระบบตรวจสอบเวชระเบียน MRA OPD</h2></div>', unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.subheader("🔐 เข้าสู่ระบบ")
    u = st.text_input("ชื่อผู้ใช้")
    p = st.text_input("รหัสผ่าน", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ เข้าสู่ระบบไม่สำเร็จ")

if not st.session_state.login:
    login()
    st.stop()

# ================= UPLOAD =================
file = st.file_uploader("📁 อัปโหลดไฟล์ CSV / Excel", type=["csv", "xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

    # ================= CHECK =================
    def check(v):
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
    if "DiagnosisCode" in df:
        df["ICD"] = df["DiagnosisCode"].apply(check_icd)

    if "DiagnosisText" in df:
        df["TEXT"] = df["DiagnosisText"].apply(check)

    status_cols = [c for c in df.columns if c in ["ICD", "TEXT"]]

    # ================= SCORE =================
    def score_row(row):
        full = len(status_cols) * 50
        got = 0

        for c in status_cols:
            if row[c] == "OK":
                got += 50

        percent = (got / full * 100) if full > 0 else 0

        return pd.Series([full, got, percent])

    df[["คะแนนเต็ม", "คะแนนได้", "เปอร์เซ็นต์"]] = df.apply(score_row, axis=1)

    df["ระดับ"] = df["เปอร์เซ็นต์"].apply(
        lambda x: "ดี 🟢" if x >= 90 else "พอใช้ 🟡" if x >= 70 else "ต้องแก้ไข 🔴"
    )

    # ================= FILTER =================
    level = st.selectbox("📊 เลือกระดับ", ["ทั้งหมด", "ดี 🟢", "พอใช้ 🟡", "ต้องแก้ไข 🔴"])

    show = df.copy()
    if level != "ทั้งหมด":
        show = show[show["ระดับ"] == level]

    # ================= KPI =================
    c1, c2, c3 = st.columns(3)
    c1.metric("จำนวนเคส", len(show))
    c2.metric("คะแนนเฉลี่ย", f"{show['คะแนนได้'].mean():.2f}")
    c3.metric("เปอร์เซ็นต์เฉลี่ย", f"{show['เปอร์เซ็นต์'].mean():.2f}")

    st.bar_chart(show["ระดับ"].value_counts())

    # ================= COLOR FULL ROW =================
    def row_color(row):
        if row["ระดับ"] == "ดี 🟢":
            return ["background-color:#d4edda"] * len(row)
        elif row["ระดับ"] == "พอใช้ 🟡":
            return ["background-color:#fff3cd"] * len(row)
        else:
            return ["background-color:#f8d7da"] * len(row)

    st.markdown("## 📋 ตารางตรวจสอบ")

    st.dataframe(
        show.style.apply(row_color, axis=1),
        use_container_width=True
    )

    # ================= DETAIL =================
    st.markdown("## 🔍 ดูเคส")

    idx = st.selectbox("เลือกเคส", show.index)
    st.write(show.loc[idx])

    # ================= EXPORT =================
    def to_excel(data):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='MRA')
        return output.getvalue()

    st.markdown("## 📤 Export Excel")

    st.download_button(
        "⬇️ ดาวน์โหลด Excel",
        data=to_excel(show),
        file_name="MRA_OPD.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
