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
🏥 MRA OPD REALTIME DASHBOARD (FINAL FIX)
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

# ================= MISSING HANDLER =================
MISSING = "❌ ไม่มีข้อมูล (Missing)"

def clean(v):
    if v is None:
        return MISSING
    if str(v).strip() == "" or str(v).lower() == "nan":
        return MISSING
    return v

# ================= UPLOAD =================
file = st.file_uploader("📁 อัปโหลดไฟล์ OPD", type=["csv","xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

    df = df.applymap(clean)

    # ================= SAFE GET =================
    def get(col):
        if col in df.columns:
            return df[col]
        return pd.Series([MISSING] * len(df))

    icd_raw = get("DiagnosisCode")
    dx_raw  = get("DiagnosisText")
    tx_raw  = get("Treatment")
    fu_raw  = get("FollowUp")
    dr_raw  = get("Doctor")

    # ================= CHECK =================
    def icd(v):
        if v == MISSING:
            return "❌ ไม่มีข้อมูล"
        return "ถูกต้อง" if re.match(r"^[A-Z][0-9]{2,3}$", str(v)) else "ผิดรูปแบบ"

    def txt(v):
        if v == MISSING:
            return "❌ ไม่มีข้อมูล"
        return "ถูกต้อง" if len(str(v)) >= 3 else "ข้อมูลไม่ครบ"

    df["ICD"] = icd_raw.apply(icd)
    df["DX"]  = dx_raw.apply(txt)
    df["TX"]  = tx_raw.apply(txt)
    df["FU"]  = fu_raw.apply(txt)
    df["DR"]  = dr_raw.apply(txt)

    # ================= SCORE =================
    def score(r):
        items = [r["ICD"], r["DX"], r["TX"], r["FU"], r["DR"]]
        total = len(items)
        got = sum(1 for i in items if i == "ถูกต้อง")
        return pd.Series([total, got, (got/total)*100])

    df[["เต็ม","ได้","%"]] = df.apply(score, axis=1)

    # ================= STATUS =================
    def status(x):
        if x >= 80:
            return "🟢 ผ่าน"
        elif x >= 60:
            return "🟡 เฝ้าระวัง"
        return "🔴 ต้องแก้"

    df["สถานะ"] = df["%"].apply(status)

    # ================= FIND ISSUES =================
    def จุดที่ต้องแก้(row):
        issues = []

        if row["ICD"] != "ถูกต้อง":
            issues.append("ICD-10")
        if row["DX"] != "ถูกต้อง":
            issues.append("Diagnosis")
        if row["TX"] != "ถูกต้อง":
            issues.append("Treatment")
        if row["FU"] != "ถูกต้อง":
            issues.append("Follow-up")
        if row["DR"] != "ถูกต้อง":
            issues.append("Doctor")

        return " / ".join(issues) if issues else "-"

    # ================= DASHBOARD =================
    st.markdown("## 📊 KPI Dashboard")

    c1,c2,c3 = st.columns(3)

    c1.metric("จำนวนเคส", len(df))
    c2.metric("คะแนนเฉลี่ย", f"{df['ได้'].mean():.2f}")
    c3.metric("% ผ่าน", f"{len(df[df['สถานะ']=='🟢 ผ่าน'])/len(df)*100:.2f}")

    # ================= GRAPH =================
    st.markdown("## 📊 กราฟ")

    chart = df["สถานะ"].value_counts().reindex(
        ["🟢 ผ่าน","🟡 เฝ้าระวัง","🔴 ต้องแก้"],
        fill_value=0
    )

    st.bar_chart(chart)

    # ================= TABLE =================
    st.markdown("## 📋 ตาราง")

    def color(row):
        if row["สถานะ"] == "🟢 ผ่าน":
            return ["background-color:#d4edda"] * len(row)
        elif row["สถานะ"] == "🟡 เฝ้าระวัง":
            return ["background-color:#fff3cd"] * len(row)
        return ["background-color:#f8d7da"] * len(row)

    st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 รายละเอียดเคส")

    idx = st.selectbox("เลือกเคส", df.index)

    st.write(df.loc[idx])

    # ================= STATUS CASE =================
    st.markdown("## 🧾 สถานะเคส")

    issues = จุดที่ต้องแก้(df.loc[idx])

    if df.loc[idx, "สถานะ"] == "🟢 ผ่าน":
        st.success("🟢 ผ่าน")
    else:
        st.error(df.loc[idx, "สถานะ"])
        st.warning(f"⚠️ จุดที่ต้องแก้: {issues}")

    # ================= EXPORT =================
    def export(df):

        output = io.BytesIO()

        summary = pd.DataFrame({
            "รายการ":["ทั้งหมด","คะแนนเฉลี่ย","ผ่าน","เฝ้าระวัง","ต้องแก้"],
            "ค่า":[
                len(df),
                df["ได้"].mean(),
                len(df[df["สถานะ"]=="🟢 ผ่าน"]),
                len(df[df["สถานะ"]=="🟡 เฝ้าระวัง"]),
                len(df[df["สถานะ"]=="🔴 ต้องแก้"])
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
        file_name=f"MRA_OPD_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
