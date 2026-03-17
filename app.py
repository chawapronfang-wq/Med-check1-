# ---------- DOWNLOAD ZONE ----------
st.subheader("📥 ดาวน์โหลดข้อมูล")

# 1. ดาวน์โหลดทั้งหมด
st.download_button(
    "📄 ดาวน์โหลดข้อมูลทั้งหมด",
    df.to_csv(index=False),
    file_name="all_data.csv"
)

# 2. ดาวน์โหลดเฉพาะ error
error_df = df[
    df.isnull().any(axis=1) |
    (df.filter(like="_error").any(axis=1))
]

st.download_button(
    "🚨 ดาวน์โหลดเฉพาะ Error",
    error_df.to_csv(index=False),
    file_name="error_data.csv"
)

# 3. ดาวน์โหลดเฉพาะข้อมูลที่ถูกต้อง
clean_df = df[
    ~(df.isnull().any(axis=1) |
      (df.filter(like="_error").any(axis=1)))
]

st.download_button(
    "🧹 ดาวน์โหลดข้อมูลที่ถูกต้อง",
    clean_df.to_csv(index=False),
    file_name="clean_data.csv"
)

# 4. Summary (Missing + Error)
summary = pd.DataFrame({
    "Column": df.columns,
    "Missing": df.isnull().sum().values
})

st.download_button(
    "📊 ดาวน์โหลด Summary",
    summary.to_csv(index=False),
    file_name="summary.csv"
)

# 5. Column Quality %
quality = {}
total = len(df)

for col in df.columns:
    ok = df[col].notnull().sum()
    quality[col] = (ok / total) * 100

quality_df = pd.DataFrame({
    "Column": list(quality.keys()),
    "Quality (%)": list(quality.values())
})

st.download_button(
    "📈 ดาวน์โหลดคุณภาพรายคอลัมน์",
    quality_df.to_csv(index=False),
    file_name="column_quality.csv"
)
