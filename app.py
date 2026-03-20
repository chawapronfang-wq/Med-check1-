import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

st.set_page_config(page_title="MRA OPD PRO", layout="wide")

# ================= HEADER =================
st.markdown("""
<div style="background:linear-gradient(90deg,#0f3057,#008891);
padding:18px;border-radius:12px;color:white;font-size:22px">
🏥 ระบบ MRA OPD PRO (Audit + Error Tracking + KPI)
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

    # ================= CLEAN DATA =================
    df = df.fillna("ไม่ระบุ")

    # ================= CHECK FUNCTIONS =================
    def icd(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if re.match(r"^[A-Z][0-9]{2,3}$", str(v)) else "รูปแบบผิด"

    def text(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if len(str(v)) >= 3 else "ข้อมูลสั้น"

    # ================= STATUS PER FIELD =================
    df["ICD_status"] = df["DiagnosisCode"].apply(icd) if "DiagnosisCode" in df else "ไม่มีข้อมูล"
    df["DX_status"] = df["DiagnosisText"].apply(text) if "DiagnosisText" in df else "ไม่มีข้อมูล"
    df["TX_status"] = df["Treatment"].apply(text) if "Treatment" in df else "ไม่มีข้อมูล"
    df["FU_status"] = df["FollowUp"].apply(text) if "FollowUp" in df else "ไม่มีข้อมูล"
    df["DR_status"] = df["Doctor"].apply(text) if "Doctor" in df else "ไม่มีข้อมูล"

    # ================= ERROR DETAIL =================
    def error_list(row):
        err = []

        if row["ICD_status"] != "ถูกต้อง":
            err.append("ICD-10")
        if row["DX_status"] != "ถูกต้อง":
            err.append("Diagnosis")
        if row["TX_status"] != "ถูกต้อง":
            err.append("Treatment")
        if row["FU_status"] != "ถูกต้อง":
            err.append("Follow-up")
        if row["DR_status"] != "ถูกต้อง":
            err.append("Doctor")

        return "✅ ผ่าน" if len(err) == 0 else "❌ ต้องแก้: " + ", ".join(err)

    df["ปัญหา"] = df.apply(error_list, axis=1)

    # ================= SCORE =================
    def score(row):
        checks = [
            row["ICD_status"],
            row["DX_status"],
            row["TX_status"],
            row["FU_status"],
            row["DR_status"]
        ]

        total = len(checks)
        got = sum(1 for c in checks if c == "ถูกต้อง")
        percent = (got / total) * 100

        return pd.Series([total, got, percent])

    df[["คะแนนเต็ม","คะแนนได้","เปอร์เซ็นต์"]] = df.apply(score, axis=1)

    # ================= STATUS LEVEL =================
    def status(x):
        if x >= 80:
            return "🟢 ผ่านเกณฑ์"
        elif x >= 60:
            return "🟡 เฝ้าระวัง"
        else:
            return "🔴 ต้องแก้ไข"

    df["สถานะ"] = df["เปอร์เซ็นต์"].apply(status)

    # ================= KPI =================
    st.markdown("## 📊 KPI Dashboard")

    c1, c2, c3 = st.columns(3)
    c1.metric("จำนวนเคส", len(df))
    c2.metric("คะแนนเฉลี่ย", f"{df['คะแนนได้'].mean():.2f}")
    c3.metric("% ผ่าน", f"{len(df[df['สถานะ']=='🟢 ผ่านเกณฑ์'])/len(df)*100:.2f}")

    # ================= FIX GRAPH =================
    chart = df["สถานะ"].value_counts().reindex(
        ["🟢 ผ่านเกณฑ์","🟡 เฝ้าระวัง","🔴 ต้องแก้ไข"],
        fill_value=0
    )

    st.bar_chart(chart)

    # ================= TABLE COLOR =================
    def color(row):
        if row["สถานะ"] == "🟢 ผ่านเกณฑ์":
            return ["background-color:#d4edda"] * len(row)
        elif row["สถานะ"] == "🟡 เฝ้าระวัง":
            return ["background-color:#fff3cd"] * len(row)
        else:
            return ["background-color:#f8d7da"] * len(row)

    st.markdown("## 📋 ตารางข้อมูล")
    st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

    # ================= ERROR TABLE =================
    st.markdown("## ❌ เคสที่ต้องแก้ (ละเอียด)")

    error_df = df[df["สถานะ"] != "🟢 ผ่านเกณฑ์"][[
        "DiagnosisCode","DiagnosisText","Treatment","FollowUp","Doctor","ปัญหา"
    ]]

    st.dataframe(error_df, use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 วิเคราะห์รายเคส")

    idx = st.selectbox("เลือกเคส", df.index)
    st.write(df.loc[idx])

    st.markdown("### 🧾 ปัญหาเคสนี้")
    st.warning(df.loc[idx, "ปัญหา"])

    # ================= EXPORT =================
    def export(df):

        output = io.BytesIO()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        summary = pd.DataFrame({
            "รายการ":[
                "ทั้งหมด","คะแนนเฉลี่ย","ผ่าน","เฝ้าระวัง","ต้องแก้","วันที่"
            ],
            "ค่า":[
                len(df),
                df["คะแนนได้"].mean(),
                len(df[df["สถานะ"]=="🟢 ผ่านเกณฑ์"]),
                len(df[df["สถานะ"]=="🟡 เฝ้าระวัง"]),
                len(df[df["สถานะ"]=="🔴 ต้องแก้ไข"]),
                now
            ]
        })

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="DATA")
            error_df.to_excel(writer, index=False, sheet_name="ERROR")
            summary.to_excel(writer, index=False, sheet_name="SUMMARY")

        return output.getvalue()

    st.markdown("## 📤 ดาวน์โหลดรายงาน")

    st.download_button(
        "⬇️ ดาวน์โหลด MRA OPD PRO FINAL",
        data=export(df),
        file_name=f"MRA_OPD_PRO_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
