import pandas as pd
import numpy as np
import streamlit as st
import re

st.set_page_config(page_title="Medical Data Checker", page_icon="🏥", layout="wide")

st.title("🏥 Medical Data Quality Checker")

uploaded_file = st.file_uploader("📁 อัปโหลดไฟล์ (CSV / Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:

    # อ่านไฟล์
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # -------------------------
    # 🔍 ตรวจ DiagnosisCode (ICD-10)
    # -------------------------
    def check_icd(code):
        if pd.isna(code):
            return "Missing"
        pattern = r"^[A-Z][0-9]{2,3}$"
        if re.match(pattern, str(code)):
            return "OK"
        else:
            return "Invalid"

    df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

    # -------------------------
    # 🔍 ตรวจ Height
    # -------------------------
    def check_height(h):
        if pd.isna(h):
            return "Missing"
        elif h < 50 or h > 250:
            return "Invalid"
        else:
            return "OK"

    df["Height_error"] = df["Height"].apply(check_height)

    # -------------------------
    # 🔍 ตรวจ Age
    # -------------------------
    def check_age(a):
        if pd.isna(a):
            return "Missing"
        elif a < 0 or a > 120:
            return "Invalid"
        else:
            return "OK"

    df["Age_error"] = df["Age"].apply(check_age)

    # -------------------------
    # 🔍 ตรวจ Weight
    # -------------------------
    def check_weight(w):
        if pd.isna(w):
            return "Missing"
        elif w < 1 or w > 300:
            return "Invalid"
        else:
            return "OK"

    df["Weight_error"] = df["Weight"].apply(check_weight)

    # -------------------------
    # 🔍 ตรวจ Gender
    # -------------------------
    def check_gender(g):
        if pd.isna(g):
            return "Missing"
        elif g not in ["Male", "Female"]:
            return "Invalid"
        else:
            return "OK"

    df["Gender_error"] = df["Gender"].apply(check_gender)

    # -------------------------
    # 🔍 ตรวจ Date
    # -------------------------
    def check_date(d):
        try:
            pd.to_datetime(d)
            return "OK"
        except:
            return "Invalid"

    df["Date_error"] = df["VisitDate"].apply(lambda x: "Missing" if pd.isna(x) else check_date(x))

    # -------------------------
    # 📊 คำนวณ % คุณภาพ
    # -------------------------
    error_cols = [
        "Age_error", "Weight_error", "Height_error",
        "Gender_error", "Date_error", "Diagnosis_error"
    ]

    quality = {}
    for col in error_cols:
        ok = (df[col] == "OK").sum()
        quality[col] = (ok / len(df)) * 100

    overall = np.mean(list(quality.values()))

    # -------------------------
    # 🏆 Grade
    # -------------------------
    if overall >= 90:
        grade = "A 🟢"
    elif overall >= 80:
        grade = "B 🟡"
    else:
        grade = "C 🔴"

    # -------------------------
    # 📊 Dashboard
    # -------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("📄 จำนวนข้อมูล", len(df))
    c2.metric("📊 คุณภาพรวม (%)", f"{overall:.2f}%")
    c3.metric("🏆 เกรด", grade)

    st.subheader("📊 ความสมบูรณ์ของข้อมูล (%)")

    quality_df = pd.DataFrame({
        "Column": list(quality.keys()),
        "Quality (%)": list(quality.values())
    }).sort_values(by="Quality (%)")

    st.bar_chart(quality_df.set_index("Column"))

    # -------------------------
    # 🎨 highlight error
    # -------------------------
    def highlight(val):
        if val in ["Missing", "Invalid"]:
            return "background-color: red"
        return ""

    st.subheader("📋 ตารางข้อมูล (มีการตรวจสอบแล้ว)")
    st.dataframe(df.style.applymap(highlight, subset=error_cols))
