import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

st.set_page_config(page_title="MRA OPD SYSTEM", layout="wide")

# ================= HEADER =================
st.markdown("""
<div style="background:linear-gradient(90deg,#0f3057,#008891);
padding:18px;border-radius:12px;color:white;font-size:22px">
🏥 ระบบ MRA OPD (Audit + KPI Dashboard)
</div>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 เข้าสู่ระบบ")
    u = st.text_input("ชื่อผู้ใช้")
    p = st.text_input("รหัสผ่าน", type="password")

    if st.button("เข้าสู่ระบบ"):
        if users.get(u) == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# ================= UPLOAD =================
file = st.file_uploader("📁 อัปโหลดไฟล์ OPD (CSV / Excel)", type=["csv","xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

    # ================= FIX NaN =================
    df = df.fillna("ไม่ระบุ")

    # ================= CHECK FUNCTIONS =================
    def icd_check(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if re.match(r"^[A-Z][0-9]{2,3}$", str(v)) else "ผิดรูปแบบ"

    def text_check(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if len(str(v)) >= 3 else "ข้อมูลสั้นเกินไป"

    # ================= AUDIT =================
    checks = {
        "ICD": lambda r: icd_check(r.get("DiagnosisCode")),
        "DIAG": lambda r: text_check(r.get("DiagnosisText")),
        "TREAT": lambda r: text_check(r.get("Treatment")),
        "FOLLOW": lambda r: text_check(r.get("FollowUp")),
        "DOC": lambda r: text_check(r.get("Doctor"))
    }

    def score(row):
        total = len(checks)
        got = sum(1 for c in checks if checks[c](row) == "ถูกต้อง")
        percent = (got / total) * 100
        return pd.Series([total, got, percent])

    df[["คะแนนเต็ม","คะแนนได้","เปอร์เซ็นต์"]] = df.apply(score, axis=1)

    # ================= LEVEL =================
    def level(x):
        if x >= 80:
            return "ผ่านเกณฑ์ 🟢"
        elif x >= 60:
            return "พอใช้ 🟡"
        else:
            return "ต้องแก้ไข 🔴"

    df["สถานะ"] = df["เปอร์เซ็นต์"].apply(level)

    # ================= FILTER =================
    st.markdown("## 📊 KPI Dashboard")

    c1, c2, c3 = st.columns(3)
    c1.metric("จำนวนเคส", len(df))
    c2.metric("คะแนนเฉลี่ย", f"{df['คะแนนได้'].mean():.2f}")
    c3.metric("% ผ่าน", f"{len(df[df['สถานะ']=='ผ่านเกณฑ์ 🟢'])/len(df)*100:.2f}")

    # ================= GRAPH FIX =================
    chart = df["สถานะ"].value_counts().reindex(
        ["ผ่านเกณฑ์ 🟢","พอใช้ 🟡","ต้องแก้ไข 🔴"],
        fill_value=0
    )

    st.bar_chart(chart)

    # ================= TABLE COLOR =================
    def color(row):
        if row["สถานะ"] == "ผ่านเกณฑ์ 🟢":
            return ["background-color:#d4edda"] * len(row)
        elif row["สถานะ"] == "พอใช้ 🟡":
            return ["background-color:#fff3cd"] * len(row)
        else:
            return ["background-color:#f8d7da"] * len(row)

    st.markdown("## 📋 ตารางข้อมูล")
    st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 รายละเอียดเคส")
    idx = st.selectbox("เลือกเคส", df.index)
    st.write(df.loc[idx])

    # ================= STATUS THAI =================
    st.markdown("## 🧾 สถานะข้อมูล")

    for c in ["DiagnosisCode","DiagnosisText","Treatment","FollowUp","Doctor"]:
        if c in df.columns:
            v = df.loc[idx, c]

            if v == "ไม่ระบุ":
                msg = "❗ ไม่มีข้อมูล (ควรกรอก)"
            elif len(str(v)) < 3:
                msg = "⚠️ ข้อมูลไม่ครบ"
            else:
                msg = "✅ ถูกต้อง"

            st.write(f"{c}: {msg}")

    # ================= EXPORT =================
    def export_excel(data):

        output = io.BytesIO()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        summary = pd.DataFrame({
            "รายการ": [
                "ทั้งหมด",
                "คะแนนเฉลี่ย",
                "ผ่าน",
                "พอใช้",
                "ต้องแก้ไข",
                "วันที่"
            ],
            "ค่า": [
                len(data),
                data["คะแนนได้"].mean(),
                len(data[data["สถานะ"]=="ผ่านเกณฑ์ 🟢"]),
                len(data[data["สถานะ"]=="พอใช้ 🟡"]),
                len(data[data["สถานะ"]=="ต้องแก้ไข 🔴"]),
                now
            ]
        })

        error = data[data["สถานะ"] != "ผ่านเกณฑ์ 🟢"]

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            data.to_excel(writer, index=False, sheet_name="DATA")
            error.to_excel(writer, index=False, sheet_name="ERROR")
            summary.to_excel(writer, index=False, sheet_name="SUMMARY")

        return output.getvalue()

    st.markdown("## 📤 ดาวน์โหลดรายงาน")

    st.download_button(
        "⬇️ ดาวน์โหลด MRA OPD Report",
        data=export_excel(df),
        file_name=f"MRA_OPD_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
