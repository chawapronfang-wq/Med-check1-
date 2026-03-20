import streamlit as st
import pandas as pd
import io

# ================= EXPORT FUNCTION =================
def export_audit(df, idx):

    output = io.BytesIO()

    row = df.loc[idx]

    fields = {
        "ICD-10": row.get("ICD", "ไม่มีข้อมูล"),
        "Diagnosis": row.get("DX", "ไม่มีข้อมูล"),
        "Treatment": row.get("TX", "ไม่มีข้อมูล"),
        "Follow-up": row.get("FU", "ไม่มีข้อมูล"),
        "Doctor": row.get("DR", "ไม่มีข้อมูล")
    }

    audit = []
    passed = 0
    total = len(fields)

    for k, v in fields.items():

        if v == "ถูกต้อง":
            audit.append([k, "ผ่าน", "ถูกต้องตามเกณฑ์ MRA OPD"])
            passed += 1

        elif v == "ไม่มีข้อมูล":
            audit.append([k, "ไม่ผ่าน", "ควรบันทึกข้อมูลให้ครบถ้วน"])
        else:
            audit.append([k, "ไม่ผ่าน", "ต้องตรวจสอบและแก้ไขข้อมูล"])

    score = (passed / total) * 100 if total > 0 else 0

    summary = pd.DataFrame({
        "รายการ": ["คะแนนรวม", "สถานะเคส"],
        "ผล": [
            f"{passed}/{total} ({score:.2f}%)",
            "ผ่านเกณฑ์" if score >= 80 else "ไม่ผ่านเกณฑ์"
        ]
    })

    detail = pd.DataFrame(audit, columns=["หัวข้อ", "สถานะ", "คำแนะนำ"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="SUMMARY")
        detail.to_excel(writer, index=False, sheet_name="AUDIT")

    return output.getvalue()


# ================= UI =================
st.markdown("## 📄 ใบ Audit MRA OPD")

# กันพัง: ต้องมี df ก่อน
if "df" not in globals():
    st.warning("⚠️ ยังไม่มีข้อมูล กรุณาอัปโหลดไฟล์ก่อน")
    st.stop()

if len(df) == 0:
    st.warning("⚠️ ไม่มีข้อมูลในตาราง")
    st.stop()

# เลือกเคส
idx = st.selectbox("เลือกเคส", df.index)

# ปุ่มโหลด
st.download_button(
    label="⬇️ ดาวน์โหลดใบ Audit MRA",
    data=export_audit(df, idx),
    file_name="MRA_OPD_AUDIT.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
