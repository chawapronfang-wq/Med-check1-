import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ระบบ MRA OPD", layout="wide")

# ================= เข้าสู่ระบบ =================
ผู้ใช้ = {"admin": "1234"}

if "เข้าสู่ระบบแล้ว" not in st.session_state:
    st.session_state.เข้าสู่ระบบแล้ว = False

if not st.session_state.เข้าสู่ระบบแล้ว:
    st.title("🔐 เข้าสู่ระบบระบบตรวจเวชระเบียน MRA OPD")

    ชื่อผู้ใช้ = st.text_input("ชื่อผู้ใช้")
    รหัสผ่าน = st.text_input("รหัสผ่าน", type="password")

    if st.button("เข้าสู่ระบบ"):
        if ชื่อผู้ใช้ in ผู้ใช้ and ผู้ใช้[ชื่อผู้ใช้] == รหัสผ่าน:
            st.session_state.เข้าสู่ระบบแล้ว = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# ================= อัปโหลดไฟล์ =================
ไฟล์ = st.file_uploader("📁 อัปโหลดไฟล์ผู้ป่วย OPD", type=["csv","xlsx"])

ข้อมูล = None

if ไฟล์:
    ข้อมูล = pd.read_csv(ไฟล์) if ไฟล์.name.endswith("csv") else pd.read_excel(ไฟล์)
    ข้อมูล = ข้อมูล.fillna("ไม่มีข้อมูล")

# ================= ตรวจสอบข้อมูล =================
if ข้อมูล is None or len(ข้อมูล) == 0:
    st.warning("⚠️ กรุณาอัปโหลดข้อมูลก่อน")
    st.stop()

# ================= เตรียมข้อมูล =================
for คอลัมน์ in ["ICD","DX","TX","FU","DR"]:
    if คอลัมน์ not in ข้อมูล.columns:
        ข้อมูล[คอลัมน์] = "ไม่มีข้อมูล"
    else:
        ข้อมูล[คอลัมน์] = ข้อมูล[คอลัมน์].fillna("ไม่มีข้อมูล")

# ================= ตรวจสอบคุณภาพ =================
def ตรวจ(v):
    if v == "ไม่มีข้อมูล":
        return "ขาดข้อมูล"
    return "ถูกต้อง" if len(str(v)) >= 3 else "ข้อมูลไม่ครบ"

ข้อมูล["ICD_s"] = ข้อมูล["ICD"].apply(ตรวจ)
ข้อมูล["DX_s"] = ข้อมูล["DX"].apply(ตรวจ)
ข้อมูล["TX_s"] = ข้อมูล["TX"].apply(ตรวจ)
ข้อมูล["FU_s"] = ข้อมูล["FU"].apply(ตรวจ)
ข้อมูล["DR_s"] = ข้อมูล["DR"].apply(ตรวจ)

# ================= คำนวณคะแนน =================
def คำนวณแนน(row):
    รายการ = [row["ICD_s"], row["DX_s"], row["TX_s"], row["FU_s"], row["DR_s"]]
    เต็ม = len(รายการ)
    ได้ = sum(1 for i in รายการ if i == "ถูกต้อง")
    return pd.Series([เต็ม, ได้, (ได้/เต็ม)*100])

ข้อมูล[["คะแนนเต็ม","คะแนนได้","เปอร์เซ็นต์"]] = ข้อมูล.apply(คำนวณแนน, axis=1)

# ================= สถานะเคส =================
def สถานะ(x):
    if x >= 80:
        return "🟢 ผ่านเกณฑ์"
    elif x >= 60:
        return "🟡 เฝ้าระวัง"
    return "🔴 ต้องแก้ไข"

ข้อมูล["สถานะ"] = ข้อมูล["เปอร์เซ็นต์"].apply(สถานะ)

# ================= แดชบอร์ด =================
st.markdown("## 📊 แดชบอร์ด MRA OPD")

คอล1, คอล2, คอล3 = st.columns(3)

คอล1.metric("จำนวนเคส", len(ข้อมูล))
คอล2.metric("คะแนนเฉลี่ย", f"{ข้อมูล['คะแนนได้'].mean():.2f}")
คอล3.metric("% ผ่าน", f"{len(ข้อมูล[ข้อมูล['สถานะ']=='🟢 ผ่านเกณฑ์'])/len(ข้อมูล)*100:.2f}")

