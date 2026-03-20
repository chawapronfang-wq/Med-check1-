import streamlit as st

st.markdown("## 📊 กราฟสถานะเคส")

# กัน df ไม่มี
if "df" not in globals():
    st.warning("⚠️ ยังไม่มีข้อมูล")
    st.stop()

if "สถานะ" not in df.columns:
    st.warning("⚠️ ไม่พบคอลัมน์ 'สถานะ'")
    st.stop()

# กัน None + ทำความสะอาด
status = (
    df["สถานะ"]
    .fillna("ไม่มีข้อมูล")
    .astype(str)
    .str.strip()
)

# แปลงชื่อให้ตรงกันทั้งหมด
status = status.replace({
    "ผ่านเกณฑ์": "🟢 ผ่าน",
    "ผ่าน": "🟢 ผ่าน",
    "🟢 ผ่านเกณฑ์": "🟢 ผ่าน",

    "ไม่ผ่าน": "🔴 ต้องแก้",
    "ต้องแก้": "🔴 ต้องแก้",
    "🔴 ต้องแก้ไข": "🔴 ต้องแก้",

    "เฝ้าระวัง": "🟡 เฝ้าระวัง",
    "🟡 เฝ้าระวัง": "🟡 เฝ้าระวัง"
})

# นับค่า
chart = status.value_counts().reindex(
    ["🟢 ผ่าน","🟡 เฝ้าระวัง","🔴 ต้องแก้","ไม่มีข้อมูล"],
    fill_value=0
)

# กันกราฟว่าง
if chart.sum() == 0:
    st.warning("⚠️ ไม่มีข้อมูลสำหรับสร้างกราฟ")
else:
    st.bar_chart(chart)
