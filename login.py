import streamlit as st
import psycopg2
import bcrypt
import re


@st.cache_resource
def init_connection():
    return psycopg2.connect(st.secrets['DATABASE_URL'])

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def get_user(email):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    return user

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

conn = init_connection()

with st.container(border=True):
    st.header('Login', divider='gray')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    if st.button('Submit'):
        if email and password:
            if is_valid_email(email):
                user = get_user(email)
                if user:
                    hashed_password = user[1]
                    if verify_password(password, hashed_password):
                        st.session_state.user = {'name': user[3], 'id': user[0]}
                        st.switch_page('pages/app.py')
                    else:
                        st.error('Incorrect password!')
                else:
                    st.warning('User not found!')
            else:
                st.error('Please input a valid email!')
        else:
            st.warning('Please fill in missing details!')

    st.write("Don't have an account?")
    st.page_link('pages/register.py', label='Register', icon='📝')
