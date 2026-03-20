elif menu == "📊 ตรวจข้อมูล":

    file = st.file_uploader("📁 อัปโหลดไฟล์", type=["xlsx","csv"])

    if file:
        try:
            # ================= READ =================
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            df = df.replace("None", None)

            # ================= BASIC CHECK =================
            def check_range(val, min_v, max_v):
                if pd.isna(val): return "Missing"
                if val < min_v or val > max_v: return "Invalid"
                return "OK"

            def check_gender(g):
                if pd.isna(g): return "Missing"
                if g not in ["Male","Female"]: return "Invalid"
                return "OK"

            def check_date(d):
                if pd.isna(d): return "Missing"
                try:
                    pd.to_datetime(d)
                    return "OK"
                except:
                    return "Invalid"

            def check_icd(code):
                if pd.isna(code): return "Missing"
                if re.match(r"^[A-Z][0-9]{2,3}$", str(code)):
                    return "OK"
                return "Invalid"

            def check_text(x):
                if pd.isna(x): return "Missing"
                if len(str(x)) < 3: return "Invalid"
                return "OK"

            # ================= APPLY =================
            if "Age" in df.columns:
                df["Age_error"] = df["Age"].apply(lambda x: check_range(x,0,120))

            if "Gender" in df.columns:
                df["Gender_error"] = df["Gender"].apply(check_gender)

            if "VisitDate" in df.columns:
                df["Date_error"] = df["VisitDate"].apply(check_date)

            if "DiagnosisCode" in df.columns:
                df["Diagnosis_error"] = df["DiagnosisCode"].apply(check_icd)

            if "DiagnosisText" in df.columns:
                df["DiagnosisText_error"] = df["DiagnosisText"].apply(check_text)

            if "Treatment" in df.columns:
                df["Treatment_error"] = df["Treatment"].apply(check_text)

            if "FollowUp" in df.columns:
                df["FollowUp_error"] = df["FollowUp"].apply(check_text)

            if "Doctor" in df.columns:
                df["Doctor_error"] = df["Doctor"].apply(check_text)

            error_cols = [c for c in df.columns if "_error" in c]

            # ================= MRA RUBRIC =================
            weights = {
                "Diagnosis_error": 0.25,
                "DiagnosisText_error": 0.20,
                "Treatment_error": 0.20,
                "FollowUp_error": 0.15,
                "Doctor_error": 0.10,
                "Date_error": 0.05,
                "Gender_error": 0.05
            }

            def calculate_score(row):
                score = 0
                total_weight = 0
                for col, w in weights.items():
                    if col in row:
                        val = row[col]
                        if val != "Missing":
                            total_weight += w
                            if val == "OK":
                                score += w
                return (score / total_weight) * 100 if total_weight else 0

            df["MRA_Score"] = df.apply(calculate_score, axis=1)

            def level(s):
                return "Good 🟢" if s>=90 else "Fair 🟡" if s>=70 else "Poor 🔴"

            df["MRA_Level"] = df["MRA_Score"].apply(level)

            # ================= ERROR FILTER =================
            error_mask = False
            for col in error_cols:
                error_mask |= (df[col] != "OK")

            error_df = df[error_mask]
            clean_df = df[~error_mask]

            # ================= DASHBOARD =================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("ทั้งหมด", len(df))
            c2.metric("ผิดพลาด", len(error_df))
            c3.metric("ค่าเฉลี่ย", f"{df['MRA_Score'].mean():.2f}%")
            c4.metric("Good 🟢", (df["MRA_Level"]=="Good 🟢").sum())
            st.markdown('</div>', unsafe_allow_html=True)

            # ================= QUALITY =================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📈 Data Quality")

            quality = {col:(df[col]=="OK").mean()*100 for col in error_cols}
            quality_df = pd.DataFrame({"Column":quality.keys(),"Quality":quality.values()})
            st.bar_chart(quality_df.set_index("Column"))

            st.markdown('</div>', unsafe_allow_html=True)

            # ================= ADVANCED =================
            st.subheader("📊 Advanced Analytics")

            st.write("### Score Distribution")
            st.bar_chart(df["MRA_Level"].value_counts())

            if "VisitDate" in df.columns:
                try:
                    df["VisitDate"] = pd.to_datetime(df["VisitDate"], errors="coerce")
                    trend = df.groupby(df["VisitDate"].dt.date)["MRA_Score"].mean()
                    st.line_chart(trend)
                except:
                    pass

            # ================= AI SUMMARY =================
            def ai_summary():
                total = len(df)
                poor = (df["MRA_Level"]=="Poor 🔴").sum()

                txt = f"Total: {total} | Poor: {poor}\n\n"

                if poor > total*0.3:
                    txt += "⚠️ ต้องปรับปรุงเร่งด่วน"
                elif poor > total*0.1:
                    txt += "⚠️ ควรปรับปรุงบางส่วน"
                else:
                    txt += "✅ คุณภาพดี"

                return txt

            st.warning(ai_summary())

            # ================= TABLE =================
            st.dataframe(df)

            # ================= DOWNLOAD =================
            st.download_button("📄 All", df.to_csv(index=False), "all.csv")
            st.download_button("🚨 Error", error_df.to_csv(index=False), "error.csv")
            st.download_button("🧹 Clean", clean_df.to_csv(index=False), "clean.csv")
            st.download_button("📊 Score", df.to_csv(index=False), "mra_score.csv")

        except Exception as e:
            st.error(f"❌ {e}")
