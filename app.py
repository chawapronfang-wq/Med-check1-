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
🏥 MRA OPD REALTIME DASHBOARD (ANTI-CRASH)
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

# ================= SAFE CONSTANT =================
MISSING = "❌ ไม่มีข้อมูล"

# ================= CLEAN =================
def clean(v):
    if v is None:
        return MISSING
    v = str(v).strip()
    if v == "" or v.lower() == "nan":
        return MISSING
    return v

def bad_text(v):
    v = str(v)
    if v == MISSING:
        return True
    if "�" in v or "??" in v:
        return True
    if re.fullmatch(r"[^a-zA-Z0-9ก-๙]+", v):
        return True
    return False

def bad_age(v):
    if v == MISSING:
        return True
    try:
        v = float(v)
        return v < 0 or v > 120
    except:
        return True

# ================= UPLOAD =================
file = st.file_uploader("📁 อัปโหลด OPD", type=["csv","xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

    df = df.applymap(clean)

    def get(col):
        return df[col] if col in df.columns else pd.Series([MISSING]*len(df))

    icd_raw = get("DiagnosisCode")
    dx_raw  = get("DiagnosisText")
    tx_raw  = get("Treatment")
    fu_raw  = get("FollowUp")
    dr_raw  = get("Doctor")
    age_raw = get("Age")
    sex_raw = get("Sex")

    # ================= CHECK =================
    def icd(v):
        if v == MISSING: return "❌"
        if bad_text(v): return "❌"
        return "⚠️" if not re.match(r"^[A-Z][0-9]{2,3}$", v) else "✅"

    def txt(v):
        if v == MISSING: return "❌"
        if bad_text(v): return "❌"
        return "⚠️" if len(v) < 3 else "✅"

    df["ICD"] = icd_raw.apply(icd)
    df["DX"]  = dx_raw.apply(txt)
    df["TX"]  = tx_raw.apply(txt)
    df["FU"]  = fu_raw.apply(txt)
    df["DR"]  = dr_raw.apply(txt)

    df["AGE"] = age_raw.apply(lambda x: "❌" if bad_age(x) else "✅")

    df["SEX"] = sex_raw.apply(lambda x:
        "❌" if bad_text(x) or str(x).lower() not in ["male","female","ชาย","หญิง"]
        else "✅"
    )

    # ================= SCORE (FIXED NO CRASH) =================
    def score(row):
        items = [row["ICD"], row["DX"], row["TX"], row["FU"], row["DR"], row["AGE"], row["SEX"]]

        total = len(items)
        ok = sum(1 for i in items if i == "✅")
        warn = sum(1 for i in items if i == "⚠️")

        percent = ((ok + warn*0.5) / total) * 100 if total else 0

        return pd.Series([total, ok, percent])

    result = df.apply(score, axis=1)
    result.columns = ["เต็ม","ได้","%"]
    df = pd.concat([df, result], axis=1)

    # ================= STATUS =================
    def status(x):
        if x >= 85:
            return "🟢 ผ่านเกณฑ์"
        elif x >= 65:
            return "🟡 เฝ้าระวัง"
        return "🔴 ต้องแก้ไข"

    df["สถานะ"] = df["%"].apply(status)

    # ================= ISSUES =================
    def issues(row):
        err = []

        mapping = {
            "ICD":"รหัสโรค",
            "DX":"วินิจฉัย",
            "TX":"การรักษา",
            "FU":"ติดตาม",
            "DR":"แพทย์",
            "AGE":"อายุ",
            "SEX":"เพศ"
        }

        for k,v in mapping.items():
            if row[k] == "❌":
                err.append(v)

        return " / ".join(err) if err else "ไม่มีปัญหา"

    df["จุดที่ต้องแก้"] = df.apply(issues, axis=1)

    # ================= DASHBOARD =================
    st.markdown("## 📊 KPI")

    c1,c2,c3 = st.columns(3)
    c1.metric("จำนวนเคส", len(df))
    c2.metric("คะแนนเฉลี่ย", f"{df['ได้'].mean():.2f}")
    c3.metric("% ผ่าน", f"{len(df[df['สถานะ']=='🟢 ผ่านเกณฑ์'])/len(df)*100:.2f}")

    # ================= GRAPH =================
    st.markdown("## 📊 กราฟ")

    st.bar_chart(df["สถานะ"].value_counts().reindex(
        ["🟢 ผ่านเกณฑ์","🟡 เฝ้าระวัง","🔴 ต้องแก้ไข"],
        fill_value=0
    ))

    # ================= TABLE =================
    st.markdown("## 📋 ตาราง")

    def color(row):
        if row["สถานะ"] == "🟢 ผ่านเกณฑ์":
            return ["background-color:#d4edda"] * len(row)
        if row["สถานะ"] == "🟡 เฝ้าระวัง":
            return ["background-color:#fff3cd"] * len(row)
        return ["background-color:#f8d7da"] * len(row)

    st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

    # ================= DETAIL =================
    st.markdown("## 🔍 รายละเอียดเคส")

    idx = st.selectbox("เลือกเคส", df.index)

    st.write(df.loc[idx])

    st.markdown("## 🧾 สถานะเคส")

    st.write("สถานะ:", df.loc[idx,"สถานะ"])
    st.info("📌 จุดที่ต้องแก้: " + df.loc[idx,"จุดที่ต้องแก้"])

    # ================= EXPORT =================
    def export(df):

        output = io.BytesIO()

        summary = pd.DataFrame({
            "รายการ":["ทั้งหมด","คะแนนเฉลี่ย","ผ่าน","เฝ้าระวัง","ต้องแก้"],
            "ค่า":[
                len(df),
                df["ได้"].mean(),
                len(df[df["สถานะ"]=="🟢 ผ่านเกณฑ์"]),
                len(df[df["สถานะ"]=="🟡 เฝ้าระวัง"]),
                len(df[df["สถานะ"]=="🔴 ต้องแก้ไข"])
            ]
        })

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="DATA")
            summary.to_excel(writer, index=False, sheet_name="SUMMARY")

        return output.getvalue()

    st.markdown("## 📤 ดาวน์โหลด")

    st.download_button(
        "⬇️ Export MRA OPD",
        data=export(df),
        file_name=f"MRA_OPD_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
