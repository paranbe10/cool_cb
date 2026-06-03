import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
import pandas as pd

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Deep Sea Thinking Chatbot v1", page_icon="🐟", layout="centered")

# 2. 세션 상태 초기화 및 새로고침 자동 로그인 감지
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

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
"""

def init_new_chat():
    st.session_state.messages = []
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])


# 4. 브라우저/시스템 테마를 알아서 감지하는 지능형 통합 CSS 주입 + 초소형 관리자 버튼 스타일
auto_theme_css = """
<style>
    /* 📌 [공통 레이아웃 구조] */
    .chat-container { display: flex; flex-direction: column; width: 100%; margin: 25px 0; }
    .chat-row { display: flex; width: 100%; }
    .user-row { justify-content: flex-end; }
    .ai-row { justify-content: flex-start; }
    .message-box { padding: 16px 24px; max-width: 78%; font-size: 15px; line-height: 1.6; word-break: break-word; white-space: pre-wrap; margin: 5px 0; }
    div[data-testid="stChatInput"] { background-color: transparent !important; }
    div[data-testid="stChatInput"] textarea { background-color: transparent !important; }
    div[data-testid="stChatInput"] button { background-color: transparent !important; }
    
    .user-msg { background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%); color: #ffffff !important; border-radius: 24px 24px 4px 24px; box-shadow: 0px 4px 12px rgba(0, 180, 216, 0.15); font-weight: 500; }
    .user-msg * { color: #ffffff !important; }

    /* 🚨 [핵심 수정] 왼쪽 하단 관리자 비밀 진입 버튼을 ㅈㄴ 작게 만드는 CSS 테러 */
    div.admin-secret-btn > button {
        background-color: transparent !important;
        border: none !important;
        color: #94a3b844 !important; /* 거의 안 보이게 흐릿한 회색 처리 */
        font-size: 10px !important;
        padding: 0px !important;
        min-height: 20px !important;
        width: auto !important;
        box-shadow: none !important;
    }
    div.admin-secret-btn > button:hover {
        color: #00b4d8 !important; /* 마우스를 올릴 때만 슬쩍 파란빛 유혹 */
        background-color: transparent !important;
    }

    /* 🌙 [1] 사용자가 다크 모드일 때 브라우저가 알아서 켜는 스타일 */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #060d19 !important; color: #e0f2fe; }
        [data-testid="stSidebar"] { background-color: #03070f !important; border-right: 1px solid #00b4d822 !important; }
        
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] [data-baseweb="select"] {
            background-color: #0f1a2c !important; color: #e2f1ff !important; border: 1px solid #00b4d844 !important;
        }
        div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #0f1a2c !important; color: #e2f1ff !important; }
        div[data-baseweb="popover"] li { background-color: transparent !important; color: #e2f1ff !important; }
        div[data-baseweb="popover"] li:hover { background-color: #0077b6 !important; }
        
        div.stButton > button { background-color: #0f1a2c !important; color: #e2f1ff !important; border: 1px solid #00b4d866 !important; }
        div.stButton > button:hover { background-color: #0077b6 !important; border-color: #00b4d8 !important; color: #ffffff !important; }

        div[data-testid="stChatInput"] > div { background-color: #0f1a2c !important; border: 1px solid #00b4d844 !important; }
        div[data-testid="stChatInput"] textarea { color: #e2f1ff !important; }
        div[data-testid="stChatInput"] button { color: #00b4d8 !important; }
        
        .chat-container { gap: 40px; }
        .ai-msg { background-color: #0f1a2c; color: #e2f1ff !important; border-radius: 24px 24px 24px 4px; border: 1.5px solid #00b4d8; box-shadow: 0px 4px 20px rgba(0, 180, 216, 0.15); }
        .ai-msg * { color: #e2f1ff !important; }
        
        h1, h2, h3, p, span, label, .stMarkdown, div[data-testid="stWidgetLabel"] p { color: #e2f1ff !important; }
        .stCaption { color: #64748b !important; }
    }

    /* ☀️ [2] 사용자가 라이트 모드일 때 브라우저가 알아서 켜는 스타일 */
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #ffffff !important; color: #1e293b; }
        [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0 !important; }
        
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] [data-baseweb="select"] {
            background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important;
        }
        div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #ffffff !important; color: #1e293b !important; }
        div[data-baseweb="popover"] li { background-color: transparent !important; color: #1e293b !important; }
        div[data-baseweb="popover"] li:hover { background-color: #f1f5f9 !important; }
        
        div.stButton > button { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
        div.stButton > button:hover { background-color: #0077b6 !important; border-color: #0077b6 !important; color: #ffffff !important; }

        div[data-testid="stChatInput"] > div { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.05) !important; }
        div[data-testid="stChatInput"] textarea { color: #1e293b !important; }
        div[data-testid="stChatInput"] button { color: #0077b6 !important; }
        
        .chat-container { gap: 35px; }
        .ai-msg { background-color: #f4f9fc; color: #1e293b !important; border-radius: 24px 24px 24px 4px; border: 1.5px solid #00b4d8; box-shadow: 0px 4px 15px rgba(0, 180, 216, 0.06); }
        .ai-msg * { color: #1e293b !important; }
        
        h1, h2, h3, p, span, label, .stMarkdown, div[data-testid="stWidgetLabel"] p { color: #0f172a !important; }
        .stCaption { color: #64748b !important; }
    }
</style>
"""
st.markdown(auto_theme_css, unsafe_allow_html=True)


# 5. 왼쪽 사이드바 구성 (상단: 회원 정보 / 맨 하단: ㅈㄴ 작은 비밀 버튼)
with st.sidebar:
    if st.session_state.logged_in:
        st.subheader(f"🐟 {st.session_state.username} 탐험가")
        if st.button("새 대화 시작하기", use_container_width=True):
            init_new_chat()
            st.rerun()
        st.markdown("---")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.query_params.clear()
            st.rerun()
    else:
        st.caption("로그인 후 서비스를 이용하실 수 있습니다.")
    
    # 🤫 [비밀 공간] 사이드바 본문을 띄우기 위한 빈 여백 확보 후 구석에 배치
    st.write("")
    st.write("")
    
    # 클래스 주입으로 크기와 투명도를 극대화한 ⚙️ 버튼
    st.markdown('<div class="admin-secret-btn">', unsafe_allow_html=True)
    if st.button("관리자"):
        st.session_state.show_admin = not st.session_state.show_admin
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- 6. 비밀 메뉴 활성화 시 노출되는 오버레이 인증 창 ---
if st.session_state.show_admin:
    st.warning("⚠️ 시스템 관리자 검증 모드 활성화됨")
    admin_password = st.text_input("마스터 권한 인증 암호를 입력하세요", type="password", key="admin_menu_pass")
    
    # 본인만 알 수 있는 마스터 비밀번호 설정 (예: admin1234)
    if admin_password == "admin1234": 
        st.success("인증 완료. 실시간 회원 명부를 로드했습니다.")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            df = pd.DataFrame(rows, columns=["아이디 (Username)", "암호화된 비번 (Hash)"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("현재 가입된 회원이 아무도 없습니다.")
            
        if st.button("🔧 관리자 모드 끄기"):
            st.session_state.show_admin = False
            st.rerun()
    elif admin_password:
        st.error("X 마스터 비밀번호가 틀렸습니다.")
    st.markdown("---")


# --- 7. 비로그인 화면 (로그인 / 회원가입) ---
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


# --- 8. 메인 채팅 화면 (로그인 완료 상태) ---
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
