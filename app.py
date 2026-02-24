import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Smart Expense Tracker")

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    category TEXT,
    type TEXT,
    date TEXT
)
""")
conn.commit()

# ---------------- ADD TRANSACTION ---------------- #

st.sidebar.header("➕ Add Transaction")

amount = st.sidebar.number_input("Amount", min_value=0.0)
category = st.sidebar.selectbox("Category",
    ["Food", "Travel", "Rent", "Shopping", "Investment", "Savings"])
type_ = st.sidebar.selectbox("Type",
    ["expense", "investment", "saving"])
date = st.sidebar.date_input("Date")

if st.sidebar.button("Add Transaction"):
    cursor.execute(
        "INSERT INTO expenses (amount, category, type, date) VALUES (?, ?, ?, ?)",
        (amount, category, type_, str(date))
    )
    conn.commit()
    st.sidebar.success("Transaction Added!")

# ---------------- FETCH DATA ---------------- #

df = pd.read_sql_query("SELECT * FROM expenses", conn)

if df.empty:
    st.warning("No transactions yet.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["year_month"] = df["date"].dt.to_period("M").astype(str)

# ---------------- MONTH FILTER ---------------- #

st.header("📅 Monthly Analysis")

months = sorted(df["year_month"].unique(), reverse=True)
selected_month = st.selectbox("Select Month", months)

filtered_df = df[df["year_month"] == selected_month]

# ---------------- EXPENSE LIMIT ---------------- #

st.subheader("🎯 Set Monthly Expense Limit")

expense_limit = st.number_input("Enter Monthly Expense Limit", min_value=0.0)

expense_total = filtered_df[filtered_df["type"] == "expense"]["amount"].sum()
investment_total = filtered_df[filtered_df["type"] == "investment"]["amount"].sum()
saving_total = filtered_df[filtered_df["type"] == "saving"]["amount"].sum()

# ---------------- METRICS ---------------- #

col1, col2, col3 = st.columns(3)

col1.metric("🔴 Total Expense", f"₹{expense_total:,.2f}")
col2.metric("🔵 Total Investment", f"₹{investment_total:,.2f}")
col3.metric("🟢 Total Saving", f"₹{saving_total:,.2f}")

# ---------------- EXPENSE ALERT ---------------- #

if expense_limit > 0:
    if expense_total > expense_limit:
        st.error("🚨 ALERT: You are running over your monthly expense limit!")
    else:
        remaining = expense_limit - expense_total
        st.success(f"✅ You are within budget. Remaining: ₹{remaining:,.2f}")

# ---------------- WHO IS HIGHEST ---------------- #

st.subheader("📊 Monthly Financial Behavior")

max_value = max(expense_total, investment_total, saving_total)

if max_value == expense_total:
    st.markdown(
        "<h3 style='color:red;'>🔴 You spent the most this month.</h3>",
        unsafe_allow_html=True
    )
elif max_value == investment_total:
    st.markdown(
        "<h3 style='color:blue;'>🔵 You invested the most this month.</h3>",
        unsafe_allow_html=True
    )
elif max_value == saving_total:
    st.markdown(
        "<h3 style='color:green;'>🟢 You saved the most this month.</h3>",
        unsafe_allow_html=True
    )

# ---------------- LINE CHART ---------------- #

st.subheader("📈 Daily Expense Trend")

daily_expense = (
    filtered_df[filtered_df["type"] == "expense"]
    .groupby("date")["amount"]
    .sum()
)

if not daily_expense.empty:
    fig, ax = plt.subplots()
    ax.plot(daily_expense.index, daily_expense.values, marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.set_title("Daily Expense Trend")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ---------------- PIE CHART ---------------- #

st.subheader("🥧 Category Breakdown")

category_data = (
    filtered_df[filtered_df["type"] == "expense"]
    .groupby("category")["amount"]
    .sum()
)

if not category_data.empty:
    fig2, ax2 = plt.subplots()
    ax2.pie(category_data, labels=category_data.index, autopct="%1.1f%%")
    ax2.set_title("Category-wise Expense Distribution")
    st.pyplot(fig2)

# ---------------- EXCEL EXPORT ---------------- #

st.subheader("📤 Download Monthly Excel Report")

def generate_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Transactions")

        summary_df = pd.DataFrame({
            "Metric": ["Total Expense", "Total Investment", "Total Saving"],
            "Amount": [expense_total, investment_total, saving_total]
        })
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    return output.getvalue()

excel_file = generate_excel(filtered_df)

st.download_button(
    label="Download Excel Report",
    data=excel_file,
    file_name=f"expense_report_{selected_month}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)