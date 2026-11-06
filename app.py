"""
Smart Parking Management System (Dynamic Slots & Custom Entry Edition)
Streamlit Web SaaS + Dynamic Slot Creation + Custom Vehicle Inputs + Rupee Billing + SQLite
"""
import streamlit as st
import sqlite3
import time
import pandas as pd
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "parking_web.db")

# Page Config
st.set_page_config(
    page_title="Smart Parking Hub",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme CSS Styling
st.markdown("""
<style>
    .main { background-color: #090d16; color: #f8fafc; }
    .stSidebar { background-color: #0f172a; }
    .card-available {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        border: 2px solid #10b981;
        padding: 18px;
        border-radius: 12px;
        color: #a7f3d0;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .card-occupied {
        background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
        border: 2px solid #ef4444;
        padding: 18px;
        border-radius: 12px;
        color: #fecaca;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .card-user {
        background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
        border: 2px solid #6366f1;
        padding: 18px;
        border-radius: 12px;
        color: #c7d2fe;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3 { color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

# Tiered Pricing Configuration in INR
PRICING_TIERS = {
    "Bike": {"base_fee": 15.0, "per_min": 1.0},
    "Sedan": {"base_fee": 30.0, "per_min": 2.5},
    "SUV": {"base_fee": 50.0, "per_min": 4.0}
}

# Initialize Database with expanded slots
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            zone TEXT,
            occupied INTEGER,
            vehicle TEXT,
            vehicle_type TEXT,
            checkin_time TEXT,
            checkin_epoch REAL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS checkout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle TEXT,
            vehicle_type TEXT,
            checkin_time TEXT,
            checkout_time TEXT,
            duration_mins REAL,
            fee REAL
        )""")
        
        # Seed initial expanded slots if empty
        count = con.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
        if count == 0:
            initial = [
                ("Bay A-01", "Ground Floor (A-Zone)", 0, "", "", "", 0),
                ("Bay A-02", "Ground Floor (A-Zone)", 0, "", "", "", 0),
                ("Bay A-03", "Ground Floor (A-Zone)", 0, "", "", "", 0),
                ("Bay A-04", "Ground Floor (A-Zone)", 0, "", "", "", 0),
                ("Bay A-05", "Ground Floor (A-Zone)", 0, "", "", "", 0),
                ("Bay B-01", "Basement (B-Zone)", 0, "", "", "", 0),
                ("Bay B-02", "Basement (B-Zone)", 0, "", "", "", 0),
                ("Bay B-03", "Basement (B-Zone)", 0, "", "", "", 0),
                ("Bay B-04", "Basement (B-Zone)", 0, "", "", "", 0),
                ("Bay B-05", "Basement (B-Zone)", 0, "", "", "", 0),
                ("VIP Bay 1", "VIP Zone", 0, "", "", "", 0),
                ("VIP Bay 2", "VIP Zone", 0, "", "", "", 0),
                ("VIP Bay 3", "VIP Zone", 0, "", "", "", 0),
                ("VIP Bay 4", "VIP Zone", 0, "", "", "", 0),
            ]
            con.executemany("INSERT INTO slots (name, zone, occupied, vehicle, vehicle_type, checkin_time, checkin_epoch) VALUES (?,?,?,?,?,?,?)", initial)

init_db()

# Database Helper Functions
def get_slots():
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql("SELECT * FROM slots", con)

def update_slot(slot_id, occupied, vehicle, v_type, checkin_t, checkin_ep):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("UPDATE slots SET occupied=?, vehicle=?, vehicle_type=?, checkin_time=?, checkin_epoch=? WHERE id=?",
                    (occupied, vehicle, v_type, checkin_t, checkin_ep, slot_id))

def add_new_slot(name, zone):
    with sqlite3.connect(DB_PATH) as con:
        try:
            con.execute("INSERT INTO slots (name, zone, occupied, vehicle, vehicle_type, checkin_time, checkin_epoch) VALUES (?,?,0,'','','',0)", (name, zone))
            return True
        except sqlite3.IntegrityError:
            return False

# --- SIDEBAR NAVIGATION & LOGIN ---
st.sidebar.markdown("# 🅿️ Smart Parking Hub")
st.sidebar.markdown("---")

role = st.sidebar.selectbox("Select Portal Access", ["Customer Portal", "Admin Control Center"])

if role == "Customer Portal":
    customer_name = st.sidebar.text_input("Enter Your Name / Driver ID", value="", placeholder="e.g. Rahul Sharma")
    admin_mode = False
else:
    admin_pass = st.sidebar.text_input("Admin Password", type="password", value="")
    admin_mode = True
    customer_name = "Admin"

st.sidebar.markdown("---")

# Dynamic Slot Creation Feature (Admin Only)
if admin_mode and admin_pass == "admin123":
    st.sidebar.markdown("### ➕ Add New Parking Slot")
    new_bay_name = st.sidebar.text_input("New Slot Name", placeholder="e.g. Bay A-06")
    new_bay_zone = st.sidebar.selectbox("Zone", ["Ground Floor (A-Zone)", "Basement (B-Zone)", "VIP Zone", "Roof Level"])
    
    if st.sidebar.button("Add Slot to Lot", type="secondary"):
        if new_bay_name.strip():
            if add_new_slot(new_bay_name.strip(), new_bay_zone):
                st.sidebar.success(f"Added '{new_bay_name}' to {new_bay_zone}!")
                st.rerun()
            else:
                st.sidebar.error("A slot with this name already exists!")
        else:
            st.sidebar.error("Please enter a slot name.")

st.sidebar.markdown("### 📊 System Status")
df_slots = get_slots()
total_bays = len(df_slots)
occupied_bays = int(df_slots["occupied"].sum())
available_bays = total_bays - occupied_bays

st.sidebar.metric("Total Capacity", total_bays)
st.sidebar.metric("Available Bays", available_bays, delta=f"{available_bays} free")
st.sidebar.metric("Occupied Bays", occupied_bays)

# --- MAIN DASHBOARD INTERFACE ---
if admin_mode and admin_pass != "admin123":
    st.error("🔒 Please enter the correct admin password in the sidebar (`admin123`) to access controls.")
    st.stop()

if admin_mode:
    st.title("👑 Admin Control & Operations Dashboard")
    st.markdown("Monitor real-time floor occupancy, assign incoming vehicles, process checkout billing, or add extra slots.")
    
    # Revenue Metrics Bar
    with sqlite3.connect(DB_PATH) as con:
        rev_res = con.cursor().execute("SELECT SUM(fee) FROM checkout_logs").fetchone()[0]
        total_revenue = rev_res if rev_res else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Capacity", total_bays)
    col2.metric("Available Bays", available_bays)
    col3.metric("Occupied Bays", occupied_bays)
    col4.metric("Total Revenue Collected", f"₹{total_revenue:.2f}")
    
    st.markdown("---")

    # Gate Check-In Form (Custom Inputs)
    with st.expander("🚗 Manual Vehicle Entry & Check-In", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            in_veh = st.text_input("Vehicle Registration Number", value="", placeholder="e.g. KA-01-AB-1234")
        with c2:
            in_type = st.selectbox("Vehicle Category (Pricing Tier)", ["Sedan", "SUV", "Bike"])
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Check-In Vehicle", type="primary", use_container_width=True):
                if not in_veh.strip():
                    st.error("Please enter a vehicle registration number.")
                else:
                    vacant = df_slots[df_slots["occupied"] == 0]
                    if not vacant.empty:
                        target = vacant.iloc[0]
                        update_slot(int(target["id"]), 1, in_veh.strip().upper(), in_type, time.strftime("%H:%M:%S"), time.time())
                        st.success(f"Parked {in_type} '{in_veh.strip().upper()}' at {target['zone']} [{target['name']}]!")
                        st.rerun()
                    else:
                        st.error("Parking lot is fully occupied!")

else:
    display_driver = customer_name if customer_name.strip() else "Guest Driver"
    st.title(f"👤 Customer Portal | Driver: {display_driver}")
    st.markdown("View live parking floor maps, check slot availability, or reserve your vehicle slot.")
    
    with st.expander("🚗 Park Vehicle", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            cust_veh = st.text_input("Enter Your Vehicle ID / Number", value="", placeholder="e.g. DL-04-XY-9876")
        with c2:
            cust_type = st.selectbox("Select Vehicle Type", ["Sedan", "SUV", "Bike"])
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Park Now", type="primary", use_container_width=True):
                if not cust_veh.strip():
                    st.error("Please enter your vehicle number.")
                else:
                    vacant = df_slots[df_slots["occupied"] == 0]
                    if not vacant.empty:
                        target = vacant.iloc[0]
                        update_slot(int(target["id"]), 1, cust_veh.strip().upper(), cust_type, time.strftime("%H:%M:%S"), time.time())
                        st.success(f"Assigned bay {target['name']} ({target['zone']}) to your vehicle!")
                        st.rerun()
                    else:
                        st.error("Sorry, all parking bays are fully occupied!")

st.markdown("---")
st.markdown("## 🗺️ Architectural Floor Map & Live Parking Bays")

# Render Map by Zones
zones = df_slots["zone"].unique()
if len(zones) > 0:
    zone_tabs = st.tabs([f"🏢 {z}" for z in zones])

    for i, zone in enumerate(zones):
        with zone_tabs[i]:
            st.markdown(f"**Floor Plan Layout — {zone}**")
            zone_df = df_slots[df_slots["zone"] == zone]
            
            # Display slots dynamically in grid rows of 4
            cols_per_row = 4
            rows = [zone_df.iloc[j:j+cols_per_row] for j in range(0, len(zone_df), cols_per_row)]
            
            for row_df in rows:
                cols = st.columns(cols_per_row)
                for idx, (_, row) in enumerate(row_df.iterrows()):
                    with cols[idx]:
                        is_occ = row["occupied"] == 1
                        is_my_car = (not admin_mode) and customer_name.strip() and (customer_name.lower() in str(row["vehicle"]).lower())
                        
                        if is_occ:
                            if is_my_car:
                                card_class = "card-user"
                                status_title = f"⭐ {row['name']} [YOUR VEHICLE]"
                            else:
                                card_class = "card-occupied"
                                status_title = f"🛑 {row['name']} [OCCUPIED]"
                            
                            elapsed = int((time.time() - row["checkin_epoch"]) / 60)
                            card_body = f"**Type:** {row['vehicle_type']}<br>**Veh:** {row['vehicle']}<br>⏱️ Parked: {elapsed} mins ago"
                        else:
                            card_class = "card-available"
                            status_title = f"🅿️ {row['name']} [VACANT]"
                            card_body = "<br>Status: Ready for Parking<br><br>"

                        st.markdown(f"""
                        <div class="{card_class}">
                            <h4>{status_title}</h4>
                            <p>{card_body}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                        if is_occ:
                            if admin_mode:
                                if st.button(f"Checkout ({row['name']})", key=f"btn_{row['id']}", use_container_width=True):
                                    # Calculate Bill
                                    duration_mins = max(1.0, (time.time() - row["checkin_epoch"]) / 60.0)
                                    v_type = row["vehicle_type"]
                                    tier = PRICING_TIERS.get(v_type, PRICING_TIERS["Sedan"])
                                    fee = round(tier["base_fee"] + (duration_mins * tier["per_min"]), 2)
                                    
                                    # Log transaction
                                    with sqlite3.connect(DB_PATH) as con:
                                        con.execute("INSERT INTO checkout_logs(vehicle, vehicle_type, checkin_time, checkout_time, duration_mins, fee) VALUES(?,?,?,?,?,?)",
                                                    (row["vehicle"], v_type, row["checkin_time"], time.strftime("%Y-%m-%d %H:%M:%S"), round(duration_mins, 1), fee))
                                    
                                    # Clear slot
                                    update_slot(int(row["id"]), 0, "", "", "", 0)
                                    st.success(f"Checked out {row['vehicle']}. Fee Billed: ₹{fee:.2f}")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.info("Occupied")
                        else:
                            if st.button(f"Park Here ({row['name']})", key=f"park_{row['id']}", use_container_width=True):
                                user_car_id = f"KA-05-GUEST" if not customer_name.strip() else f"KA-05-{customer_name[:3].upper()}-99"
                                update_slot(int(row["id"]), 1, user_car_id, "Sedan", time.strftime("%H:%M:%S"), time.time())
                                st.success(f"Assigned bay {row['name']}!")
                                time.sleep(0.5)
                                st.rerun()
                        
                        st.markdown("<br>", unsafe_allow_html=True)

# --- ADMIN REPORTS & TRANSACTION LEDGER ---
if admin_mode:
    st.markdown("---")
    st.markdown("## 📊 Billing Ledger & Transaction Reports")
    
    with sqlite3.connect(DB_PATH) as con:
        df_logs = pd.read_sql("SELECT * FROM checkout_logs ORDER BY id DESC", con)
    
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
        
        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Complete Billing Ledger (CSV)",
            data=csv_data,
            file_name="parking_ledger_report.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No checkout transactions recorded yet.")