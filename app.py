import streamlit as st
import pandas as pd
import numpy as np
import re

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="MRA OPD", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.main {background-color:#f4f8fb;}
.header {background:linear-gradient(90deg,#0f3057,#008891);padding:20px;border-radius:12px;color:white;}
.card {background:white;padding:18px;border-radius:12px;margin-bottom:15px;box-shadow:0px 4px 12px rgba(0,0,0,0.08);}
.good {color:green;font-weight:bold;}
.fair {color:orange;font-weight:bold;}
.poor {color:red;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin":{"password":"1234"},"user":{"password":"1234"}}

if "login" not in st.session_state:
    st.session_state.login=False

def login():
    st.markdown("## 🔐 Login")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")
    if st.button("Login"):
        if u in users and users[u]["password"]==p:
            st.session_state.login=True
            st.rerun()
        else:
            st.error("Login failed")

if not st.session_state.login:
    login()
    st.stop()

# ================= HEADER =================
st.markdown('<div class="header"><h2>🏥 ระบบตรวจสอบเวชระเบียน (MRA OPD)</h2></div>',unsafe_allow_html=True)

# ================= MENU =================
menu=st.sidebar.radio("📂 เมนู",["🏠 หน้าแรก","📊 ตรวจข้อมูล"])
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu=="🏠 หน้าแรก":
    st.success("ระบบพร้อมใช้งาน")

# ================= DATA =================
elif menu=="📊 ตรวจข้อมูล":

    file=st.file_uploader("📁 อัปโหลดไฟล์",type=["xlsx","csv"])

    if file:
        df=pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

        # ===== CHECK =====
        def check_range(v,a,b):
            if pd.isna(v): return "Missing"
            if v<a or v>b: return "Invalid"
            return "OK"

        def check_text(v):
            if pd.isna(v): return "Missing"
            if len(str(v))<3: return "Invalid"
            return "OK"

        def check_icd(v):
            if pd.isna(v): return "Missing"
            if re.match(r"^[A-Z][0-9]{2,3}$",str(v)): return "OK"
            return "Invalid"

        if "Age" in df: df["Age_error"]=df["Age"].apply(lambda x:check_range(x,0,120))
        if "DiagnosisCode" in df: df["Diagnosis_error"]=df["DiagnosisCode"].apply(check_icd)
        if "DiagnosisText" in df: df["DiagnosisText_error"]=df["DiagnosisText"].apply(check_text)
        if "Treatment" in df: df["Treatment_error"]=df["Treatment"].apply(check_text)
        if "FollowUp" in df: df["FollowUp_error"]=df["FollowUp"].apply(check_text)
        if "Doctor" in df: df["Doctor_error"]=df["Doctor"].apply(check_text)

        error_cols=[c for c in df.columns if "_error" in c]

        # ===== ERROR COUNT =====
        df["Error_Count"]=df[error_cols].apply(lambda r:sum(v!="OK" for v in r),axis=1)

        # ===== CRITERIA =====
        criteria={
            "Diagnosis_error":{"name":"ICD-10","score":30},
            "DiagnosisText_error":{"name":"วินิจฉัย","score":20},
            "Treatment_error":{"name":"การรักษา","score":20},
            "FollowUp_error":{"name":"นัดติดตาม","score":15},
            "Doctor_error":{"name":"แพทย์","score":15}
        }

        # ===== SCORE =====
        def calc(row):
            s=0
            for col,v in criteria.items():
                if col in row and row[col]=="OK":
                    s+=v["score"]
            return s

        df["MRA_Score"]=df.apply(calc,axis=1)
        df["MRA_Level"]=df["MRA_Score"].apply(lambda x:"Good 🟢" if x>=90 else "Fair 🟡" if x>=70 else "Poor 🔴")

        # ===== FILTER =====
        filtered=df.copy()
        if "Doctor" in df:
            doc=st.selectbox("เลือกแพทย์",["All"]+list(df["Doctor"].dropna().unique()))
            if doc!="All": filtered=filtered[filtered["Doctor"]==doc]

        level=st.selectbox("เลือกระดับ",["All","Good 🟢","Fair 🟡","Poor 🔴"])
        if level!="All": filtered=filtered[filtered["MRA_Level"]==level]

        # ===== DASHBOARD =====
        c1,c2,c3=st.columns(3)
        c1.metric("จำนวน",len(filtered))
        c2.metric("คะแนนเฉลี่ย",f"{filtered['MRA_Score'].mean():.2f}")
        c3.metric("Error เฉลี่ย",f"{filtered['Error_Count'].mean():.2f}")

        st.bar_chart(filtered["MRA_Level"].value_counts())

        # ===== CASE VIEW =====
        st.markdown("## 🔍 วิเคราะห์รายเคส")

        idx=st.selectbox("เลือกเคส",filtered.index)
        case=filtered.loc[idx]

        # DETAIL
        detail=[]
        total=0
        got=0

        for col,v in criteria.items():
            if col in case:
                total+=v["score"]
                score=v["score"] if case[col]=="OK" else 0
                got+=score
                detail.append([v["name"],v["score"],score,case[col]])

        st.markdown(f"""
### 🧾 ผลการประเมิน
- คะแนนเต็ม: {total}
- ได้: {got}
- %: {(got/total)*100:.2f}
- ระดับ: {case['MRA_Level']}
""")

        st.dataframe(pd.DataFrame(detail,columns=["หัวข้อ","เต็ม","ได้","สถานะ"]))

        # ===== HIGHLIGHT TABLE =====
        def color(v):
            if v=="Missing": return "background-color:orange"
            if v=="Invalid": return "background-color:red;color:white"
            return ""

        st.dataframe(filtered.style.applymap(color,subset=error_cols))

        # ===== RANKING =====
        st.markdown("## 🏆 Ranking")
        st.dataframe(filtered.sort_values("MRA_Score",ascending=False).head(10))
        st.dataframe(filtered.sort_values("MRA_Score").head(10))

        # ===== PDF =====
        def export_pdf():
            doc=SimpleDocTemplate("report.pdf")
            styles=getSampleStyleSheet()
            content=[]
            content.append(Paragraph("รายงาน MRA OPD",styles["Title"]))
            content.append(Paragraph(f"คะแนน: {got}",styles["Normal"]))
            content.append(Spacer(1,10))
            content.append(Table([["หัวข้อ","เต็ม","ได้","สถานะ"]]+detail))
            doc.build(content)

        if st.button("📄 Export PDF"):
            export_pdf()
            with open("report.pdf","rb") as f:
                st.download_button("Download PDF",f,"report.pdf")
