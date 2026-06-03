import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="생각을 깨우는 챗봇", page_icon="💡", layout="centered")

# CSS 스타일 (오타 수정: unsafe_allow_html=True)
css_style = """
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 20px;
    }
    .message-box {
        padding: 10px 15px;
        border-radius: 15px;
        max-width: 75%;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
    }
    .user-row {
        display: flex;
        justify-content: flex-end;
    }
    .user-msg {
        background-color: #fee500;
        color: #191919;
        border-top-right-radius: 0px;
    }
    .ai-row {
        display: flex;
        justify-content: flex-start;
    }
    .ai-msg {
        background-color: #ffffff;
        color: #333333;
        border-top-left-radius: 0px;
        border: 1px solid #e2e2e2;
    }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

st.title("💡 생각을 깨우는 다정한 대화 공간")
st.caption("이 챗봇은 정답을 바로 주지 않고, 당신이 스스로 답을 찾을 수 있도록 다정하게 도와줍니다.")

# 2. 데이터베이스 설정 (SQLite)
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users(username, password) VALUES (?,?)", (username, make_hashes(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False

# DB 초기화 실행
init_db()

# 3. Gemini API 키 설정 및 검증
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Streamlit Settings -> Secrets에 GOOGLE_API_KEY를 설정해주세요.")
    st.stop()

# 4. 프롬프트 (수정 없이 100% 동일하게 유지)
system_instruction = """
# Role and Core Objective
You are a strict Socratic guide and cognitive coach. Your primary objective is to lead the user to find their own answers through guided discovery. You must NEVER think,
