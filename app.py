import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="MRA OPD", layout="wide")

# ================= LOGIN =================
users = {"admin": "1234"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 เข้าสู่ระบบ MRA OPD")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# ================= UPLOAD =================
file = st.file_uploader("📁 อัปโหลดไฟล์ OPD", type=["csv","xlsx"])

df = None

if file:
    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)
    df = df.fillna("ไม่มีข้อมูล")

    st.success("โหลดข้อมูลสำเร็จ")

# ================= SAFE CHECK =================
if df is None:
    st.warning("กรุณาอัปโหลดไฟล์ก่อน")
    st.stop()

if len(df) == 0:
    st.warning("ไม่มีข้อมูลในไฟล์")
    st.stop()

# ================= MOCK STATUS =================
for col in ["ICD","DX","TX","FU","DR"]:
    if col not in df.columns:
        df[col] = "ไม่มีข้อมูล"
    else:
        df[col] = df[col].fillna("ไม่มีข้อมูล")

# ================= AUDIT FUNCTION =================
def export_audit(df, idx):

    output = io.BytesIO()
    row = df.loc[idx]

    fields = {
        "ICD-10": row["ICD"],
        "Diagnosis": row["DX"],
        "Treatment": row["TX"],
        "Follow-up": row["FU"],
        "Doctor": row["DR"]
    }

    audit = []
    passed = 0
    total = len(fields)

    for k, v in fields.items():

        if v == "ถูกต้อง":
            audit.append([k, "ผ่าน", "ถูกต้องตามเกณฑ์ MRA OPD"])
            passed += 1
        elif v == "ไม่มีข้อมูล":
            audit.append([k, "ไม่ผ่าน", "ควรบันทึกข้อมูลให้ครบ"])
        else:
            audit.append([k, "ไม่ผ่าน", "ต้องตรวจสอบและแก้ไข"])

    score = (passed / total) * 100

    summary = pd.DataFrame({
        "รายการ": ["คะแนนรวม","สถานะ"],
        "ผล": [
            f"{passed}/{total} ({score:.2f}%)",
            "ผ่าน" if score >= 80 else "ไม่ผ่าน"
        ]
    })

    detail = pd.DataFrame(audit, columns=["หัวข้อ","สถานะ","คำแนะนำ"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="SUMMARY")
        detail.to_excel(writer, index=False, sheet_name="AUDIT")

    return output.getvalue()

# ================= UI =================
st.markdown("## 🏥 MRA OPD DASHBOARD")

idx = st.selectbox("เลือกเคส", df.index)

st.markdown("## 📄 ใบ Audit MRA")

st.download_button(
    "⬇️ ดาวน์โหลด Audit",
    data=export_audit(df, idx),
    file_name="MRA_OPD_AUDIT.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
