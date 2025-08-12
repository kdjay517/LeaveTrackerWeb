import streamlit as st
import pandas as pd
import os
from datetime import date
from io import BytesIO

# ========================
# CONFIG
# ========================
EMPLOYEES = [
    "Gupta Shamit", "Kartheesh Krishna", "Sukumaran Ramya",
    "Sarvagnamurthy Harish", "Valiyakandathil Fawas",
    "L Rajeswari", "Ravi Janani", "Kannan Pavithran",
    "Mahadev Bhavish", "Rao C Ramachandra", "Kummari Dhanunjaya"
]
EXCEL_FILE = "leave_records.xlsx"
ADMIN_USER = "shamit"
ADMIN_PASS = "password123"

# ========================
# CREATE FRESH SHEET IF NOT EXISTS
# ========================
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=["Name", "From Date", "To Date", "No. of Days"])
    df_init.to_excel(EXCEL_FILE, index=False, encoding='utf-8')


# ========================
# HELPER FUNCTIONS
# ========================
def load_data():
    """Loads leave data from the Excel file, or creates an empty DataFrame if the file doesn't exist."""
    try:
        # Explicitly set the encoding to UTF-8 to prevent file encoding errors
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "From Date", "To Date", "No. of Days"])

    # Ensure all columns exist and are in the correct format
    for col in ["Name", "From Date", "To Date", "No. of Days"]:
        if col not in df.columns:
            df[col] = ""

    # Explicitly convert date columns to datetime objects to avoid the AttributeError
    df["From Date"] = pd.to_datetime(df["From Date"], errors="coerce")
    df["To Date"] = pd.to_datetime(df["To Date"], errors="coerce")

    # After conversion, convert back to date objects for display and calculation
    df["From Date"] = df["From Date"].dt.date
    df["To Date"] = df["To Date"].dt.date

    return df


def save_data(df):
    """Saves the DataFrame to the Excel file."""
    # Explicitly set the encoding to UTF-8
    df.to_excel(EXCEL_FILE, index=False, encoding='utf-8')


def calculate_days(from_date, to_date):
    """Calculates the number of days between two dates."""
    if from_date and to_date:
        return (to_date - from_date).days + 1
    return 0


