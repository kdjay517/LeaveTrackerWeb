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
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "From Date", "To Date", "No. of Days"])

    # Ensure all columns exist and are in the correct format
    for col in ["Name", "From Date", "To Date", "No. of Days"]:
        if col not in df.columns:
            df[col] = ""
    
    # Explicitly convert date columns to datetime objects for consistent handling
    df["From Date"] = pd.to_datetime(df["From Date"], errors="coerce")
    df["To Date"] = pd.to_datetime(df["To Date"], errors="coerce")
    
    return df

def save_data(df):
    """Saves the DataFrame to the Excel file."""
    df_to_save = df.copy()
    # Convert dates back to a date-only format before saving to Excel
    df_to_save["From Date"] = df_to_save["From Date"].dt.date
    df_to_save["To Date"] = df_to_save["To Date"].dt.date
    df_to_save.to_excel(EXCEL_FILE, index=False, encoding='utf-8')

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
    writer.close()
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
if "last_employee" not in st.session_state:
    st.session_state.last_employee = None
if "selected_row_index" not in st.session_state:
    st.session_state.selected_row_index = None

# Employee selection
name = st.selectbox("Select Employee", EMPLOYEES)

# Reset Shamit login if switching employee
if name != st.session_state.last_employee:
    st.session_state.logged_in = False
    st.session_state.selected_row_index = None
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
# ADMIN VIEW
# ========================
if name == "Gupta Shamit" and st.session_state.logged_in:
    st.subheader("📋 All Leave Records")
    
    if not leave_data.empty:
        months = leave_data['From Date'].dt.strftime('%B %Y').unique()
        selected_month = st.selectbox("Filter by Month", ["All"] + sorted(months))

        filtered_data = leave_data
        if selected_month != "All":
            filtered_data = leave_data[leave_data['From Date'].dt.strftime('%B %Y') == selected_month]

        # Convert date columns to DD-MMM-YYYY strings for display
        display_data = filtered_data.copy()
        display_data['From Date'] = display_data['From Date'].dt.strftime('%d-%b-%Y')
        display_data['To Date'] = display_data['To Date'].dt.strftime('%d-%b-%Y')
        st.dataframe(display_data.reset_index(drop=True), use_container_width=True)
        
        # Use a selectbox for a more reliable mobile experience
        st.markdown("---")
        st.subheader("Edit or Delete Leave Record")
        
        # Create a list of options for the selectbox and a mapping to original indices
        options_map = {
            f"{row['Name']} | {row['From Date'].strftime('%d-%b-%Y')} to {row['To Date'].strftime('%d-%b-%Y')}": index
            for index, row in filtered_data.iterrows()
        }
        
        options = ["Select a record to edit/delete"] + list(options_map.keys())
        selected_record_str = st.selectbox("Choose a record", options)
        
        selected_original_idx = None
        if selected_record_str != "Select a record to edit/delete":
            selected_original_idx = options_map[selected_record_str]

        # Check if a record is selected
        if selected_original_idx is not None:
            col1, col2 = st.columns(2)
            if col1.button("✏️ Edit Selected", key="edit_button"):
                st.session_state.edit_index = selected_original_idx
                st.rerun()
            if col2.button("🗑️ Delete Selected", key="delete_button"):
                # Use .drop() with the original index
                leave_data = leave_data.drop(selected_original_idx).reset_index(drop=True)
                save_data(leave_data)
                st.success("Leave deleted successfully")
                st.rerun()
    else:
        st.info("No leave records available.")

    # Add the download button
    st.markdown("---")
    st.download_button(
        label="⬇️ Download All Leave Records",
        data=to_excel(leave_data),
        file_name='leave_records.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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

    st.subheader(f"📋 {name}'s Leave Records")
    employee_leave_data = leave_data[leave_data['Name'] == name]

    if not employee_leave_data.empty:
      employee_leave_data['From Date'] = pd.to_datetime(employee_leave_data['From Date'])
      months = employee_leave_data['From Date'].dt.strftime('%B %Y').unique()
      selected_month = st.selectbox("Filter by Month", ["All"] + sorted(months))

      filtered_data = employee_leave_data
      if selected_month != "All":
          filtered_data = employee_leave_data[employee_leave_data['From Date'].dt.strftime('%B %Y') == selected_month]
      
      # Convert date columns to DD-MMM-YYYY strings for display
      display_data = filtered_data.copy()
      display_data['From Date'] = display_data['From Date'].dt.strftime('%d-%b-%Y')
      display_data['To Date'] = display_data['To Date'].dt.strftime('%d-%b-%Y')
      st.dataframe(display_data.reset_index(drop=True), use_container_width=True)
    else:
      st.info("No leave records available for you.")


# ========================
# EDIT MODE
# ========================
if "edit_index" in st.session_state and st.session_state.edit_index is not None and name == "Gupta Shamit" and st.session_state.logged_in:
    idx = st.session_state.edit_index
    row = leave_data.loc[idx]
    st.subheader("✏️ Edit Leave")
    
    with st.form(key="edit_form"):
        # Ensure we have datetime objects for st.date_input
        from_date_edit = pd.to_datetime(row["From Date"]).date() if pd.notnull(row["From Date"]) else date.today()
        to_date_edit = pd.to_datetime(row["To Date"]).date() if pd.notnull(row["To Date"]) else date.today()

        new_from_date = st.date_input("From Date", from_date_edit)
        new_to_date = st.date_input("To Date", to_date_edit)
        submit_button = st.form_submit_button("Save Changes")
        
        if submit_button:
            no_days = calculate_days(new_from_date, new_to_date)
            if new_from_date > new_to_date:
                st.error("From Date cannot be after To Date.")
            else:
                leave_data.loc[idx, "From Date"] = new_from_date
                leave_data.loc[idx, "To Date"] = new_to_date
                leave_data.loc[idx, "No. of Days"] = no_days
                save_data(leave_data)
                st.success("Leave updated successfully")
                st.session_state.edit_index = None
                st.rerun()
