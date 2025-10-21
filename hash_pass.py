import streamlit_authenticator as stauth
import streamlit_authenticator as stauth
hashed_pw = stauth.Hasher('yourpassword').generate()  # ✅ Pass as argument(s), not list
print(hashed_pw)

