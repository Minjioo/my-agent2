"""실시간 환율 챗봇 Streamlit 화면."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="실시간 환율 챗봇", page_icon="💱")

st.title("💱 실시간 환율 챗봇")
st.caption(
    "Frankfurter API의 최신 일별 기준 환율로 환산합니다. "
    "실시간 체결가(은행·거래소 매매가)가 아닙니다."
)

st.info(
    "**이렇게 물어보세요**\n\n"
    "- 100달러는 원화로 얼마야?\n"
    "- 1유로는 엔화로 얼마야?\n"
    "- 오늘 엔화 환율 알려줘\n"
    "- 50000원은 달러로 얼마야?"
)

if not os.getenv("OPENAI_API_KEY"):
    st.error(
        "OPENAI_API_KEY가 설정되지 않았습니다. "
        "프로젝트 폴더에 `.env` 파일을 만들고 `OPENAI_API_KEY=키값`을 입력한 뒤 앱을 다시 실행하세요. "
        "(`.env.example` 참고)"
    )
    st.stop()

from agent import build_agent  # noqa: E402  키 확인 후에 불러온다


@st.cache_resource
def get_agent():
    return build_agent()


agent = get_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("환율이 궁금한 내용을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("환율을 조회하는 중..."):
            try:
                response = agent.invoke({"messages": st.session_state.messages})
                answer = response["messages"][-1].text
            except Exception as e:
                answer = f"답변을 만드는 중 오류가 발생했습니다: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
