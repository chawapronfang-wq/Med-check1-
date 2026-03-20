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
    if "DiagnosisCode" in df:
        df["ICD_Status"] = df["DiagnosisCode"].apply(check_icd)

    if "DiagnosisText" in df:
        df["Text_Status"] = df["DiagnosisText"].apply(check_text)

    status_cols = [c for c in df.columns if "Status" in c]

    # ================= SCORE =================
    def score(row):
        s = 100
        for c in status_cols:
            if row[c] != "OK":
                s -= 30
        return max(s, 0)

    df["Score"] = df.apply(score, axis=1)

    df["ระดับ"] = df["Score"].apply(
        lambda x: "ดี 🟢" if x >= 90 else "พอใช้ 🟡" if x >= 70 else "ต้องแก้ไข 🔴"
    )

    # ================= FILTER =================
    level = st.selectbox("📊 เลือกระดับ", ["ทั้งหมด", "ดี 🟢", "พอใช้ 🟡", "ต้องแก้ไข 🔴"])

    show = df.copy()
    if level != "ทั้งหมด":
        show = show[show["ระดับ"] == level]

    # ================= KPI =================
    c1, c2 = st.columns(2)
    c1.metric("จำนวนเคส", len(show))
    c2.metric("คะแนนเฉลี่ย", f"{show['Score'].mean():.2f}")

    st.bar_chart(show["ระดับ"].value_counts())

    # ================= COLOR HIGHLIGHT =================
    def color(val):
        if val == "Missing":
            return "background-color:#fff3cd"   # เหลือง
        if val == "Invalid":
            return "background-color:#f8d7da"   # แดง
        if val == "OK":
            return "background-color:#d4edda"   # เขียว
        return ""

    st.markdown("## 📋 ตารางตรวจสอบ")

    st.dataframe(
        show.style.applymap(color, subset=status_cols),
        use_container_width=True
    )

    # ================= DETAIL =================
    st.markdown("## 🔍 ดูเคส")

    idx = st.selectbox("เลือกเคส", show.index)
    st.write(show.loc[idx])

    # ================= EXPORT EXCEL =================
    def to_excel(data):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='MRA')
        return output.getvalue()

    st.markdown("## 📤 Export")

    excel = to_excel(show)

    st.download_button(
        "⬇️ ดาวน์โหลด Excel",
        data=excel,
        file_name="MRA_OPD.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
