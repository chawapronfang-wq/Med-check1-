import streamlit as st
import pandas as pd

# ================= CONFIG =================
st.set_page_config(page_title="MRA Audit System", layout="wide")

# ================= LOGIN =================
users = {
    "admin": "1234",
    "coder": "1111"
}

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.title("🔐 Login - MRA System")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user in users and users[user] == pwd:
            st.session_state.login = True
            st.success("Login success")
        else:
            st.error("Invalid credentials")

if not st.session_state.login:
    login()
    st.stop()

# ================= HEADER =================
st.title("🏥 MRA Audit System")

# ================= FILE UPLOAD =================
uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx"])

# ================= RULE ENGINE =================
def check_mra(row):
    errors = []
    warnings = []

    # Completeness
    if pd.isna(row.get("Principal_dx")):
        errors.append("Missing Principal Dx")

    if pd.isna(row.get("LOS")):
        errors.append("Missing LOS")

    # Accuracy
    dx = str(row.get("Principal_dx"))
    if "." not in dx:
        warnings.append("Check ICD format")

    # Consistency
    if row.get("Sex") == "F" and "C61" in dx:
        errors.append("Prostate cancer in female")

    if row.get("LOS", 0) <= 0:
        errors.append("Invalid LOS")

    # Score
    score = max(0, 100 - (len(errors)*15 + len(warnings)*5))

    status = "✅ Pass"
    if errors:
        status = "❌ Error"
    elif warnings:
        status = "⚠️ Warning"

    return pd.Series([
        ", ".join(errors),
        ", ".join(warnings),
        score,
        status
    ])

# ================= MAIN =================
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip()

    required_cols = ["HN","AN","Sex","Age","Principal_dx","LOS"]
    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        st.error(f"Missing columns: {missing_cols}")
        st.stop()

    # Apply MRA
    df[["Errors","Warnings","Score","Status"]] = df.apply(check_mra, axis=1)

    # ================= DASHBOARD =================
    st.subheader("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    total = len(df)
    pass_rate = (df["Status"] == "✅ Pass").mean()*100
    avg_score = df["Score"].mean()

    col1.metric("Total Cases", total)
    col2.metric("Pass Rate (%)", f"{pass_rate:.2f}")
    col3.metric("Avg Score", f"{avg_score:.2f}")

    # ================= FILTER =================
    st.subheader("🔍 Filter")
    status_filter = st.selectbox("Select Status", ["All","✅ Pass","⚠️ Warning","❌ Error"])

    if status_filter != "All":
        df = df[df["Status"] == status_filter]

    # ================= TABLE =================
    st.subheader("📋 Result Table")
    st.dataframe(df, use_container_width=True)

    # ================= EXPORT =================
    st.download_button(
        "📥 Download CSV",
        df.to_csv(index=False),
        "mra_result.csv",
        "text/csv"
    )
