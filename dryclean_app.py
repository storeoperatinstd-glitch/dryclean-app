import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dry Clean Central Audit", layout="wide")
st.title("🧺 Centralized Dry Cleaning Payment Audit Dashboard")

# --- INITIALIZE STATE FOR DYNAMIC STORES & RECORD KEEPING ---
if "store_list" not in st.session_state:
    st.session_state.store_list = ["Connaught Place", "Noida Sector 62", "Gurgaon Phase 3"]

if "software_records" not in st.session_state:
    # Default fallback data matching your uploaded spreadsheet template
    st.session_state.software_records = pd.DataFrame([
        {"Order Number": "T8593", "Customer Name": "savita singh", "Expected Amount": 1980.0},
        {"Order Number": "T8594", "Customer Name": "Nutan Chandra", "Expected Amount": 1000.0},
        {"Order Number": "T8595", "Customer Name": "Vedant", "Expected Amount": 240.0},
    ])

if "cloud_sim" not in st.session_state:
    st.session_state.cloud_sim = pd.DataFrame(columns=["Date", "Store Location", "Bill No (Order No)", "Customer Name", "Software Net Amount", "Notebook Amount Taken", "Payment Mode", "Status", "Remarks / Notes"])

# --- SIDEBAR: MATCHES THE PHYSICAL NOTEBOOK LAYOUT ---
st.sidebar.header("🏢 Branch Notebook Audit")

store_location = st.sidebar.selectbox("Select Your Store Branch:", st.session_state.store_list)

with st.sidebar.form("audit_form", clear_on_submit=True):
    audit_date = st.date_input("Date of Delivery", value=datetime.today())
    
    # Matches "Bill No" column from your notebook photos
    bill_no = st.text_input("Enter Bill No. / Order No. (e.g., T8593):").strip()
    
    # Live Crosscheck into your uploaded Software Excel sheet
    matching_order = st.session_state.software_records[st.session_state.software_records["Order Number"].astype(str).str.lower() == str(bill_no).lower()]
    
    if not matching_order.empty:
        software_net_amt = float(matching_order["Expected Amount"].values[0])
        cust_name = str(matching_order["Customer Name"].values[0])
        st.sidebar.markdown(f"✅ **System Found:** {cust_name} | **Expected Net:** ₹{software_net_amt}")
    else:
        software_net_amt = 0.0
        cust_name = "Not Uploaded / Manual Entry"
        if bill_no:
            st.sidebar.warning("⚠️ Bill No not found in current software upload.")
    
    # Matches "Amount" column from your notebook photos
    notebook_amt = st.number_input("Amount Written in Notebook (₹):", min_value=0.0, step=10.0)
    
    # Matches the payment status indicators from your notebook notes
    pay_mode = st.selectbox("Payment Mode / Status:", ["Cash", "Online / GPay / Paytm", "Balance Due / Customer Not Home"])
    staff_notes = st.text_input("Remarks / Special Notes")
    
    submit_audit = st.form_submit_button("Submit to Central Cloud")

    if submit_audit:
        if not bill_no:
            st.sidebar.error("Please enter a valid Bill Number!")
        else:
            if pay_mode == "Balance Due / Customer Not Home":
                final_status = "Held Up"
                notebook_amt = 0.0
            elif notebook_amt == software_net_amt:
                final_status = "Matched"
            else:
                final_status = "MISMATCH / DISCREPANCY"
                
            new_entry = pd.DataFrame([{
                "Date": audit_date.strftime("%Y-%m-%d"),
                "Store Location": store_location,
                "Bill No (Order No)": bill_no,
                "Customer Name": cust_name,
                "Software Net Amount": software_net_amt,
                "Notebook Amount Taken": notebook_amt,
                "Payment Mode": pay_mode,
                "Status": final_status,
                "Remarks / Notes": staff_notes
            }])
            
            st.session_state.cloud_sim = pd.concat([st.session_state.cloud_sim, new_entry], ignore_index=True)
            st.sidebar.success(f"Bill {bill_no} processed and matched successfully!")

