from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

# Employees
EMPLOYEES = [
    "Gupta Shamit","Kartheesh Krishna","Sukumaran Ramya",
    "Sarvagnamurthy Harish","Valiyakandathil Fawas",
    "L Rajeswari","Ravi Janani","Kannan Pavithran",
    "Mahadev Bhavish","Rao C Ramachandra","Kummari Dhanunjaya"
]

DATA_FILE = "leave_data.csv"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        employee = request.form.get("employee")
        leave_date = request.form.get("leave_date")  # format YYYY-MM-DD

        if not employee or not leave_date:
            return render_template("index.html", employees=EMPLOYEES,
                                   error="Please select employee and date.")

        new_entry = pd.DataFrame(
            [[employee, leave_date, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]],
            columns=["Employee", "Leave Date", "Submitted At"]
        )

        if os.path.exists(DATA_FILE):
            new_entry.to_csv(DATA_FILE, mode="a", header=False, index=False)
        else:
            new_entry.to_csv(DATA_FILE, index=False)

        return redirect(url_for("success"))

    return render_template("index.html", employees=EMPLOYEES)

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/view")
def view():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["Employee", "Leave Date", "Submitted At"])
    table_html = df.to_html(index=False, classes="table table-striped", border=0)
    return render_template("view.html", table_html=table_html)

@app.route("/export")
def export():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["Employee", "Leave Date", "Submitted At"])

    bio = BytesIO()
    df.to_excel(bio, index=False, engine="openpyxl")
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name="leave_data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    # host='0.0.0.0' lets other devices on the same network access it.
    app.run(host="0.0.0.0", port=5000, debug=True)
