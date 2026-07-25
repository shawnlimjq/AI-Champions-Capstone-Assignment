import streamlit as st

st.set_page_config(
    page_title="CPF Schemes Self Help Portal", 
    layout="wide"
)

st.write("# Welcome to CPF Schemes Self Help Portal! 👋")
st.markdown(
    """
    Feel free to explore the website and learn more about the CPF Schemes.
    """
)

secrets = st.secrets.get("credentials", {})
admin_ids = secrets.get("ADMIN_IDS", [])
admin_password = secrets.get("ADMIN_PASSWORD")
regular_ids = secrets.get("REGULAR_IDS", [])
regular_password = secrets.get("REGULAR_PASSWORD")

if isinstance(admin_ids, str):
    admin_ids = [admin_ids]
if isinstance(regular_ids, str):
    regular_ids = [regular_ids]

if st.session_state.logged_in:
    st.success(
        f"Logged in as {st.session_state.current_user} ({st.session_state.login_role.title()})"
    )
    logout_clicked = st.button("Logout")
    if logout_clicked:
        st.session_state.logged_in = False
        st.session_state.login_error = ""
        st.session_state.login_role = ""
        st.session_state.current_user = ""
        st.rerun()

    if st.session_state.logged_in:
        if st.session_state.login_role == "admin":
            st.markdown(
                """
                ### Admin Dashboard
                You have full admin access. Use the sidebar to manage and explore all features.
                """
            )
        else:
            st.markdown(
                """
                ### User Portal
                You are logged in as a regular user. Explore the pages from the sidebar.
                """
            )
    else:
        st.info("You have been logged out. Please log in again.")
else:
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            value="",
            key="login_input_username"
        )
        password = st.text_input(
            "Password",
            type="password",
            value="",
            key="login_input_password"
        )
        submit = st.form_submit_button("Login")

    if submit:
        if not username or not password:
            st.session_state.login_error = "Please enter both username and password."
        elif not (admin_ids and admin_password and regular_ids and regular_password):
            st.session_state.login_error = (
                "Credential configuration is incomplete. Set ADMIN_IDS, ADMIN_PASSWORD, REGULAR_IDS, and REGULAR_PASSWORD in `.streamlit/secrets.toml`."
            )
        elif username in admin_ids and password == admin_password:
            st.session_state.logged_in = True
            st.session_state.login_role = "admin"
            st.session_state.current_user = username
            st.session_state.login_error = ""
            st.rerun()
        elif username in regular_ids and password == regular_password:
            st.session_state.logged_in = True
            st.session_state.login_role = "regular"
            st.session_state.current_user = username
            st.session_state.login_error = ""
            st.rerun()
        else:
            if username in admin_ids or username in regular_ids:
                st.session_state.login_error = "Password is incorrect."
            else:
                st.session_state.login_error = "Username not found."

    if st.session_state.login_error:
        st.error(st.session_state.login_error)

    if not (admin_ids and admin_password and regular_ids and regular_password):
        st.info(
            "If you haven't already, add credentials to `.streamlit/secrets.toml` and restart the app."
        )
