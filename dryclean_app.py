import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dry Clean Central Audit", layout="wide")
st.title("🧺 Centralized Dry Cleaning Payment Audit Dashboard")

# --- INITIALIZE STATE FOR DYNAMIC STORES & EXCEL DATA ---
if "store_list" not in st.session_state:
    st.session_state.store_list = ["Connaught Place", "Noida Sector 62", "Gurgaon Phase 3"]

if "software_records" not in st.session_state:
    # Default placeholder records if no Excel is uploaded yet
    st.session_state.software_records = pd.DataFrame([
        {"Order Number": "101", "Customer": "Amit Kumar", "Expected Amount": 100.0},
        {"Order Number": "102", "Customer": "Neha Sharma", "Expected Amount": 250.0},
        {"Order Number": "103", "Customer": "Rahul Singh", "Expected Amount": 150.0},
    ])

if "cloud_sim" not in st.session_state:
    st.session_state.cloud_sim = pd.DataFrame(columns=["Date", "Store Location", "Order Number", "Expected Amount", "Staff Logged Amount", "Payment Mode", "Status", "Notes"])

# --- SIDEBAR: MULTI-STORE AUDIT ENTRY & PHOTO UPLOAD ---
st.sidebar.header("🏢 Branch Log Entry")

# 1. Store Names dynamically load from our list
store_location = st.sidebar.selectbox("Select Your Store Branch:", st.session_state.store_list)

with st.sidebar.form("audit_form", clear_on_submit=True):
    audit_date = st.date_input("Date of Delivery", value=datetime.today())
    order_num = st.text_input("Enter Order Number from Notebook:")
    
    # Try to automatically pull Expected Amount if order exists in uploaded Excel records
    matching_order = st.session_state.software_records[st.session_state.software_records["Order Number"].astype(str) == str(order_num)]
    suggested_amt = float(matching_order["Expected Amount"].values[0]) if not matching_order.empty else 0.0
    
    expected_amt = st.number_input("Expected Amount from Software (₹):", value=suggested_amt, step=10.0)
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
            
            st.session_state.cloud_sim = pd.concat([st.session_state.cloud_sim, new_entry], ignore_index=True)
            st.sidebar.success(f"Order {order_num} uploaded to master ledger!")

# 3. Notebook Page Photo Uploader brought back into the sidebar
st.sidebar.markdown("---")
st.sidebar.header("📸 Upload Notebook Page")
uploaded_photo = st.sidebar.file_uploader("Upload page screenshot reference", type=["png", "jpg", "jpeg"])
if uploaded_photo is not None:
    st.sidebar.image(uploaded_photo, caption="Uploaded Notebook Page Reference", use_container_width=True)


# --- MAIN INTERFACE TABS ---
tab1, tab2, tab3 = st.tabs(["🚨 Live Discrepancy Audits", "⏳ Central Held Up Vault", "⚙️ Admin & Setup Panel"])

# --- FILTER DASHBOARD BY STORE FOR OWNER VIEW ---
with tab1:
    view_option = st.selectbox("🎯 Filter Owner Dashboard View:", ["All Stores Combined"] + st.session_state.store_list)
    if view_option != "All Stores Combined":
        filtered_df = st.session_state.cloud_sim[st.session_state.cloud_sim["Store Location"] == view_option]
    else:
        filtered_df = st.session_state.cloud_sim

    active_deliveries = filtered_df[filtered_df["Status"] != "Held Up"]
    if not active_deliveries.empty:
        def highlight_rows(row):
            if row["Status"] == "MISMATCH / DISCREPANCY":
                return ['background-color: #ffcccc; color: black'] * len(row)
            return ['background-color: #d4edda; color: black'] * len(row)
            
        st.dataframe(active_deliveries.style.apply(highlight_rows, axis=1), use_container_width=True, hide_index=True)
        
        leakage = active_deliveries["Expected Amount"].sum() - active_deliveries["Staff Logged Amount"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Expected Revenue", f"₹{active_deliveries['Expected Amount'].sum():,.2f}")
        c2.metric("Total Shortage / Leakage", f"₹{leakage:,.2f}", delta=f"-₹{leakage:,.2f}" if leakage > 0 else "0.00", delta_color="inverse")
    else:
        st.info("No active mismatch transactions logged yet.")

with tab2:
    if view_option != "All Stores Combined":
        filtered_df = st.session_state.cloud_sim[st.session_state.cloud_sim["Store Location"] == view_option]
    else:
        filtered_df = st.session_state.cloud_sim

    held_up_df = filtered_df[filtered_df["Status"] == "Held Up"]
    if not held_up_df.empty:
        st.warning(f"There are {len(held_up_df)} orders stuck in delivery limbo.")
        st.dataframe(held_up_df[["Date", "Store Location", "Order Number", "Expected Amount", "Notes"]], use_container_width=True, hide_index=True)
        st.metric("Total Funds Stuck in Limbo", f"₹{held_up_df['Expected Amount'].sum():,.2f}")
    else:
        st.success("Clean ledger! No pending held up payments found.")

# --- NEW: ADMIN PANEL TO SOLVE PROBLEMS 1 AND 2 ---
with tab3:
    st.subheader("🛠️ Master Administrative Configuration")
    st.markdown("---")
    
    # PROBLEM 1 SOLVED: Dynamic Store Management
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Manage Store Locations")
        st.write("Current Branches:", st.session_state.store_list)
        
        new_store = st.text_input("Type New Store Name to Add:")
        if st.button("➕ Add Branch"):
            if new_store and new_store not in st.session_state.store_list:
                st.session_state.store_list.append(new_store)
                st.success(f"Added {new_store} successfully!")
                st.rerun()
                
        remove_store = st.selectbox("Select Store to Remove:", ["-- Select --"] + st.session_state.store_list)
        if st.button("❌ Remove Branch"):
            if remove_store != "-- Select --":
                st.session_state.store_list.remove(remove_store)
                st.warning(f"Removed {remove_store}")
                st.rerun()

    # PROBLEM 2 SOLVED: Upload Store's System Excel 
    with col2:
        st.subheader("📁 Bulk Upload Software Bookings Excel")
        st.write("Upload your master daily sheet pulled from your store software here to update order amounts automatically.")
        
        uploaded_excel = st.file_uploader("Choose Excel file (.xlsx)", type=["xlsx"])
        if uploaded_excel is not None:
            try:
                # Read the uploaded sheet into memory
                user_df = pd.read_excel(uploaded_excel)
                
                # Check for necessary columns to prevent script breakages
                if "Order Number" in user_df.columns and "Expected Amount" in user_df.columns:
                    st.session_state.software_records = user_df
                    st.success(f"Successfully loaded {len(user_df)} system billing records!")
                    st.dataframe(user_df.head(5), use_container_width=True) # show preview
                else:
                    st.error("Excel must contain exactly an 'Order Number' column and an 'Expected Amount' column.")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
