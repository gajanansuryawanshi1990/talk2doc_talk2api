# login.py
import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
import time
import requests

# Page config
st.set_page_config(
    page_title="AI Chatbot - Login", 
    page_icon="🔐", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# def hash_password(password: str) -> str:
#     """Hash password using SHA-256"""
#     return hashlib.sha256(password.encode()).hexdigest()


API_BASE_URL = "http://localhost:8001"  # Change if your FastAPI runs on a different port

def register_user(username: str, email: str, password: str,  doj:datetime, designation: str, department: str, location: str) -> tuple[bool, str]:
    try:
        # response = requests.post(
        #     f"{API_BASE_URL}/register",
        #     json={
        #         "username": username,
        #         "email": email,
        #         "password": password,
        #         "doj": str(doj),  # Convert date to string
        #         "designation": designation,
        #         "department": department,
        #         "location": location
        #     }
        # )
        response = requests.post(
            f"{API_BASE_URL}/register",
            params={"username": username, "email": email, "password": password,  "doj": str(doj),"designation": designation,"department": department,"location": location}
        )
        if response.status_code == 200:
            return True, response.json().get("message", "Registration successful!")
        else:
            return False, response.json().get("detail", "Registration failed!")
    except Exception as e:
        return False, f"Error: {str(e)}"


def authenticate_user(username: str, password: str) -> tuple[bool, str, str | None, str | None]:
    """Authenticate user login and return (success, message, role, id)"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/authenticate",
            params={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            # return (success, message, role, id)
            return True, data.get("message", "Login successful!"), data.get("role", "user"), data.get("id")
        else:
            # Return consistent tuple on failure
            detail = None
            try:
                detail = response.json().get("detail", "login failed!")
            except Exception:
                detail = "login failed!"
            return False, detail, None, None
    except Exception as e:
        return False, f"Error: {str(e)}", None, None

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    
    return True, "Password is strong"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
    }
    
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 400px;
        margin: 0 auto;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        height: 3rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e1e5e9;
        padding: 0.75rem;
    }
    
    .switch-form {
        text-align: center;
        margin-top: 1rem;
        color: #666;
    }
    
    .switch-form a {
        color: #667eea;
        text-decoration: none;
        font-weight: bold;
    }
    
    .switch-form a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Chatbot</h1>
        <p>Secure Access to Your AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if user is already authenticated
    if st.session_state.authenticated:
        st.success(f"✅ Welcome back, {st.session_state.username}!")
        st.info("🚀 Redirecting to main application...")
        col1, col2, col3 = st.columns([1, 2, 1])
        # with col2:
        # st.button("🔓 Continue to Chat", type="primary"):
                # Redirect to main app
        st.switch_page("pages/app-ui.py")
        with col2:    
            if st.button("🚪 Logout", type="secondary"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
        
        return
    
    # Login/Register Form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        if not st.session_state.show_register:
            # LOGIN FORM
            st.markdown("### 🔐 Login")
            st.markdown("---")
            
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_button = st.form_submit_button("🚀 Login", type="primary")
                # with col_b:
                #     forgot_button = st.form_submit_button("❓ Demo Login")
                
                if login_button:
                    if username and password:
                        success, message, role, id = authenticate_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.role = role
                            st.session_state.user_id = id  # store user id in session state
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("⚠️ Please fill in all fields!")
                
                # if forgot_button:
                    # # Demo login for testing
                    # st.session_state.authenticated = True
                    # st.session_state.username = "demo_user"
                    # st.success("✅ Demo login successful!")
                    # time.sleep(1)
                    # st.rerun()
            
            # Switch to register
            st.markdown("""
            <div class="switch-form">
                Don't have an account? 
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📝 Create New Account", type="secondary"):
                st.session_state.show_register = True
                st.rerun()
        
        else:
            # REGISTER FORM
            st.markdown("### 📝 Create Account")
            st.markdown("---")
            
            with st.form("register_form"):
                new_username = st.text_input("👤 Choose Username", placeholder="Enter desired username")
                new_email = st.text_input("📧 Email", placeholder="Enter your email address")
                new_password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                
                # doj = st.date_input("📅 Date of Joining", value=date.today())
                doj = st.date_input("📅 Date of Joining")
                designation = st.text_input("🏢 Designation", placeholder="Enter your designation")
                department = st.text_input("📂 Department", placeholder="Enter your department")
                location = st.text_input("📍 Location", placeholder="Enter your location")

                # Terms and conditions
                agree_terms = st.checkbox("I agree to the Terms and Conditions")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    register_button = st.form_submit_button("✅ Register", type="primary")
                with col_b:
                    cancel_button = st.form_submit_button("❌ Cancel")
                
                if register_button:
                    if new_username and new_email and new_password and confirm_password and doj and designation and department and location:
                        if not agree_terms:
                            st.warning("⚠️ Please agree to the Terms and Conditions!")
                        elif new_password != confirm_password:
                            st.error("❌ Passwords don't match!")
                        elif not validate_email(new_email):
                            st.error("❌ Please enter a valid email address!")
                        else:
                            # Validate password
                            is_valid, password_msg = validate_password(new_password)
                            if not is_valid:
                                st.error(f"❌ {password_msg}")
                            else:
                                success, message = register_user(new_username, new_email, new_password, doj, designation, department, location)
                                
                                if success:
                                    st.success(message)
                                    st.info("🔄 Please login with your new credentials")
                                    time.sleep(2)
                                    st.session_state.show_register = False
                                    st.rerun()
                                else:
                                    st.error(message)
                    else:
                        st.warning("⚠️ Please fill in all fields!")
                
                if cancel_button:
                    st.session_state.show_register = False
                    st.rerun()
            
            # Switch back to login
            st.markdown("""
            <div class="switch-form">
                Already have an account?
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔐 Back to Login", type="secondary"):
                st.session_state.show_register = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🔒 Your data is secure and encrypted</p>
        <p><small>AI Chatbot v2.0 • Powered by Azure OpenAI</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
