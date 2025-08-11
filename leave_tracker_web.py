import streamlit as st
import pandas as pd
from datetime import date

# Employee List
employees = [
    "Gupta Shamit", "Kartheesh Krishna", "Sukumaran Ramya",
    "Sarvagnamurthy Harish", "Valiyakandathil Fawas",
    "L Rajeswari", "Ravi Janani", "Kannan Pavithran",
    "Mahadev Bhavish", "Rao C Ramachandra", "Kummari Dhanunjaya"
]

# File to store leave data
leave_file = "leave_records.csv"

# Load existing data or create new
try:
    leave_data = pd.read_csv(leave_file)
except FileNotFoundError:
    leave_data = pd.DataFrame(columns=["Name", "Leave Date"])

st.title("Leave Tracker")

# Employee selection
name = st.selectbox("Select Employee", employees)

# Date selection
leave_date = st.date_input("Select Leave Date", date.today())

# Submit button
if st.button("Add Leave"):
    new_entry = pd.DataFrame([[name, leave_date]], columns=["Name", "Leave Date"])
    leave_data = pd.concat([leave_data, new_entry], ignore_index=True)
    leave_data.to_csv(leave_file, index=False)
    st.success(f"Leave added for {name} on {leave_date}")

# Display leave records
st.subheader("Leave Records")
st.dataframe(leave_data)