# ================= กราฟ =================
st.markdown("## 📊 กราฟสถานะเคส")

สถานะ_clean = ข้อมูล["สถานะ"].astype(str).str.strip()

สถานะ_clean = สถานะ_clean.replace({
    "ผ่านเกณฑ์":"🟢 ผ่านเกณฑ์",
    "เฝ้าระวัง":"🟡 เฝ้าระวัง",
    "ต้องแก้":"🔴 ต้องแก้ไข"
})

กราฟ = สถานะ_clean.value_counts().reindex(
    ["🟢 ผ่านเกณฑ์","🟡 เฝ้าระวัง","🔴 ต้องแก้ไข","ไม่มีข้อมูล"],
    fill_value=0
)

st.bar_chart(กราฟ)

# ================= ตาราง =================
st.markdown("## 📋 ตารางข้อมูล")

def สี(row):
    if row["สถานะ"] == "🟢 ผ่านเกณฑ์":
        return ["background-color:#d4edda"] * len(row)
    elif row["สถานะ"] == "🟡 เฝ้าระวัง":
        return ["background-color:#fff3cd"] * len(row)
    return ["background-color:#f8d7da"] * len(row)

st.dataframe(ข้อมูล.style.apply(สี, axis=1), use_container_width=True)

# ================= รายละเอียดเคส =================
st.markdown("## 🧾 สถานะเคสรายรายการ")

เลือก = st.selectbox("เลือกเคส", ข้อมูล.index)

เคส = {
    "ICD": ข้อมูล.loc[เลือก,"ICD_s"],
    "การวินิจฉัย": ข้อมูล.loc[เลือก,"DX_s"],
    "การรักษา": ข้อมูล.loc[เลือก,"TX_s"],
    "การติดตาม": ข้อมูล.loc[เลือก,"FU_s"],
    "แพทย์": ข้อมูล.loc[เลือก,"DR_s"]
}

for k,v in เคส.items():
    if v == "ถูกต้อง":
        st.success(f"{k}: ผ่าน")
    elif v == "ขาดข้อมูล":
        st.warning(f"{k}: ไม่มีข้อมูล")
    else:
        st.error(f"{k}: ต้องแก้ไข")

# ================= รายงานส่งออก =================
def ส่งออกรายงาน(ข้อมูล, idx):

    output = io.BytesIO()
    row = ข้อมูล.loc[idx]

    รายการ = {
        "ICD": row["ICD_s"],
        "การวินิจฉัย": row["DX_s"],
        "การรักษา": row["TX_s"],
        "การติดตาม": row["FU_s"],
        "แพทย์": row["DR_s"]
    }

    รายงาน = []
    ผ่าน = 0
    ทั้งหมด = len(รายการ)

    for k,v in รายการ.items():

        if v == "ถูกต้อง":
            รายงาน.append([k,"ผ่าน","ถูกต้องตามเกณฑ์ MRA"])
            ผ่าน += 1
        elif v == "ขาดข้อมูล":
            รายงาน.append([k,"ไม่ผ่าน","ควรบันทึกข้อมูลให้ครบ"])
        else:
            รายงาน.append([k,"ไม่ผ่าน","ต้องแก้ไขข้อมูล"])

    คะแนน = (ผ่าน/ทั้งหมด)*100

    สรุป = pd.DataFrame({
        "หัวข้อ":["คะแนนรวม","สถานะ"],
        "ผล":[f"{ผ่าน}/{ทั้งหมด} ({คะแนน:.2f}%)","ผ่าน" if คะแนน>=80 else "ไม่ผ่าน"]
    })

    รายละเอียด = pd.DataFrame(รายงาน, columns=["หัวข้อ","สถานะ","คำแนะนำ"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        สรุป.to_excel(writer,index=False,sheet_name="สรุป")
        รายละเอียด.to_excel(writer,index=False,sheet_name="ตรวจสอบ")

    return output.getvalue()

st.markdown("## 📄 ดาวน์โหลดรายงาน")

st.download_button(
    "⬇️ ดาวน์โหลดใบตรวจ MRA",
    data=ส่งออกรายงาน(ข้อมูล, เลือก),
    file_name="รายงาน_MRA_OPD.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
