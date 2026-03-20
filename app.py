import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

st.set_page_config(page_title="MRA OPD REALTIME", layout="wide")

# ================= HEADER =================
st.markdown("""
<div style="background:linear-gradient(90deg,#0f3057,#008891);
padding:18px;border-radius:12px;color:white;font-size:22px">
🏥 MRA OPD REALTIME DASHBOARD (FINAL)
</div>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin":"1234"}

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

    # ================= CLEAN =================
    df = df.fillna("ไม่ระบุ")

    # ================= CHECK =================
    def icd(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if re.match(r"^[A-Z][0-9]{2,3}$", str(v)) else "ผิดรูปแบบ"

    def txt(v):
        if v == "ไม่ระบุ":
            return "ไม่มีข้อมูล"
        return "ถูกต้อง" if len(str(v)) >= 3 else "ข้อมูลไม่ครบ"

    # ================= FIELD STATUS =================
    df["ICD"] = df["DiagnosisCode"].apply(icd) if "DiagnosisCode" in df else "ไม่มีข้อมูล"
    df["DX"] = df["DiagnosisText"].apply(txt) if "DiagnosisText" in df else "ไม่มีข้อมูล"
    df["TX"] = df["Treatment"].apply(txt) if "Treatment" in df else "ไม่มีข้อมูล"
    df["FU"] = df["FollowUp"].apply(txt) if "FollowUp" in df else "ไม่มีข้อมูล"
    df["DR"] = df["Doctor"].apply(txt) if "Doctor" in df else "ไม่มีข้อมูล"

    # ================= SCORE =================
    def score(r):
        items = [r["ICD"], r["DX"], r["TX"], r["FU"], r["DR"]]
        total = len(items)
        got = sum(1 for i in items if i == "ถูกต้อง")
        percent = (got / total) * 100
        return pd.Series([total, got, percent])

    df[["คะแนนเต็ม","คะแนนได้","เปอร์เซ็นต์"]] = df.apply(score, axis=1)

    # ================= STATUS =================
    def status(x):
        if x >= 80:
            return "🟢 ผ่านเกณฑ์"
        elif x >= 60:
            return "🟡 เฝ้าระวัง"
        return "🔴 ต้องแก้ไข"

    df["สถานะ"] = df["เปอร์เซ็นต์"].apply(status)

    # ================= KPI DASHBOARD =================
    st.markdown("## 📊 KPI Dashboard (Realtime)")

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
        return ["background-color:#f8d7da"] * len(row)

    st.markdown("## 📋 ตารางข้อมูล")
    st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 รายละเอียดเคส")

    idx = st.selectbox("เลือกเคส", df.index)
    st.write(df.loc[idx])

    # ================= 🧾 STATUS CASE (FIXED NAME) =================
    st.markdown("## 🧾 สถานะเคส")

    fields = {
        "ICD-10": df.loc[idx, "ICD"],
        "Diagnosis": df.loc[idx, "DX"],
        "Treatment": df.loc[idx, "TX"],
        "Follow-up": df.loc[idx, "FU"],
        "Doctor": df.loc[idx, "DR"]
    }

    for k,v in fields.items():
        if v == "ถูกต้อง":
            st.success(f"{k}: ผ่าน")
        elif v == "ไม่มีข้อมูล":
            st.warning(f"{k}: ไม่มีข้อมูล (ควรกรอก)")
        else:
            st.error(f"{k}: ต้องแก้ ({v})")

    # ================= EXPORT =================
    def export(df):

        output = io.BytesIO()

        summary = pd.DataFrame({
            "รายการ":[
                "ทั้งหมด","คะแนนเฉลี่ย","ผ่าน","เฝ้าระวัง","ต้องแก้"
            ],
            "ค่า":[
                len(df),
                df["คะแนนได้"].mean(),
                len(df[df["สถานะ"]=="🟢 ผ่านเกณฑ์"]),
                len(df[df["สถานะ"]=="🟡 เฝ้าระวัง"]),
                len(df[df["สถานะ"]=="🔴 ต้องแก้ไข"])
            ]
        })

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="DATA")
            summary.to_excel(writer, index=False, sheet_name="SUMMARY")

        return output.getvalue()

    st.markdown("## 📤 ดาวน์โหลดรายงาน")

    st.download_button(
        "⬇️ ดาวน์โหลด MRA OPD REPORT",
        data=export(df),
        file_name=f"MRA_OPD_REALTIME_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