# Notebook Image Reference Uploader
st.sidebar.markdown("---")
st.sidebar.header("📸 Upload Notebook Page")
uploaded_photo = st.sidebar.file_uploader("Upload page screenshot reference", type=["png", "jpg", "jpeg"])
if uploaded_photo is not None:
    st.sidebar.image(uploaded_photo, caption="Uploaded Notebook Reference", use_container_width=True)

# --- MAIN DASHBOARD INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🚨 Daily Cash Leakage Audits", "⏳ Held Up Payments Vault", "⚙️ Admin & Setup Panel"])

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
        
        # Total Shortage Calculation
        leakage = active_deliveries["Software Net Amount"].sum() - active_deliveries["Notebook Amount Taken"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Expected Revenue (System)", f"₹{active_deliveries['Software Net Amount'].sum():,.2f}")
        c2.metric("Total Cash Shortage / Leakage", f"₹{leakage:,.2f}", delta=f"-₹{leakage:,.2f}" if leakage > 0 else "0.00", delta_color="inverse")
    else:
        st.info("No reconciled billing entries logged yet for today.")

with tab2:
    if view_option != "All Stores Combined":
        filtered_df = st.session_state.cloud_sim[st.session_state.cloud_sim["Store Location"] == view_option]
    else:
        filtered_df = st.session_state.cloud_sim

    held_up_df = filtered_df[filtered_df["Status"] == "Held Up"]
    if not held_up_df.empty:
        st.warning(f"There are {len(held_up_df)} orders currently sitting as outstanding/unpaid balance items.")
        st.dataframe(held_up_df[["Date", "Store Location", "Bill No (Order No)", "Customer Name", "Software Net Amount", "Remarks / Notes"]], use_container_width=True, hide_index=True)
        st.metric("Total Outstanding Money Blocked", f"₹{held_up_df['Software Net Amount'].sum():,.2f}")
    else:
        st.success("Clean book! No pending held up balances found.")

with tab3:
    st.subheader("🛠️ Master Administrative Configuration")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Manage Store Locations")
        new_store = st.text_input("Type New Store Name to Add:")
        if st.button("➕ Add Branch"):
            if new_store and new_store not in st.session_state.store_list:
                st.session_state.store_list.append(new_store)
                st.success(f"Added {new_store}!")
                st.rerun()
                
        remove_store = st.selectbox("Select Store to Remove:", ["-- Select --"] + st.session_state.store_list)
        if st.button("❌ Remove Branch"):
            if remove_store != "-- Select --":
                st.session_state.store_list.remove(remove_store)
                st.warning(f"Removed {remove_store}")
                st.rerun()

    with col2:
        st.subheader("📁 Bulk Upload Software Bookings Excel")
        st.caption("Drop your standard software exported spreadsheet here.")
        
        uploaded_excel = st.file_uploader("Choose Excel file (.xlsx)", type=["xlsx"])
        if uploaded_excel is not None:
            try:
                user_df = pd.read_excel(uploaded_excel)
                
                if "Order No." in user_df.columns and "Net Amount" in user_df.columns:
                    clean_df = user_df[["Order No.", "Name", "Net Amount"]].copy()
                    clean_df = clean_df.rename(columns={
                        "Order No.": "Order Number",
                        "Name": "Customer Name",
                        "Net Amount": "Expected Amount"
                    })
                    st.session_state.software_records = clean_df
                    st.success(f"Successfully loaded {len(clean_df)} system billing records!")
                    st.dataframe(clean_df.head(5), use_container_width=True, hide_index=True)
                else:
                    st.error("Invalid File Layout! The sheet must contain 'Order No.' and 'Net Amount' columns.")
            except Exception as e:
                st.error(f"Error reading spreadsheet: {e}")
