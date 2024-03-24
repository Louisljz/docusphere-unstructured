import streamlit as st
import psycopg2
import re
import bcrypt

@st.cache_resource
def init_connection():
    return psycopg2.connect(st.secrets['DATABASE_URL'])

conn = init_connection()

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

with st.form('register_form', clear_on_submit=True):
    st.header('Register', divider='gray')
    name = st.text_input('Name')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    password2 = st.text_input('Confirm password', type='password')

    if st.form_submit_button('Submit'):
        if name and email and password and password2:
            if is_valid_email(email):
                if password == password2:
                    username = email.split('@')[0]
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    try: 
                        cur = conn.cursor()
                        df = cur.execute(f'''INSERT INTO users (username, password, email, name) 
                                        VALUES ('{username}', '{hashed_password}', '{email}', '{name}')''')
                        conn.commit()
                    except Exception as e:
                        print(e)
                        conn.rollback()

                        st.warning(f'User with {email} already exists!')
                        st.stop()

                    cur.close()
                    st.success(f'Welcome {name}! You have successfully registered with {email}')
                    st.page_link('login.py', label='Login', icon='🔐')
                else:
                    st.error('Passwords do not match!')
            else:
                st.error('Please input a valid email!')
        else:
            st.warning('Please fill in missing details!')
