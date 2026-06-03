import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Deep Sea Thinking Chatbot v1", page_icon="🐟", layout="centered")

# 2. 세션 상태 초기화 및 새로고침 자동 로그인 감지
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# URL 쿼리 파라미터를 확인하여 새로고침 시 로그인 상태 자동 복구
if not st.session_state.logged_in and "user" in st.query_params and "token" in st.query_params:
    saved_user = st.query_params["user"]
    saved_token = st.query_params["token"]
    expected_token = hashlib.sha256(str.encode(saved_user + "deep_sea_secret_salt")).hexdigest()
    if saved_token == expected_token:
        st.session_state.logged_in = True
        st.session_state.username = saved_user


# 3. 데이터베이스 및 대화 초기화 함수 선언
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

# Gemini API 키 및 지침 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    genai.configure(api_key="AQ.Ab8RN6KC5DpBgtEw2bxuK0l0F5imUQtjfuwdFF-ga0S7_Ow1pQ") 

system_instruction = """
# Role and Core Objective
You are a strict Socratic guide and cognitive coach. Your primary objective is to lead the user to find their own answers through guided discovery. You must NEVER think, write, or make choices on behalf of the user. Your goal is to foster absolute intellectual independence.

# Strict Rules for Interaction
1. NO DIRECT ANSWERS OR SOLUTIONS: Never write essays, reflections, reports, or opinions for the user. Absolutely refuse to do the intellectual heavy lifting.
2. NO "MOTHERING" OR PROVIDING OPTIONS: When the user is stuck, frustrated, or asks "What should I do?", DO NOT provide a list of options, choices, or potential answers. Providing choices creates dependency. Instead, force the user to generate their own options by asking them to look at the problem from a different angle or break it down into smaller parts.
3. STEP-BY-STEP GUIDANCE: Guide the user through the thinking process one tiny step at a time. Ask only ONE open-ended question per turn. Never overwhelm them.
4. IMMEDIATE FACTUAL INFORMATION: Provide objective facts, raw data, or definitions immediately if requested. However, the moment the task shifts to analyzing, reflecting, or making a decision based on that data, you must strictly revert to asking questions.

# Handling User Roadblocks
* WRONG AI Behavior: "If you're stuck, you could choose Topic A, Topic B, or Topic C. Which one do you like?" (X)
* CORRECT AI Behavior: "It's completely normal to feel stuck at this point. Let's take a step back. If you had to explain the core issue to a 10-year-old in one sentence, what would you say?" (O)
"""

def init_new_chat():
    st.session_state.messages = []
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])


# 4. 통합 사이드바 구성 (테마 선택 + 회원 메뉴)
with st.sidebar:
    st.subheader("🎨 UI 테마 설정")
    theme_choice = st.radio("화면 모드를 선택하세요", ["🌙 다크 모드", "☀️ 라이트 모드"], label_visibility="collapsed")
    
    # 로그인 상태일 때만 추가 메뉴 노출
    if st.session_state.logged_in:
        st.markdown("---")
        st.subheader(f"🐟 {st.session_state.username} 탐험가님")
        if st.button("새 대화 시작하기", use_container_width=True):
            init_new_chat()
            st.rerun()
        st.markdown("---")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.query_params.clear()
            st.rerun()


# 5. 다크 모드 / 라이트 모드 CSS 분리 정의
dark_css = """
<style>
    .stApp { background-color: #060d19 !important; color: #e0f2fe; }
    [data-testid="stSidebar"] { background-color: #03070f !important; border-right: 1px solid #00b4d822 !important; }
    
    /* 입력창 및 셀렉트박스 */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #0f1a2c !important; color: #e2f1ff !important; border: 1px solid #00b4d844 !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #0f1a2c !important; color: #e2f1ff !important; }
    div[data-baseweb="popover"] li { background-color: transparent !important; color: #e2f1ff !important; }
    div[data-baseweb="popover"] li:hover { background-color: #0077b6 !important; }
    
    /* 버튼 */
    div.stButton > button { background-color: #0f1a2c !important; color: #e2f1ff !important; border: 1px solid #00b4d866 !important; }
    div.stButton > button:hover { background-color: #0077b6 !important; border-color: #00b4d8 !important; color: #ffffff !important; }

    /* 하단 채팅창 */
    div[data-testid="stChatInput"] { background-color: transparent !important; }
    div[data-testid="stChatInput"] > div { background-color: #0f1a2c !important; border: 1px solid #00b4d844 !important; }
    div[data-testid="stChatInput"] textarea { background-color: transparent !important; color: #e2f1ff !important; }
    div[data-testid="stChatInput"] button { background-color: transparent !important; color: #00b4d8 !important; }
    
    /* 말풍선 공통 및 인라인 배치 */
    .chat-container { display: flex; flex-direction: column; gap: 40px; margin: 25px 0; width: 100%; }
    .chat-row { display: flex; width: 100%; }
    .user-row { justify-content: flex-end; }
    .ai-row { justify-content: flex-start; }
    .message-box { padding: 16px 24px; max-width: 78%; font-size: 15px; line-height: 1.6; word-break: break-word; white-space: pre-wrap; margin: 5px 0; }
    
    .user-msg { background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%); color: #ffffff !important; border-radius: 24px 24px 4px 24px; box-shadow: 0px 4px 15px rgba(0, 180, 216, 0.2); font-weight: 500; }
    .user-msg * { color: #ffffff !important; }
    .ai-msg { background-color: #0f1a2c; color: #e2f1ff !important; border-radius: 24px 24px 24px 4px; border: 1.5px solid #00b4d8; box-shadow: 0px 4px 20px rgba(0, 180, 216, 0.15); }
    .ai-msg * { color: #e2f1ff !important; }
    
    h1, h2, h3, p, span, label, .stMarkdown, div[data-testid="stWidgetLabel"] p { color: #e2f1ff !important; }
    .stCaption { color: #64748b !important; }
</style>
"""

