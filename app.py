import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Self Thinking Chatbot v1", page_icon="❔", layout="centered")

st.title("안녕하세요! 저는 Beta-T에요")
st.caption("이 챗봇은 당신이 스스로 답을 찾을 수 있도록 도와줍니다.")

# 2. Gemini API 키 설정 (Streamlit Secrets 보안 기능 활용)
# 테스트 시에는 'YOUR_API_KEY'에 직접 넣어도 되지만, 배포 시에는 Secrets 시스템을 씁니다.
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    # 로컬 테스트용 (Secrets가 없을 때)
    genai.configure(api_key="AQ.Ab8RN6KC5DpBgtEw2bxuK0l0F5imUQtjfuwdFF-ga0S7_Ow1pQ") 

# 3. 우리가 완성한 영어 프롬프트를 System Instruction에 주입
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

# 4. 세션 상태(대화 기록) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    # 모델 설정 시 system_instruction을 주입합니다.
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", # 빠르고 가벼운 플래시 모델 추천
        system_instruction=system_instruction
    )
    st.session_state.chat_session = model.start_chat(history=[])

# 5. 기존 대화 내용 화면에 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력창 및 AI 답변 로직
if user_input := st.chat_input("어떤 생각이나 고민을 나누고 싶으신가요?"):
    # 사용자 메시지 표시 및 저장
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Gemini API 호출 및 답변 수집
    try:
        response = st.session_state.chat_session.send_message(user_input)
        ai_response = response.text

        # AI 메시지 표시 및 저장
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
