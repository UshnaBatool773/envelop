import streamlit as st
import json
import os

# --- Page Setup ---
st.set_page_config(page_title="PocketVault & Budget", page_icon="💰", layout="wide")

DATA_FILE = "user_vault_data.json"

# --- Storage Engine ---
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "bank_balance": 50000.0,
            "blocks": {
                "Shopping": 10000.0,
                "Rent": 10000.0,
                "Grocery": 10000.0,
                "Savings": 20000.0
            },
            "credentials": []
        }
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f)
        return default_data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "data" not in st.session_state:
    st.session_state.data = load_data()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "hide_balances" not in st.session_state:
    st.session_state.hide_balances = False

# --- Configurable Credentials ---
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
VAULT_PIN = "1234"

# --- Helper: Money Display ---
def fmt_amount(val):
    return "••••••" if st.session_state.hide_balances else f"Rs. {val:,.2f}"

# ==========================================
# 1. AUTHENTICATION
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### 🔐 Secure Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In", use_container_width=True, type="primary"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials (try admin / admin123)")
    st.stop()

# ==========================================
# 2. MAIN APP NAVIGATION
# ==========================================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["💰 Budget & Envelopes", "🔑 Credential Vault", "🤖 AI Financial Advisor"])

if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.rerun()

# Global Eye Toggle for Privacy
st.sidebar.divider()
eye_label = "👁️ Show Balances" if st.session_state.hide_balances else "🔒 Hide Balances (Eye)"
if st.sidebar.button(eye_label):
    st.session_state.hide_balances = not st.session_state.hide_balances
    st.rerun()

# ==========================================
# PAGE 1: BUDGET & ENVELOPES
# ==========================================
if page == "💰 Budget & Envelopes":
    st.title("Smart Budgeting & Balance Allocation")
    data = st.session_state.data

    # --- Top Balance Metrics ---
    allocated = sum(data["blocks"].values())
    unallocated = data["bank_balance"] - allocated

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Bank Balance", fmt_amount(data["bank_balance"]))
    c2.metric("Allocated to Blocks", fmt_amount(allocated))
    c3.metric("Unallocated Cash", fmt_amount(unallocated))

    st.divider()

    # --- Direct Deposit / Withdrawal from Bank ---
    with st.expander("💳 Main Bank Deposit & Direct Withdrawal"):
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            st.markdown("##### Deposit to Bank")
            dep_amt = st.number_input("Deposit Amount", min_value=0.0, step=500.0, key="main_dep")
            if st.button("Add to Bank"):
                if dep_amt > 0:
                    data["bank_balance"] += dep_amt
                    save_data(data)
                    st.success(f"Added Rs. {dep_amt:,.2f} to Main Bank!")
                    st.rerun()
        with sub_c2:
            st.markdown("##### Direct Withdrawal from Bank")
            with_amt = st.number_input("Withdraw Amount", min_value=0.0, step=500.0, key="main_with")
            if st.button("Deduct from Bank"):
                if with_amt > data["bank_balance"]:
                    st.error("Insufficient balance!")
                elif with_amt > 0:
                    data["bank_balance"] -= with_amt
                    save_data(data)
                    st.success(f"Deducted Rs. {with_amt:,.2f} from Bank!")
                    st.rerun()

    # --- Active Money Blocks ---
    st.subheader("Your Budget Blocks")
    
    cols = st.columns(3)
    block_names = list(data["blocks"].keys())
    
    for i, name in enumerate(block_names):
        val = data["blocks"][name]
        with cols[i % 3]:
            st.markdown(f"#### 🏷️ {name}")
            st.write(f"**Assigned:** {fmt_amount(val)}")
            
            amt = st.number_input(f"Amount (Rs.)", min_value=0.0, step=500.0, key=f"amt_{name}")
            b1, b2, b3 = st.columns(3)
            
            # Deduct from Block AND Main Balance
            if b1.button("Deduct", key=f"ded_{name}"):
                if amt > val:
                    st.error("Block has insufficient funds.")
                elif amt > data["bank_balance"]:
                    st.error("Bank has insufficient funds.")
                elif amt > 0:
                    data["blocks"][name] -= amt
                    data["bank_balance"] -= amt
                    save_data(data)
                    st.success(f"Deducted Rs. {amt:,.2f}")
                    st.rerun()

            # Add directly to Block from Bank Balance
            if b2.button("Top-up", key=f"top_{name}"):
                if amt > (data["bank_balance"] - allocated):
                    st.warning("Exceeds unallocated bank cash! Please deposit to bank first.")
                elif amt > 0:
                    data["blocks"][name] += amt
                    save_data(data)
                    st.success(f"Added Rs. {amt:,.2f} to {name}")
                    st.rerun()

            # Delete entire block
            if b3.button("🗑️", key=f"del_{name}"):
                del data["blocks"][name]
                save_data(data)
                st.rerun()
            st.markdown("---")

    # --- Add New Category Block ---
    with st.expander("➕ Create New Allocation Block"):
        nc1, nc2 = st.columns(2)
        new_block_name = nc1.text_input("Category Name (e.g. Travel, Gym, Education)")
        new_block_amt = nc2.number_input("Starting Allocation (Rs.)", min_value=0.0, step=500.0)
        if st.button("Create Block"):
            if new_block_name in data["blocks"]:
                st.error("Category already exists.")
            elif new_block_name.strip() == "":
                st.error("Please enter a category name.")
            else:
                data["blocks"][new_block_name] = new_block_amt
                save_data(data)
                st.success(f"Created category {new_block_name}!")
                st.rerun()

