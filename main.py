import streamlit as st
from pathlib import Path
import json
import random
import string
from typing import Optional, List

# -----------------------------
# Data Layer (Bank Class)
# -----------------------------
class Bank:
    __database = "data.json"
    data: List[dict] = []

    # Load on import
    try:
        if Path(__database).exists():
            with open(__database, "r", encoding="utf-8") as fs:
                data = json.load(fs)
    except Exception as err:
        print(f"Error occurred while loading DB: {err}")

    @classmethod
    def update_data(cls):
        # Persist the in-memory data to disk
        with open(cls.__database, "w", encoding="utf-8") as fs:
            json.dump(cls.data, fs, ensure_ascii=False, indent=2)

    @classmethod
    def reload(cls):
        # Reload from disk (useful after external edits)
        if Path(cls.__database).exists():
            with open(cls.__database, "r", encoding="utf-8") as fs:
                cls.data = json.load(fs)

    @classmethod
    def generate_account_no(cls) -> str:
        alpha = random.choices(string.ascii_letters, k=4)
        digit = random.choices(string.digits, k=8)
        id_chars = alpha + digit
        random.shuffle(id_chars)
        return "".join(id_chars)

    @classmethod
    def find_user(cls, acc_no: str, pin: int) -> Optional[dict]:
        for u in cls.data:
            if u.get("AccountNo.") == acc_no and u.get("pin") == pin:
                return u
        return None

    @classmethod
    def find_by_acc(cls, acc_no: str) -> Optional[dict]:
        for u in cls.data:
            if u.get("AccountNo.") == acc_no:
                return u
        return None


# -----------------------------
# Helper Functions
# -----------------------------
def require_logged_in():
    if not st.session_state.get("auth"):
        st.warning("Please login first from the sidebar.")
        st.stop()


def login_block():
    st.subheader("Login")
    with st.form("login_form", clear_on_submit=False):
        acc_no = st.text_input("Account Number", placeholder="Enter your account number")
        pin_str = st.text_input("PIN", type="password", placeholder="4-digit PIN")
        submit = st.form_submit_button("Login")

    if submit:
        if not acc_no or not pin_str.isdigit():
            st.error("Enter a valid account number and numeric PIN.")
            return
        user = Bank.find_user(acc_no, int(pin_str))
        if user:
            st.session_state["auth"] = {"acc": acc_no, "pin": int(pin_str)}
            st.success("Logged in successfully.")
        else:
            st.error("Invalid account number or PIN.")


def show_user_summary(user: dict):
    st.write("### Account Summary")
    st.json({
        k: user[k]
        for k in ["name", "email", "age", "phone", "AccountNo.", "balance"]
        if k in user
    })