light_css = """
<style>
    .stApp { background-color: #ffffff !important; color: #1e293b; }
    [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0 !important; }
    
    /* 입력창 및 셀렉트박스 */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #ffffff !important; color: #1e293b !important; }
    div[data-baseweb="popover"] li { background-color: transparent !important; color: #1e293b !important; }
    div[data-baseweb="popover"] li:hover { background-color: #f1f5f9 !important; }
    
    /* 버튼 */
    div.stButton > button { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
    div.stButton > button:hover { background-color: #0077b6 !important; border-color: #0077b6 !important; color: #ffffff !important; }

    /* 하단 채팅창 */
    div[data-testid="stChatInput"] { background-color: transparent !important; }
    div[data-testid="stChatInput"] > div { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.05) !important; }
    div[data-testid="stChatInput"] textarea { background-color: transparent !important; color: #1e293b !important; }
    div[data-testid="stChatInput"] button { background-color: transparent !important; color: #0077b6 !important; }
    
    /* 말풍선 공통 및 인라인 배치 */
    .chat-container { display: flex; flex-direction: column; gap: 35px; margin: 25px 0; width: 100%; }
    .chat-row { display: flex; width: 100%; }
    .user-row { justify-content: flex-end; }
    .ai-row { justify-content: flex-start; }
    .message-box { padding: 16px 24px; max-width: 78%; font-size: 15px; line-height: 1.6; word-break: break-word; white-space: pre-wrap; margin: 5px 0; }
    
    .user-msg { background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%); color: #ffffff !important; border-radius: 24px 24px 4px 24px; box-shadow: 0px 4px 12px rgba(0, 180, 216, 0.15); font-weight: 500; }
    .user-msg * { color: #ffffff !important; }
    .ai-msg { background-color: #f4f9fc; color: #1e293b !important; border-radius: 24px 24px 24px 4px; border: 1.5px solid #00b4d8; box-shadow: 0px 4px 15px rgba(0, 180, 216, 0.06); }
    .ai-msg * { color: #1e293b !important; }
    
    h1, h2, h3, p, span, label, .stMarkdown, div[data-testid="stWidgetLabel"] p { color: #0f172a !important; }
    .stCaption { color: #64748b !important; }
</style>
"""

# 선택한 테마에 맞춰 실시간 CSS 주입
if theme_choice == "🌙 다크 모드":
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)


# --- 6. 비로그인 화면 (로그인 / 회원가입) ---
if not st.session_state.logged_in:
    st.title("로그인 페이지")
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
                st.query_params["user"] = username
                st.query_params["token"] = hashlib.sha256(str.encode(username + "deep_sea_secret_salt")).hexdigest()
                st.success(f"{username}님 환영합니다!")
                st.rerun()
            else:
                st.error("X 아이디 또는 비밀번호가 틀렸습니다.")

    elif choice == "회원가입":
        st.subheader("새로운 계정 만들기")
        new_user = st.text_input("원하는 아이디", key="reg_user")
        new_password = st.text_input("원하는 비밀번호", type="password", key="reg_pass")
        if st.button("가입하기"):
            if not new_user.strip() or not new_password.strip():
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")
            else:
                if add_user(new_user, new_password):
                    st.success("회원가입 성공! 로그인을 진행해주세요.")
                else:
                    st.error("X 이미 존재하는 아이디입니다.")
    st.stop()


# --- 7. 메인 채팅 화면 (로그인 완료 상태) ---
if "messages" not in st.session_state or "chat_session" not in st.session_state:
    init_new_chat()

st.title("🐳 안녕하세요! 저는 Beta-T에요")
st.caption("이 챗봇은 당신이 스스로 답을 찾을 수 있도록 도와줍니다.")

# 대화 내용 출력
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-row user-row"><div class="message-box user-msg">{message["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-row ai-row"><div class="message-box ai-msg">{message["content"]}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 사용자 입력 처리
if user_input := st.chat_input("도움이 필요하신가요?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# AI 응답 연산 및 리런
if st.session_state.get("messages") and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    with st.spinner("생각하는 중..."):
        try:
            response = st.session_state.chat_session.send_message(user_input)
            ai_response = response.text
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
