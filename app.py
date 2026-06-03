import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# 1. 페이지 설정 및 제목 (초안 설정 100% 유지)
st.set_page_config(page_title="Self Thinking Chatbot v1", page_icon="❔", layout="centered")

# CSS 스타일 주입
css_style = """
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 20px;
        width: 100%;
    }
    .chat-row {
        display: flex;
        width: 100%;
    }
    .user-row {
        justify-content: flex-end;
    }
    .ai-row {
        justify-content: flex-start;
    }
    .message-box {
        padding: 12px 16px;
        border-radius: 16px;
        max-width: 75%;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
        word-break: break-word;
    }
    .user-msg {
        background-color: #fee500;
        color: #191919;
        border-top-right-radius: 0px;
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

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    data = cursor.fetchone()
    conn.close()
    if data and data[0] == make_hashes(password):
        return True
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

init_db()

# 3. Gemini API 키 설정 (초안 분기 로직 동일)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    genai.configure(api_key="AQ.Ab8RN6KC5DpBgtEw2bxuK0l0F5imUQtjfuwdFF-ga0S7_Ow1pQ") 

# 4. 프롬프트 시스템 지침 (원본 유지)
system_instruction = """
# Role and Core Objective
You are a strict Socratic guide and cognitive coach. Your primary objective is to lead the user to find their own answers through guided discovery. You must NEVER think, write, or make choices on behalf of the user. Your goal is to foster absolute intellectual independence.

# Strict Rules for Interaction
1. NO DIRECT ANSWERS OR SOLUTIONS: Never write essays, reflections, reports, or opinions for the user. Absolutely refuse to do the intellectual heavy lifting.
2. NO "MOTHERING" OR PROVIDING OPTIONS: When the user is stuck, frustrated, or asks "What should I do?", DO NOT provide a list of options, choices, or potential answers. Providing choices creates dependency. Instead, force the user to generate their own options by asking them to look at the problem from a different angle or break it down into smaller parts.
3. STEP-BY-STEP GUIDANCE: Guide the user through the thinking process one tiny step at a time. Ask only ONE open-ended question per turn. Never overwhelm them.
4. IMMEDIATE FACTUAL INFORMATION: Provide objective facts, raw data, or definitions immediately if requested. However, the moment the task shifts to analyzing, reflecting, or making a decision based on that data, you must strictly revert to asking questions.

# Handling User Roadblocks (When the user is stuck or gives up)
* WRONG AI Behavior: "If you're stuck, you could choose Topic A, Topic B, or Topic C. Which one do you like?" (X - Spoiling them)
* CORRECT AI Behavior: "It's completely normal to feel stuck at this point. Let's take a step back. If you had to explain the core issue to a 10-year-old in one sentence, what would you say?" (O - Forcing reflection)

# Tone and Manner
* Objective, patient, yet uncompromisingly firm. 
* Do not coddle the user; act as a sounding board that mirrors their own thoughts back to them.
* Warm, encouraging, patient, and highly user-friendly.
* Never sound restrictive, defensive, or like a strict teacher. Use conversational warmth.
* Validating: Always acknowledge the user's feelings or struggles first before asking the next question.
"""

# 5. 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- [구조 변경] 1. 비로그인 상태면 여기서 화면을 그리고 무조건 멈춤 ---
if not st.session_state.logged_in:
    st.title("🔐 대화 공간 입장하기")
    menu = ["로그인", "회원가입"]
    choice = st.selectbox("원하는 작업을 선택하세요", menu)

    if choice == "로그인":
        st.subheader("로그인")
        username = st.text_input("아이디", key="login_user")
        password = st.text_input("비밀번호", type="password", key="login_pass")
        if st.button("로그인 하기"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"👋 {username}님 환영합니다!")
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")

    elif choice == "회원가입":
        st.subheader("새로운 계정 만들기")
        new_user = st.text_input("원하는 아이디", key="reg_user")
        new_password = st.text_input("원하는 비밀번호", type="password", key="reg_pass")
        if st.button("가입하기"):
            if not new_user.strip() or not new_password.strip():
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")
            else:
                if add_user(new_user, new_password):
                    st.success("🎉 회원가입 성공! 로그인을 진행해주세요.")
                else:
                    st.error("❌ 이미 존재하는 아이디입니다.")
    
    st.stop()  # 로그인 안 됬으면 여기서 코드 실행 강제 종료 (하단 코드로 안 넘어감)


# --- [구조 변경] 2. 로그인 완료된 상태 (else문을 없애고 맨 앞으로 정렬) ---
def init_new_chat():
    st.session_state.messages = []
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state or "chat_session" not in st.session_state:
    init_new_chat()

with st.sidebar:
    st.subheader(f"👤 {st.session_state.username}님")
    if st.button("🔄 새 대화 시작하기", use_container_width=True):
        init_new_chat()
        st.rerun()
    st.markdown("---")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# 초안 메인 타이틀 노출
st.title("안녕하세요! 저는 Beta-T에요")
st.caption("이 챗봇은 당신이 스스로 답을 찾을 수 있도록 도와줍니다.")

# 카카오톡 정렬 레이아웃 출력
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-row user-row"><div class="message-box user-msg">{message["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-row ai-row"><div class="message-box ai-msg">{message["content"]}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if user_input := st.chat_input("어떤 생각이나 고민을 나누고 싶으신가요?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# 비동기 백그라운드 AI 응답 연산
if st.session_state.get("messages") and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    with st.spinner("생각을 가다듬는 중..."):
        try:
            response = st.session_state.chat_session.send_message(user_input)
            ai_response = response.text
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
