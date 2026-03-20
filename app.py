import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Medical System", layout="wide")

# ================= USERS =================
users = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "1234", "role": "user"}
}

if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
def login():
    st.markdown("## 🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Login failed")

if not st.session_state.login:
    login()
    st.stop()

# ================= MENU =================
menu = st.sidebar.radio("📂 Menu", ["Home", "Data Check"])

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= HOME =================
if menu == "Home":
    st.success("✅ System Ready")

# ================= DATA CHECK =================
elif menu == "Data Check":

    file = st.file_uploader("📁 Upload File", type=["xlsx","csv"])

    if file:
        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            df = df.replace("None", None)

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
                if re.match(r"^[A-Z][0-9]{2,3}$", str(v)):
                    return "OK"
                return "Invalid"

            # ===== APPLY =====
            if "Age" in df: df["Age_error"]=df["Age"].apply(lambda x:check_range(x,0,120))
            if "DiagnosisCode" in df: df["Diagnosis_error"]=df["DiagnosisCode"].apply(check_icd)
            if "DiagnosisText" in df: df["DiagnosisText_error"]=df["DiagnosisText"].apply(check_text)
            if "Treatment" in df: df["Treatment_error"]=df["Treatment"].apply(check_text)
            if "FollowUp" in df: df["FollowUp_error"]=df["FollowUp"].apply(check_text)
            if "Doctor" in df: df["Doctor_error"]=df["Doctor"].apply(check_text)

            error_cols = [c for c in df.columns if "_error" in c]

            # ===== ERROR COUNT =====
            df["Error_Count"] = df[error_cols].apply(
                lambda r: sum([1 for v in r if v in ["Missing","Invalid"]]), axis=1
            ) if error_cols else 0

            # ===== MRA SCORE =====
            weights = {
                "Diagnosis_error":0.3,
                "DiagnosisText_error":0.2,
                "Treatment_error":0.2,
                "FollowUp_error":0.15,
                "Doctor_error":0.15
            }

            def calc(row):
                s,t=0,0
                for col,w in weights.items():
                    if col in row:
                        v=row[col]
                        if v!="Missing":
                            t+=w
                            if v=="OK": s+=w
                return (s/t)*100 if t else 0

            df["MRA_Score"]=df.apply(calc,axis=1)
            df["MRA_Level"]=df["MRA_Score"].apply(
                lambda x:"Good 🟢" if x>=90 else "Fair 🟡" if x>=70 else "Poor 🔴"
            )

            # ================= FILTER =================
            st.subheader("🔎 Filter")

            filtered_df = df.copy()

            c1,c2 = st.columns(2)

            if "Doctor" in df.columns:
                doctors = ["All"] + sorted(df["Doctor"].dropna().unique().tolist())
                doc = c1.selectbox("Doctor", doctors)
                if doc != "All":
                    filtered_df = filtered_df[filtered_df["Doctor"] == doc]

            level = c2.selectbox("Level", ["All","Good 🟢","Fair 🟡","Poor 🔴"])
            if level != "All":
                filtered_df = filtered_df[filtered_df["MRA_Level"] == level]

            # ================= DASHBOARD =================
            c1,c2,c3 = st.columns(3)
            c1.metric("Total", len(filtered_df))
            c2.metric("Avg Score", f"{filtered_df['MRA_Score'].mean():.2f}%")
            c3.metric("Avg Error", f"{filtered_df['Error_Count'].mean():.2f}")

            st.bar_chart(filtered_df["MRA_Level"].value_counts())

            # ================= ERROR SUMMARY =================
            if error_cols:
                err_sum={col:(filtered_df[col]!="OK").sum() for col in error_cols}
                err_df=pd.DataFrame({"Column":err_sum.keys(),"Errors":err_sum.values()})
                st.subheader("Top Errors")
                st.bar_chart(err_df.set_index("Column"))

            # ================= CASE VIEW =================
            st.subheader("🔍 วิเคราะห์รายเคส")

            if "PatientID" in filtered_df.columns:
                pid = st.selectbox("เลือกเคส", filtered_df["PatientID"])
                case = filtered_df[filtered_df["PatientID"]==pid].iloc[0]
            else:
                idx = st.selectbox("เลือก index", filtered_df.index)
                case = filtered_df.loc[idx]

            st.markdown(f"""
### 🧾 Result
- 🎯 Score: **{case['MRA_Score']:.2f}%**
- 📊 Level: **{case['MRA_Level']}**
- ❌ Errors: **{case['Error_Count']} จุด**
""")

            st.markdown("### 🔎 ปัญหาที่พบ")
            for col in error_cols:
                if case[col] != "OK":
                    st.write(f"❌ {col} → {case[col]}")

            st.markdown("### 📉 คะแนนที่หายไป")
            for col,w in weights.items():
                if col in case and case[col] != "OK":
                    st.write(f"- {col} (-{w*100:.0f}%)")

            # ================= TABLE =================
            def highlight(v):
                if v=="Missing": return "background-color:orange"
                if v=="Invalid": return "background-color:red;color:white"
                return ""

            def highlight_row(row):
                if row["Error_Count"]>=3:
                    return ["background-color:#ffcccc"]*len(row)
                elif row["Error_Count"]>=1:
                    return ["background-color:#fff0e6"]*len(row)
                return [""]*len(row)

            if error_cols:
                styled=filtered_df.style.apply(highlight_row,axis=1)\
                                        .applymap(highlight,subset=error_cols)
                st.dataframe(styled)
            else:
                st.dataframe(filtered_df)

            # ================= AI RECOMMEND =================
            st.subheader("🤖 Recommendation")

            for col in error_cols:
                count = (filtered_df[col]!="OK").sum()
                if count>0:
                    st.warning(f"{col}: พบ {count} เคส ควรปรับปรุง")

            # ================= DOWNLOAD =================
            st.download_button("📄 Download", filtered_df.to_csv(index=False), "result.csv")

        except Exception as e:
            st.error(f"❌ {e}")
