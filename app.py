import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ================= LOGIN SYSTEM =================
users = {
    "admin": "1234",
    "user": "abcd"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.set_page_config(page_title="Login", layout="centered")

    st.markdown("## 🔐 เข้าสู่ระบบ")
    st.info("ตัวอย่าง: admin / 1234 หรือ user / abcd")

    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")

    if st.button("เข้าสู่ระบบ"):
        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
            st.success("✅ เข้าสู่ระบบสำเร็จ")
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    st.stop()

# ================= CONFIG =================
st.set_page_config(page_title="Medical Record System", layout="wide")

# ================= LOGOUT =================
if st.button("🚪 ออกจากระบบ"):
    st.session_state.clear()
    st.rerun()

# ================= STYLE =================
st.markdown("""
<style>
.main {background-color: #eef6fb;}
.header {
    background: linear-gradient(90deg, #0a3d62, #3c91e6);
    padding: 25px;
    border-radius: 12px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div class="header">
<h2>🏥 ระบบตรวจสอบคุณภาพข้อมูลเวชระเบียน</h2>
<p>Medical Record Data Quality System (Final Pro)</p>
</div>
""", unsafe_allow_html=True)

# ================= RESET =================
if st.button("🔄 รีเซ็ต"):
    st.session_state.clear()

# ================= UPLOAD =================
uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ (Excel / CSV)", type=["xlsx", "csv"])

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.markdown("## 📊 ตัวอย่างข้อมูล")
    st.dataframe(df, use_container_width=True)

    selected_cols = st.multiselect("📌 เลือกคอลัมน์ที่ต้องการตรวจสอบ", df.columns.tolist())

    if len(selected_cols) == 0:
        st.warning("⚠️ กรุณาเลือกคอลัมน์ก่อนเริ่มตรวจสอบ")

    check_types = ["ตัวเลข", "ข้อความ", "รหัส (>=3 ตัวอักษร)", "วันที่"]

    def auto_detect(series):
        if pd.api.types.is_numeric_dtype(series):
            return "ตัวเลข"
        try:
            pd.to_datetime(series.dropna().iloc[0])
            return "วันที่"
        except:
            return "ข้อความ"

    col_types = {}
    for col in selected_cols:
        suggested = auto_detect(df[col])
        col_types[col] = st.selectbox(
            f"{col}",
            check_types,
            index=check_types.index(suggested) if suggested in check_types else 0
        )

    run = st.button("🚀 เริ่มตรวจสอบ", disabled=(len(selected_cols) == 0))

    def validate(value, check_type):
        if pd.isnull(value):
            return "Missing"

        if check_type == "ตัวเลข":
            try:
                return "OK" if float(value) >= 0 else "ค่าติดลบ"
            except:
                return "ไม่ใช่ตัวเลข"

        elif check_type == "ข้อความ":
            return "OK" if str(value).strip() != "" else "ค่าว่าง"

        elif check_type == "รหัส (>=3 ตัวอักษร)":
            return "OK" if isinstance(value, str) and len(value) >= 3 else "รหัสสั้น"

        elif check_type == "วันที่":
            try:
                pd.to_datetime(value)
                return "OK"
            except:
                return "วันที่ผิด"

        return "Error"

    if run:
        result_df = df.copy()
        total = len(result_df)
        total_errors = 0

        progress = st.progress(0)

        for i, col in enumerate(selected_cols):
            result_df[col+"_Check"] = result_df[col].apply(lambda x: validate(x, col_types[col]))
            total_errors += (result_df[col+"_Check"] != "OK").sum()
            progress.progress((i+1)/len(selected_cols))

        accuracy = (1 - total_errors/(total*len(selected_cols))) * 100

        def error_cols(row):
            return ", ".join([col for col in selected_cols if row[col+"_Check"] != "OK"])

        result_df["คอลัมน์ที่ผิด"] = result_df.apply(error_cols, axis=1)

        result_df["error_count"] = result_df[[c+"_Check" for c in selected_cols]].apply(lambda x: (x!="OK").sum(), axis=1)

        st.session_state["result_df"] = result_df
        st.session_state["selected_cols"] = selected_cols
        st.session_state["accuracy"] = accuracy
        st.session_state["total"] = total
        st.session_state["errors"] = total_errors

        st.success("✅ ตรวจสอบข้อมูลเรียบร้อยแล้ว")

    if "result_df" in st.session_state:

        result_df = st.session_state["result_df"]
        selected_cols = st.session_state["selected_cols"]

        st.divider()

        st.markdown("## 📊 Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("จำนวนข้อมูล", st.session_state["total"])
        c2.metric("จำนวน Error", st.session_state["errors"])
        c3.metric("Accuracy (%)", f"{st.session_state['accuracy']:.2f}")

        st.markdown("## 🔍 ตัวกรอง")
        show_error_only = st.checkbox("แสดงเฉพาะข้อมูลที่มีข้อผิดพลาด")

        if show_error_only:
            display_df = result_df[result_df["คอลัมน์ที่ผิด"]!=""]
        else:
            display_df = result_df

        display_df = display_df.sort_values("error_count", ascending=False)

        st.divider()

        def highlight(row):
            styles = []
            for col in row.index:
                if col.endswith("_Check") or col in ["error_count","คอลัมน์ที่ผิด"]:
                    styles.append("")
                    continue

                check_col = col+"_Check"
                if check_col in row:
                    if row[check_col] == "Missing":
                        styles.append("background-color:#fff3cd")
                    elif row[check_col] != "OK":
                        styles.append("background-color:#f8d7da")
                    else:
                        styles.append("")
                else:
                    styles.append("")
            return styles

        st.markdown("## 📋 ตารางผลลัพธ์")
        st.write(display_df.style.apply(highlight, axis=1))

        st.divider()

        st.markdown("## 📉 จำนวน Error รายคอลัมน์")
        error_summary = {col:(result_df[col+"_Check"]!="OK").sum() for col in selected_cols}

        df_error = pd.DataFrame({
            "คอลัมน์": list(error_summary.keys()),
            "จำนวน Error": list(error_summary.values())
        })

        fig = px.bar(df_error, x="คอลัมน์", y="จำนวน Error", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("## 📊 คุณภาพข้อมูลรายคอลัมน์ (%)")

        col_quality = {}
        total = len(result_df)

        for col in selected_cols:
            ok = (result_df[col+"_Check"]=="OK").sum()
            col_quality[col] = (ok/total)*100

        df_quality = pd.DataFrame({
            "คอลัมน์": list(col_quality.keys()),
            "คุณภาพ (%)": list(col_quality.values())
        })

        fig2 = px.bar(df_quality, x="คอลัมน์", y="คุณภาพ (%)", text_auto=True)

        fig2.update_traces(
            marker_color=[
                "green" if v > 90 else "orange" if v > 70 else "red"
                for v in df_quality["คุณภาพ (%)"]
            ]
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        st.markdown("## 🚨 แถวที่มีข้อผิดพลาดมากที่สุด")
        top_error = result_df.sort_values("error_count", ascending=False).head(10)
        st.dataframe(top_error)

        worst = min(col_quality, key=col_quality.get)
        st.info(f"📌 คอลัมน์ที่ควรปรับปรุงมากที่สุด: {worst}")

        st.markdown("## 📥 ดาวน์โหลด")

        st.download_button("📄 ดาวน์โหลดทั้งหมด", result_df.to_csv(index=False), "result.csv")

        output = io.BytesIO()
        result_df.to_excel(output, index=False)
        st.download_button("📊 ดาวน์โหลด Excel", output.getvalue(), "result.xlsx")

        error_only = result_df[result_df["คอลัมน์ที่ผิด"]!=""]
        st.download_button("🚨 ดาวน์โหลดเฉพาะ Error", error_only.to_csv(index=False), "error_only.csv")