# -----------------------------
# UI Sections
# -----------------------------
def ui_create_account():
    st.header("Create New Account")
    with st.form("create_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        age = st.number_input("Age", min_value=0, step=1)
        phone = st.text_input("Phone (10 digits)")
        pin = st.text_input("PIN (4 digits)", type="password")
        submitted = st.form_submit_button("Create Account")

    if submitted:
        # Validation
        if not name or not email:
            st.error("Name and Email are required.")
            return
        if age < 18:
            st.error("You must be at least 18 to open an account.")
            return
        if not phone.isdigit() or len(phone) != 10:
            st.error("Phone must be 10 digits.")
            return
        if not pin.isdigit() or len(pin) != 4:
            st.error("PIN must be a 4-digit number.")
            return

        acc_no = Bank.generate_account_no()
        info = {
            "name": name.strip(),
            "email": email.strip(),
            "age": int(age),
            "phone": int(phone),
            "pin": int(pin),
            "AccountNo.": acc_no,
            "balance": 0,
        }
        Bank.data.append(info)
        Bank.update_data()
        st.success(f"Account created! Your account number is **{acc_no}**. Keep it safe.")
        show_user_summary(info)


def ui_deposit():
    st.header("Deposit Money")
    require_logged_in()
    auth = st.session_state["auth"]
    user = Bank.find_user(auth["acc"], auth["pin"])
    if not user:
        st.error("Session expired. Please login again.")
        st.session_state.pop("auth", None)
        st.stop()

    with st.form("deposit_form"):
        amount = st.number_input("Amount (<= 10000)", min_value=0, step=1)
        submitted = st.form_submit_button("Deposit")

    if submitted:
        if amount <= 0:
            st.error("Amount must be positive.")
            return
        if amount > 10000:
            st.error("Amount is greater than 10,000.")
            return
        user["balance"] += int(amount)
        Bank.update_data()
        st.success("Money deposited successfully.")
        show_user_summary(user)


def ui_withdraw():
    st.header("Withdraw Money")
    require_logged_in()
    auth = st.session_state["auth"]
    user = Bank.find_user(auth["acc"], auth["pin"])
    if not user:
        st.error("Session expired. Please login again.")
        st.session_state.pop("auth", None)
        st.stop()

    with st.form("withdraw_form"):
        amount = st.number_input("Amount (<= 10000)", min_value=0, step=1)
        submitted = st.form_submit_button("Withdraw")

    if submitted:
        if amount <= 0:
            st.error("Amount must be positive.")
            return
        if amount > 10000:
            st.error("Amount is greater than 10,000.")
            return
        if amount > user["balance"]:
            st.error("Insufficient balance.")
            return
        user["balance"] -= int(amount)
        Bank.update_data()
        st.success("Money withdrawn successfully.")
        show_user_summary(user)


def ui_view_details():
    st.header("View Account Details")
    require_logged_in()
    auth = st.session_state["auth"]
    user = Bank.find_user(auth["acc"], auth["pin"])
    if not user:
        st.error("Session expired. Please login again.")
        st.session_state.pop("auth", None)
        st.stop()
    show_user_summary(user)


def ui_update_details():
    st.header("Update Details")
    require_logged_in()
    auth = st.session_state["auth"]
    user = Bank.find_user(auth["acc"], auth["pin"])
    if not user:
        st.error("Session expired. Please login again.")
        st.session_state.pop("auth", None)
        st.stop()

    st.info("Leave a field empty to keep current value. Account number cannot be changed.")

    with st.form("update_form"):
        name = st.text_input("Name", value="")
        email = st.text_input("Email", value="")
        age = st.text_input("Age", value="")
        phone = st.text_input("Phone (10 digits)", value="")
        pin = st.text_input("PIN (4 digits)", type="password", value="")
        submitted = st.form_submit_button("Update")

    if submitted:
        newData = {
            "name": name if name else user["name"],
            "email": email if email else user["email"],
            "age": int(age) if age.isdigit() else user["age"],
            "phone": int(phone) if phone.isdigit() else user["phone"],
            "pin": int(pin) if pin.isdigit() else user["pin"],
            "AccountNo.": user["AccountNo."],
            "balance": user["balance"],
        }
        user.update(newData)
        Bank.update_data()
        st.success("Details updated successfully.")
        show_user_summary(user)


def ui_delete_account():
    st.header("Delete Account")
    require_logged_in()
    auth = st.session_state["auth"]
    user = Bank.find_user(auth["acc"], auth["pin"])
    if not user:
        st.error("Session expired. Please login again.")
        st.session_state.pop("auth", None)
        st.stop()

    st.warning("This action is irreversible. Your account and data will be deleted.")
    if st.button("Delete my account", type="primary"):
        try:
            Bank.data.remove(user)
            Bank.update_data()
            st.success("Account deleted successfully.")
            st.session_state.pop("auth", None)
        except ValueError:
            st.error("Account not found or already deleted.")


# -----------------------------
# Sidebar + Main App
# -----------------------------
def sidebar():
    st.sidebar.title("Bank Portal")

    # Login / Logout block
    if st.session_state.get("auth"):
        acc = st.session_state["auth"]["acc"]
        st.sidebar.success(f"Logged in as: {acc}")
        if st.sidebar.button("Logout"):
            st.session_state.pop("auth", None)
            st.experimental_rerun()
    else:
        login_block()

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Go to",
        (
            "Create Account",
            "Deposit",
            "Withdraw",
            "View Details",
            "Update Details",
            "Delete Account",
            "Reload DB",
        ),
    )
    return page


def main():
    st.set_page_config(
        page_title="Bank Management",
        page_icon="🏦",
        layout="centered"
    )
    st.title("🏦 Bank Management — Streamlit UI")
    st.caption("OOP + JSON storage — Web interface for your Bank project.")

    page = sidebar()

    if page == "Create Account":
        ui_create_account()
    elif page == "Deposit":
        ui_deposit()
    elif page == "Withdraw":
        ui_withdraw()
    elif page == "View Details":
        ui_view_details()
    elif page == "Update Details":
        ui_update_details()
    elif page == "Delete Account":
        ui_delete_account()
    elif page == "Reload DB":
        Bank.reload()
        st.success("Reloaded data from disk.")
        if st.session_state.get("auth"):
            auth = st.session_state["auth"]
            if not Bank.find_user(auth["acc"], auth["pin"]):
                st.warning("Your account was not found after reload. Logging out.")
                st.session_state.pop("auth", None)


if __name__ == "__main__":
    if "auth" not in st.session_state:
        st.session_state["auth"] = None
    main()
