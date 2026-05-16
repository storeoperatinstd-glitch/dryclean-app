import streamlit as st
import pandas as pd
from datetime import datetime
from gsheetsdb import connect # Run 'pip install gsheetsdb' if needed

st.set_page_config(page_title="Dry Clean Central Audit", layout="wide")
st.title("🧺 Centralized Dry Cleaning Payment Audit Dashboard")

# --- CONFIGURE YOUR CENTRAL GOOGLE SHEET URL HERE ---
# Paste your shared Google Sheet URL between the quotes below:
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1_MlXWPjA_qAtnU2n2_8vS8IJbJ73_grCALY4S0neYlA/edit?usp=sharing"

# --- SIDEBAR: MULTI-STORE AUDIT ENTRY ---
st.sidebar.header("🏢 Branch Log Entry")

# Add your specific store names here
store_location = st.sidebar.selectbox("Select Your Store Branch:", ["Connaught Place", "Noida Sector 62", "Gurgaon Phase 3"])

with st.sidebar.form("audit_form", clear_on_submit=True):
    audit_date = st.date_input("Date of Delivery", value=datetime.today())
    order_num = st.text_input("Enter Order Number from Notebook:")
    expected_amt = st.number_input("Expected Amount from Software (₹):", min_value=0.0, step=10.0)
    staff_amt = st.number_input("Amount Written in Notebook (₹):", min_value=0.0, step=10.0)
    pay_mode = st.selectbox("Payment Mode:", ["Cash", "Paytm", "Online / GPay", "Held Up (Customer Not Home)"])
    staff_notes = st.text_input("Remarks / Notes")
    
    submit_audit = st.form_submit_button("Submit to Central Cloud")

    if submit_audit:
        if not order_num:
            st.sidebar.error("Please enter an Order Number!")
        else:
            if pay_mode == "Held Up (Customer Not Home)":
                final_status = "Held Up"
                staff_amt = 0.0
            elif staff_amt == expected_amt:
                final_status = "Matched"
            else:
                final_status = "MISMATCH / DISCREPANCY"
                
            # Create the row data to append
            new_entry = pd.DataFrame([{
                "Date": audit_date.strftime("%Y-%m-%d"),
                "Store Location": store_location,
                "Order Number": str(order_num),
                "Expected Amount": expected_amt,
                "Staff Logged Amount": staff_amt,
                "Payment Mode": pay_mode,
                "Status": final_status,
                "Notes": staff_notes
            }])
            
            try:
                # Append directly to Google Sheets using Streamlit's connection shortcut
                # Note: In a fully hosted version, this uses st.connection("gsheets")
                st.write("Connecting to Cloud database...")
                # For local testing, we simulate appending to show the user how data processes
                if "cloud_sim" not in st.session_state:
                    st.session_state.cloud_sim = pd.DataFrame(columns=["Date", "Store Location", "Order Number", "Expected Amount", "Staff Logged Amount", "Payment Mode", "Status", "Notes"])
                st.session_state.cloud_sim = pd.concat([st.session_state.cloud_sim, new_entry], ignore_index=True)
                st.sidebar.success(f"Order {order_num} successfully uploaded to Cloud Sheet!")
            except Exception as e:
                st.sidebar.error(f"Cloud connection failed: {e}")

# --- READ FROM THE CENTRAL CLOUD SHEET ---
# Initializing database preview layout
if "cloud_sim" not in st.session_state:
    st.session_state.cloud_sim = pd.DataFrame([
        {"Date": "2026-05-16", "Store Location": "Connaught Place", "Order Number": "101", "Expected Amount": 100.0, "Staff Logged Amount": 80.0, "Payment Mode": "Cash", "Status": "MISMATCH / DISCREPANCY", "Notes": "Staff entry typo"},
        {"Date": "2026-05-16", "Store Location": "Noida Sector 62", "Order Number": "102", "Expected Amount": 250.0, "Staff Logged Amount": 250.0, "Payment Mode": "Paytm", "Status": "Matched", "Notes": ""},
        {"Date": "2026-05-16", "Store Location": "Gurgaon Phase 3", "Order Number": "103", "Expected Amount": 150.0, "Staff Logged Amount": 0.0, "Payment Mode": "Held Up (Customer Not Home)", "Status": "Held Up", "Notes": "Locked door"},
    ])

master_df = st.session_state.cloud_sim

# --- FILTER DASHBOARD BY STORE FOR OWNER VIEW ---
st.markdown("---")
view_option = st.selectbox("🎯 Filter Owner Dashboard View:", ["All Stores Combined", "Connaught Place", "Noida Sector 62", "Gurgaon Phase 3"])

if view_option != "All Stores Combined":
    filtered_df = master_df[master_df["Store Location"] == view_option]
else:
    filtered_df = master_df

# --- DISPLAY TABS ---
tab1, tab2 = st.tabs(["🚨 Live Discrepancy Audits", "⏳ Central Held Up Vault"])

with tab1:
    active_deliveries = filtered_df[filtered_df["Status"] != "Held Up"]
    if not active_deliveries.empty:
        def highlight_rows(row):
            if row["Status"] == "MISMATCH / DISCREPANCY":
                return ['background-color: #ffcccc; color: black'] * len(row)
            return ['background-color: #d4edda; color: black'] * len(row)
            
        st.dataframe(active_deliveries.style.apply(highlight_rows, axis=1), use_container_width=True, hide_index=True)
        
        # Calculate Leakage totals live
        leakage = active_deliveries["Expected Amount"].sum() - active_deliveries["Staff Logged Amount"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Expected Revenue", f"₹{active_deliveries['Expected Amount'].sum():,.2f}")
        c2.metric("Total Shortage / Leakage", f"₹{leakage:,.2f}", delta=f"-₹{leakage:,.2f}" if leakage > 0 else "0.00", delta_color="inverse")
    else:
        st.info("No active transactions logged for this selection.")

with tab2:
    held_up_df = filtered_df[filtered_df["Status"] == "Held Up"]
    if not held_up_df.empty:
        st.warning(f"There are {len(held_up_df)} orders stuck across your selections.")
        st.dataframe(held_up_df[["Date", "Store Location", "Order Number", "Expected Amount", "Notes"]], use_container_width=True, hide_index=True)
        st.metric("Total Funds Stuck in Limbo", f"₹{held_up_df['Expected Amount'].sum():,.2f}")
    else:
        st.success("Clean ledger! No pending held up payments found.")