# ==========================================
# PAGE 2: CREDENTIAL VAULT
# ==========================================
elif page == "🔑 Credential Vault":
    st.title("Encrypted Credential Manager")
    data = st.session_state.data

    st.info("Protected space for your website logins and email accounts.")
    pin_input = st.text_input("Enter 4-Digit Security PIN to Reveal Passwords", type="password", max_chars=4)
    pin_valid = (pin_input == VAULT_PIN)

    # --- Display Stored Credentials ---
    st.subheader("Saved Accounts")
    if len(data["credentials"]) == 0:
        st.write("No credentials stored yet.")
    else:
        for idx, item in enumerate(data["credentials"]):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**Site:** {item['site']}")
            c2.write(f"**Email / User:** {item['email']}")
            
            # PIN logic for password reveal
            pass_display = item['password'] if pin_valid else "••••••••"
            c3.write(f"**Password:** `{pass_display}`")

            if c4.button("Delete", key=f"del_cred_{idx}"):
                data["credentials"].pop(idx)
                save_data(data)
                st.rerun()

    st.divider()

    # --- Add New Credential Form ---
    with st.expander("➕ Add New Login"):
        site_in = st.text_input("Website or Service Name (e.g. Netflix, Gmail, Bank Portal)")
        email_in = st.text_input("Email / Username")
        pass_in = st.text_input("Account Password", type="password")
        if st.button("Save Credential"):
            if site_in and email_in and pass_in:
                data["credentials"].append({
                    "site": site_in,
                    "email": email_in,
                    "password": pass_in
                })
                save_data(data)
                st.success("Credential securely saved!")
                st.rerun()
            else:
                st.error("Please complete all 3 fields.")

# ==========================================
# PAGE 3: AI FINANCIAL ADVISOR (GROQ)
# ==========================================
elif page == "🤖 AI Financial Advisor":
    st.title("Groq AI Budget Companion")
    st.write("Ask for financial advice, balance assessments, or saving strategies tailored to your allocations.")

    api_key = os.environ.get("GROQ_API_KEY") or st.text_input("Enter your Groq API Key (starts with gsk_)", type="password")

    user_query = st.text_area("Ask a question about your finances:")
    
    if st.button("Generate Advice", type="primary"):
        if not api_key:
            st.error("Please provide a Groq API Key to proceed.")
        elif not user_query:
            st.warning("Please enter a question.")
        else:
            try:
               from groq import Groq

client = Groq(api_key=api_key)
summary = f"Total balance: {st.session_state.data['bank_balance']}. Allocations: {json.dumps(st.session_state.data['blocks'])}."
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a helpful, practical personal finance assistant. Current User Financial Context: {summary}"
                        },
                        {
                            "role": "user",
                            "content": user_query
                        }
                    ],
                    model="openai/gpt-oss-120b",
                )
                st.markdown("### Advice:")
                st.write(chat_completion.choices[0].message.content)
            except Exception as e:
                st.error(f"Error communicating with Groq: {e}")
