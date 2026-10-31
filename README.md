# 💱 실시간 환율 챗봇

"100달러는 원화로 얼마야?", "1유로는 엔화로 얼마야?"처럼 자연어로 물으면
[Frankfurter Exchange Rates API](https://frankfurter.dev/)의 최신 일별 기준 환율로 환산해 답하는 Streamlit + LangChain 에이전트 웹앱입니다.

> Frankfurter 환율은 실시간 체결가가 아니라 **최신 일별 기준 환율**입니다.

## 파일 구성

| 파일 | 역할 |
| --- | --- |
| `app.py` | Streamlit 채팅 화면 |
| `agent.py` | 환율 도구(`get_exchange_rate`, `convert_currency`), 시스템 프롬프트, 에이전트 생성 |
| `.env.example` | 환경 변수 예시 (`.env`로 복사해서 사용) |
| `requirements.txt` | 필요한 패키지 목록 |

## 실행 방법 (Windows + Git Bash 기준)

### 1. 저장소 받기

```bash
git clone <이 저장소 주소>
cd my-agent2
```

### 2. 가상환경 만들기 & 활성화

```bash
python -m venv .venv
source .venv/Scripts/activate
```

> macOS/Linux: `source .venv/bin/activate`

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. `.env` 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 OpenAI API 키를 입력합니다.

```
OPENAI_API_KEY=여기에_본인_키_입력
```

> `.env`는 `.gitignore`에 포함되어 있어 커밋되지 않습니다. 키를 코드에 직접 쓰지 마세요.

### 5. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`이 열립니다.

## 예시 질문

- 100달러는 원화로 얼마야?
- 1유로는 엔화로 얼마야?
- 오늘 엔화 환율 알려줘
- 50000원은 달러로 얼마야?
