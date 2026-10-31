"""환율 챗봇의 도구, 시스템 프롬프트, 에이전트 생성 로직."""

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

load_dotenv()

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/rate/{base}/{quote}"
TIMEOUT_SECONDS = 10


def _fetch_rate(base: str, quote: str) -> dict:
    """Frankfurter API에서 환율을 조회한다. 실패하면 {'error': 메시지}를 반환한다."""
    base = base.strip().upper()
    quote = quote.strip().upper()

    if len(base) != 3 or len(quote) != 3 or not base.isalpha() or not quote.isalpha():
        return {"error": f"통화 코드는 3자리 ISO 코드여야 합니다. (입력: {base}, {quote})"}

    url = FRANKFURTER_URL.format(base=base.lower(), quote=quote.lower())
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        return {"error": f"환율 API 응답이 {TIMEOUT_SECONDS}초 안에 오지 않았습니다. 잠시 후 다시 시도해 주세요."}
    except requests.exceptions.RequestException as e:
        return {"error": f"환율 API에 연결하지 못했습니다: {e}"}

    try:
        data = response.json()
    except ValueError:
        return {"error": f"환율 API 응답을 해석하지 못했습니다. (HTTP {response.status_code})"}

    if response.status_code != 200 or "rate" not in data:
        message = data.get("message", "알 수 없는 오류")
        return {"error": f"환율을 조회하지 못했습니다: {message} (HTTP {response.status_code})"}

    return {
        "base": data.get("base", base),
        "quote": data.get("quote", quote),
        "rate": float(data["rate"]),
        "date": data.get("date", "알 수 없음"),
    }


def _format_amount(value: float, currency: str) -> str:
    """금액을 천 단위 쉼표로 표시한다. 원화(KRW)·엔화(JPY)는 정수로 반올림한다."""
    if currency in ("KRW", "JPY"):
        return f"{round(value):,}"
    return f"{value:,.2f}"


@tool
def get_exchange_rate(base: str, quote: str) -> str:
    """두 통화 사이의 최신 일별 기준 환율과 기준일을 조회합니다.

    "1 기준 통화 = ? 대상 통화"를 알고 싶을 때 사용합니다.
    예: "달러 환율 알려줘", "엔화 대비 원화 환율은?"

    Args:
        base: 기준 통화의 3자리 ISO 코드 (예: USD)
        quote: 대상 통화의 3자리 ISO 코드 (예: KRW)

    통화 이름 → ISO 코드 매핑:
        달러/미국 달러=USD, 원/원화=KRW, 엔/엔화=JPY, 유로=EUR,
        위안/위안화=CNY, 파운드=GBP, 스위스 프랑=CHF, 캐나다 달러=CAD,
        호주 달러=AUD, 홍콩 달러=HKD, 싱가포르 달러=SGD, 대만 달러=TWD,
        바트=THB, 동=VND
    """
    result = _fetch_rate(base, quote)
    if "error" in result:
        return f"오류: {result['error']}"

    return (
        f"기준 통화: {result['base']}\n"
        f"대상 통화: {result['quote']}\n"
        f"1 {result['base']} = {result['rate']:,.4f} {result['quote']}\n"
        f"환율 기준일: {result['date']}"
    )


@tool
def convert_currency(amount: float, base: str, quote: str) -> str:
    """금액을 한 통화에서 다른 통화로 환산합니다. 환산 계산은 이 도구가 직접 수행합니다.

    "100달러는 원화로 얼마야?"처럼 특정 금액을 바꿀 때 사용합니다.
    환산 결과를 직접 계산하지 말고 반드시 이 도구의 결과를 그대로 사용하세요.

    Args:
        amount: 환산할 금액 (숫자, 예: 100)
        base: 환산 전 통화의 3자리 ISO 코드 (예: USD)
        quote: 환산 후 통화의 3자리 ISO 코드 (예: KRW)

    통화 이름 → ISO 코드 매핑:
        달러/미국 달러=USD, 원/원화=KRW, 엔/엔화=JPY, 유로=EUR,
        위안/위안화=CNY, 파운드=GBP, 스위스 프랑=CHF, 캐나다 달러=CAD,
        호주 달러=AUD, 홍콩 달러=HKD, 싱가포르 달러=SGD, 대만 달러=TWD,
        바트=THB, 동=VND
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return f"오류: 금액을 숫자로 해석하지 못했습니다. (입력: {amount})"

    result = _fetch_rate(base, quote)
    if "error" in result:
        return f"오류: {result['error']}"

    converted = amount * result["rate"]
    return (
        f"기준 통화: {result['base']}\n"
        f"대상 통화: {result['quote']}\n"
        f"1 {result['base']} 환율: {result['rate']:,.4f} {result['quote']}\n"
        f"환산 전 금액: {_format_amount(amount, result['base'])} {result['base']}\n"
        f"환산 금액: {_format_amount(converted, result['quote'])} {result['quote']}\n"
        f"환율 기준일: {result['date']}"
    )


SYSTEM_PROMPT = """당신은 환율 안내 챗봇입니다.

## 규칙
- 환율이나 금액 환산 질문이면 반드시 도구를 사용하세요.
  - 특정 금액을 바꾸는 질문 → convert_currency
  - 환율 자체를 묻는 질문 → get_exchange_rate
- 도구 결과만 근거로 답하세요. 환율이나 금액을 추측하거나 직접 계산하지 마세요.
- 통화 이름은 ISO 코드로 바꿔서 도구에 전달하세요. (달러=USD, 원=KRW, 엔=JPY, 유로=EUR 등)
- 도구가 "오류:"로 시작하는 결과를 돌려주면, 그 내용을 사용자에게 짧게 알리고 다시 질문해 달라고 안내하세요.
- 환율과 무관한 질문에는 "저는 환율 안내 챗봇이에요. 예를 들어 '100달러는 원화로 얼마야?'처럼 환율 관련 질문을 해 주세요." 정도로 짧게 안내하세요.

## 답변 형식 (마크다운, 반드시 지킬 것)
금액 환산 질문일 때:

100달러(USD)는 **133,717원(KRW)** 입니다.

- 기준 통화: USD (미국 달러)
- 대상 통화: KRW (대한민국 원)
- 1 USD 환율: 1,337.1700 KRW
- 환산 금액: 133,717 KRW
- 환율 기준일: 2026-10-31

참고로 Frankfurter 환율은 실시간 체결가가 아니라 **최신 일별 기준 환율**입니다.

환율 자체를 묻는 질문일 때는 첫 줄을 "1달러(USD)는 **1,337.17원(KRW)** 입니다." 형태로 쓰고,
환산 금액 항목에는 1단위 기준 금액을 적으세요. 숫자는 도구 결과의 값을 그대로 옮기세요.
"""


def build_agent():
    """모델과 도구로 환율 에이전트를 만든다."""
    model = init_chat_model("gpt-5.4-mini", temperature=0)
    return create_agent(
        model,
        tools=[get_exchange_rate, convert_currency],
        system_prompt=SYSTEM_PROMPT,
    )
