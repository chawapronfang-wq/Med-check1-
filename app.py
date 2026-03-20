import pandas as pd
import io

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

    audit_rows = []
    passed = 0
    total = len(fields)

    for k, v in fields.items():

        if v == "ถูกต้อง":
            audit_rows.append([k, "ผ่าน", "ถูกต้องตามเกณฑ์ MRA OPD"])
            passed += 1

        elif v == "ไม่มีข้อมูล":
            audit_rows.append([k, "ไม่ผ่าน", "ควรบันทึกข้อมูลให้ครบถ้วนตามเวชระเบียน"])

        else:
            if k == "ICD-10":
                note = "รหัส ICD ไม่ถูกต้อง (รูปแบบ A00-Z99)"
            elif k == "Diagnosis":
                note = "ควรระบุวินิจฉัยให้ชัดเจน"
            elif k == "Treatment":
                note = "ควรระบุการรักษาให้ครบถ้วน"
            elif k == "Follow-up":
                note = "ควรมีแผนติดตามผู้ป่วย"
            else:
                note = "ต้องระบุชื่อแพทย์ผู้รับผิดชอบ"

            audit_rows.append([k, "ไม่ผ่าน", note])

    score = (passed / total) * 100

    summary_df = pd.DataFrame({
        "รายการ": ["คะแนนรวม", "สถานะเคส"],
        "ผล": [
            f"{passed}/{total} ({score:.2f}%)",
            "ผ่านเกณฑ์" if score >= 80 else "ไม่ผ่านเกณฑ์"
        ]
    })

    detail_df = pd.DataFrame(audit_rows, columns=["หัวข้อ", "สถานะ", "คำแนะนำ"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="SUMMARY")
        detail_df.to_excel(writer, index=False, sheet_name="AUDIT")

    return output.getvalue()