def to_excel(df):
    """Converts a DataFrame to an in-memory Excel file."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # Use writer.close() instead of writer.save()
    processed_data = output.getvalue()
    return processed_data


# ========================
# UI START
# ========================
st.set_page_config(page_title="Leave Tracker", page_icon="📅", layout="centered")
st.title("📅 Leave Tracker")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "last_employee" not in st.session_state:
    st.session_state.last_employee = None

# Employee selection
name = st.selectbox("Select Employee", EMPLOYEES)

# Reset Shamit login if switching employee
if name != st.session_state.last_employee:
    st.session_state.logged_in = False
    st.session_state.edit_index = None
st.session_state.last_employee = name

# Admin login
if name == "Gupta Shamit" and not st.session_state.logged_in:
    st.markdown("<h4>🔒 Admin Login</h4>", unsafe_allow_html=True)
    login_id = st.text_input("Login ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_id == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.logged_in = True
            st.success("✅ Logged in as Admin")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# Load data
leave_data = load_data()


# ========================
# DYNAMIC TABLE DISPLAY FUNCTION
# ========================
def display_table_with_actions(df, is_admin):
    """
    Displays a DataFrame with optional Edit and Delete buttons for each row.
    This function replaces the old HTML table generation.
    """
    if df.empty:
        st.info("No leave records available.")
        return

    # Use st.columns to create a dynamic table-like layout with buttons
    cols = st.columns([1, 3, 2, 2, 2, 1, 1] if is_admin else [1, 3, 2, 2, 2])

    # Header
    headers = ["S.No", "Name", "From Date", "To Date", "No. of Days"]
    if is_admin:
        headers.extend(["Edit", "Delete"])

    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")

    st.divider()

    # Rows with buttons
    for idx, row in df.iterrows():
        display_cols = st.columns([1, 3, 2, 2, 2, 1, 1] if is_admin else [1, 3, 2, 2, 2])

        # Display data
        display_cols[0].write(idx + 1)
        # Handle cases where `row['Name']` might be missing or an unexpected type
        display_cols[1].write(row.get('Name', 'N/A'))

        # Safely display dates
        from_date_str = row['From Date'].strftime("%d-%m-%Y") if pd.notnull(row['From Date']) else 'N/A'
        to_date_str = row['To Date'].strftime("%d-%m-%Y") if pd.notnull(row['To Date']) else 'N/A'

        display_cols[2].write(from_date_str)
        display_cols[3].write(to_date_str)
        display_cols[4].write(row['No. of Days'])

        # Admin action buttons
        if is_admin:
            if display_cols[5].button("✏️", key=f"edit_btn_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()
            if display_cols[6].button("🗑️", key=f"delete_btn_{idx}"):
                st.session_state.delete_index = idx
                st.rerun()


# ========================
# Handle Delete via session state
# ========================
if "delete_index" in st.session_state and st.session_state.delete_index is not None:
    del_idx = st.session_state.delete_index
    leave_data = leave_data.drop(del_idx).reset_index(drop=True)
    save_data(leave_data)
    st.success("Leave deleted successfully")
    st.session_state.delete_index = None  # Reset the state
    st.rerun()

# ========================
# ADMIN VIEW
# ========================
if name == "Gupta Shamit" and st.session_state.logged_in:
    st.subheader("📜 All Leave Records")
    # Add a month filter for the admin view
    # Ensure there is data before attempting to get unique months
    if not leave_data.empty:
        leave_data['From Date'] = pd.to_datetime(leave_data['From Date'])
        months = leave_data['From Date'].dt.strftime('%B %Y').unique()
        selected_month = st.selectbox("Filter by Month", ["All"] + sorted(months))

        filtered_data = leave_data
        if selected_month != "All":
            filtered_data = leave_data[leave_data['From Date'].dt.strftime('%B %Y') == selected_month]
            filtered_data['From Date'] = filtered_data['From Date'].dt.date

        display_table_with_actions(filtered_data.reset_index(drop=True), is_admin=True)

        # Add the download button
        st.markdown("---")
        st.download_button(
            label="⬇️ Download Leave Records",
            data=to_excel(leave_data),
            file_name='leave_records.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("No leave records available.")

# ========================
# EMPLOYEE VIEW
# ========================
else:
    st.subheader("📋 Add Your Leave")
    from_date = st.date_input("From Date", date.today())
    to_date = st.date_input("To Date", date.today())
    if st.button("Add Leave"):
        no_days = calculate_days(from_date, to_date)
        if from_date > to_date:
            st.error("From Date cannot be after To Date.")
        else:
            new_entry = pd.DataFrame([[name, from_date, to_date, no_days]],
                                     columns=["Name", "From Date", "To Date", "No. of Days"])
            leave_data = pd.concat([leave_data, new_entry], ignore_index=True)
            save_data(leave_data)
            st.success(f"Leave added: {from_date} → {to_date} ({no_days} days)")

    st.subheader("📜 All Leave Records")
    # Add a month filter for the employee view
    if not leave_data.empty:
        leave_data['From Date'] = pd.to_datetime(leave_data['From Date'])
        months = leave_data['From Date'].dt.strftime('%B %Y').unique()
        selected_month = st.selectbox("Filter by Month", ["All"] + sorted(months))

        filtered_data = leave_data
        if selected_month != "All":
            filtered_data = leave_data[leave_data['From Date'].dt.strftime('%B %Y') == selected_month]
            filtered_data['From Date'] = filtered_data['From Date'].dt.date

        display_table_with_actions(filtered_data.reset_index(drop=True), is_admin=False)
    else:
        st.info("No leave records available.")

# ========================
# EDIT MODE
# ========================
if st.session_state.edit_index is not None and name == "Gupta Shamit" and st.session_state.logged_in:
    idx = st.session_state.edit_index
    row = leave_data.loc[idx]
    st.subheader(f"✏️ Edit Leave - {row['Name']}")

    # Use form to group inputs and button to prevent rerun on input change
    with st.form(key="edit_form"):
        from_date = st.date_input("From Date", row["From Date"])
        to_date = st.date_input("To Date", row["To Date"])
        submit_button = st.form_submit_button("Save Changes")

        if submit_button:
            no_days = calculate_days(from_date, to_date)
            if from_date > to_date:
                st.error("From Date cannot be after To Date.")
            else:
                leave_data.loc[idx, "From Date"] = from_date
                leave_data.loc[idx, "To Date"] = to_date
                leave_data.loc[idx, "No. of Days"] = no_days
                save_data(leave_data)
                st.success("Leave updated successfully")
                st.session_state.edit_index = None  # Reset the state
                st.rerun()
