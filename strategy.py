"""매매 판단. **이 파일 하나만** 성향에 맞게 바꾸면 됩니다.

사고팔지는 **클로드 코드가 정합니다.** 이 파일은 두 가지를 담습니다.

  INSTRUCTIONS  클로드 코드에게 주는 투자 원칙. 성향을 바꾸려면 여기를 고칩니다.
  decide(m)     클로드 코드의 답을 받아 최종 결정. 여기서 넘지 말아야 할 선을 지킵니다.

클로드 코드가 없거나(설치 안 됨·시간 초과·이상한 답) 판단을 못 받으면 **아무것도
사지 않습니다.** 다만 손절·익절은 클로드 코드에게 묻지 않고 규칙이 먼저 자릅니다.
클로드 코드가 조용한 날에도 손절은 동작해야 하기 때문입니다.

고친 뒤에는 `python check.py` 로 검사하세요. 통과해야 씁니다.

━━ 지켜야 하는 약속 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

아래 다섯 개를 반드시 정의할 것:
  SYMBOLS        국내 6자리 종목코드 문자열 리스트. 안 하면 []
                 (삼성전자 005930, SK하이닉스 000660, 카카오 035720,
                  NAVER 035420, 현대차 005380, LG에너지솔루션 373220)
  US_SYMBOLS     미국 티커 대문자 리스트. 안 하면 []
                 (애플 AAPL, 마이크로소프트 MSFT, 엔비디아 NVDA,
                  테슬라 TSLA, 구글 GOOGL, 아마존 AMZN)
  BUY_AMOUNT     국내 한 종목에 넣을 금액(원, 정수)
  US_BUY_AMOUNT  미국 한 종목에 넣을 금액(달러, 정수)
  MAX_HOLDINGS   동시에 들고 갈 최대 종목 수(정수, 1 이상)

그리고 decide(m) 함수가 ("buy"|"sell"|"hold", 이유문자열) 튜플을 돌려줄 것.

없어도 되지만 있으면 쓰이는 세 가지:
  US_SESSIONS   미국장을 볼 시간대. "pre"(프리마켓) "regular"(정규장)
                "after"(애프터마켓) 중에서 고른 리스트. 없으면 정규장만 봅니다.
                프리·애프터에도 주문은 들어가지만(지정가만) 사려는 사람이 적어
                원하는 값에 안 걸리고, 지표는 일봉이라 아직 어제 것입니다.
  INSTRUCTIONS  클로드 코드에게 그대로 가는 투자 원칙. 없으면 원칙 없이 판단합니다.
  facts(m)      클로드 코드에게 더 보여 줄 사실을 문자열 리스트로 돌려줍니다.
                기본으로는 최근 20일 종가·5일/20일 평균·52주 고저·보유 상태·
                공시가 갑니다. **여기에 없는 값을 원칙에 쓰려면 facts()로
                직접 계산해서 넘겨야 합니다.** 예를 들어 "RSI 70 넘으면 사지 마"
                라고 쓰려면:

                    def facts(m):
                        value = rsi(m["closes"])          # 직접 계산
                        return [f"- RSI(14): {value}"] if value else []

                넘기지 않은 값을 원칙에서 부르면 클로드 코드가 종가로 암산하다 틀립니다.

이것만 지키면 나머지는 자유입니다. 다만:
  - 계산용 표준 라이브러리는 자유롭게 (math, statistics, random, re, json, datetime,
    zoneinfo, itertools, functools, collections, decimal …). 파일·네트워크·프로세스에
    손대는 모듈(os, sys, io, pathlib, socket, urllib, subprocess …)과 eval/exec/open은 금지
  - **여기서 클로드 코드를 직접 부르지 않습니다.** 부를 수도 없습니다(네트워크 금지).
    묻는 일은 클로드 코드 예약이 하고, 이 파일은 그 답을 받아 씁니다
  - closes 가 비어 있거나 짧아도 터지지 않게 할 것 (첫날에는 시세가 없습니다)
  - 이유 문자열은 초보자가 읽어서 이해할 수 있는 한국어로
  - 금액을 이유에 쓸 때는 통화를 맞출 것 (원 / $). m["currency"] 로 판단

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

decide()에 들어오는 m의 내용:
  m["code"]      종목코드        "005930"
  m["name"]      종목이름        "삼성전자"
  m["price"]     현재가          71_000
  m["closes"]    최근 종가들      [69800, 70100, ...]  (오래된 것부터, 오늘 포함)
  m["held"]      보유 중인가      True / False
  m["qty"]       보유 수량        0 이면 미보유
  m["avg"]       평균 매입가      미보유면 0
  m["pnl_pct"]   수익률(%)        미보유면 0.0
  m["cash"]      주문가능 현금     1_000_000
                 미국 종목이어도 **항상 원화**입니다. US_BUY_AMOUNT(달러)와 직접
                 비교하지 마세요. 살 수 있는 수량은 앱이 따로 확인합니다.

  ── 클로드 코드의 판단 (예약이 `--do` 로 넘겨 준 것) ──
  m["ai"]  {"decision": "buy"|"sell"|"hold", "reason": "왜 그렇게 봤는지"}
           None 이면 판단을 받지 못한 것입니다. 사면 안 됩니다.

  ── 시세에 딸려 오는 값 (추가 조회 없음) ──
  m["change_pct"]  전일 대비(%)      2.43
  m["turnover"]    거래대금          국내 원, 미국 달러
  m["high_52w"]    52주 최고가       미보유 자료면 None
  m["low_52w"]     52주 최저가
  m["per"]         PER              미국은 None일 수 있음
  m["pbr"]         PBR              미국은 None
  m["market_cap"]  시가총액(원)      미국은 None
  m["industry"]    업종             "코스피 전기·전자"
  m["market"]      어느 장인가       "kr" 또는 "us"
  m["currency"]    통화             "KRW" 또는 "USD"

값이 None이면 "모른다"는 뜻입니다. 0으로 읽지 마세요.

국내와 미국이 같은 모양으로 들어오므로 decide()는 둘을 구분하지 않아도 됩니다.
장을 나눠서 다르게 굴리고 싶으면 m["market"]을 보면 됩니다.
"""

# ── 무엇을 얼마나 살지 ───────────────────────────────────────────────
SYMBOLS = []  # 국내는 하지 않습니다. 하려면 6자리 종목코드를 넣으세요
# 미국: 엔비디아 · 마이크로소프트 · 메타 · 테슬라 · 브로드컴 · SOXL(반도체 3배)
#      · TQQQ(나스닥100 3배) — 이 종목만 딥매수 규칙으로 굴립니다. 아래 DIP_BUY 참고
US_SYMBOLS = ["NVDA", "MSFT", "META", "TSLA", "AVGO", "SOXL", "TQQQ"]
# 시장 상태를 볼 기준 종목. **사고팔지 않습니다.** 레버리지 ETF는 자기 200일선으로
# 시장을 읽으면 틀립니다(변동성 때문에 지수와 어긋납니다). 지수를 직접 봅니다.
MARKET_INDEX = "QQQM"
BUY_AMOUNT = 300_000  # 국내 한 종목에 넣을 금액(원). 국내를 안 하므로 쓰이지 않습니다
US_BUY_AMOUNT = 2000  # 미국 한 종목에 넣을 금액(달러). 약 290만원(환율 1,450원 기준)
# 종목마다 금액을 달리 하고 싶을 때만 적습니다. 없는 종목은 위 US_BUY_AMOUNT를 씁니다.
US_BUY_AMOUNTS = {"SOXL": 10000}  # SOXL 한 자리 $10,000 (약 1,450만원)
# 딥매수로 굴릴 종목. 여기 있는 종목은 위 「사라」의 돌파 조건을 **쓰지 않습니다.**
# 오르는 것을 사는 것이 아니라 **떨어진 것을 사기** 때문에 정반대 규칙입니다.
#
#   entry "index_dip"  MARKET_INDEX 가 52주 고점 대비 entry_dip 이하로 빠졌고,
#                      그러면서도 index_sma_days 일선 위일 것
#   entry "band"       그 종목이 자기 볼린저 하단(band_days 일선 - band_mult × 표준편차)
#                      아래로 밀렸을 것
#   exit  "old_high"   자기 52주 고점을 회복하면 익절 (몇 달짜리)
#   exit  "ma20"       band_days 일 이동평균을 회복하면 익절 (며칠짜리)
#   손절                STOP_LOSS_PCTS 의 값 (아래)
DIP_BUY = {
    # 나스닥100 3배. 지수가 크게 눌렸을 때만 들어갑니다. index_sma_days 조건이 핵심인데,
    # 이것을 빼면 진짜 하락장에서 3배 상품을 계속 받다가 원금이 녹습니다.
    "TQQQ": {"entry": "index_dip", "entry_dip": -10.0, "index_sma_days": 200,
             "exit": "old_high"},
    # 반도체 3배. 볼린저 하단 아래로 밀리면 사서 20일선 회복에 팝니다.
    # 지난 2년을 되돌려 보니 돌파로 사는 것보다 이쪽이 확실히 나았습니다(review.py).
    # SOXL이 -62.7% 무너지던 구간에서도 이 규칙은 +44.9% 였습니다. 눌릴 때마다
    # 반등을 주워 담기 때문입니다. 대신 급등장은 대부분 놓칩니다.
    # 지수 200일선 조건은 넣지 않았습니다. SOXL의 눌림은 지수가 평온할 때가 아니라
    # 흔들릴 때 나와서, 이 표본에서는 필터가 기회를 깎기만 했습니다.
    "SOXL": {"entry": "band", "band_mult": 1.5, "band_days": 20, "exit": "ma20"},
}
MAX_HOLDINGS = 3  # 동시에 들고 갈 최대 종목 수 (딥매수 자리는 여기 안 셉니다)
US_SESSIONS = ["regular"]  # 미국을 볼 시간대: "pre" 프리마켓 · "regular" 정규장 · "after" 애프터마켓

# ── 클로드 코드에게 주는 투자 원칙 ─────────────────────────────────────────
# 성향을 바꾸고 싶으면 여기를 고치세요. 이 글이 그대로 클로드 코드에게 갑니다.
# 지시가 구체적일수록 판단이 일관됩니다. "알아서 잘"이라고 쓰면 그날그날 달라집니다.
INSTRUCTIONS = """너는 오르고 있는 흐름에 올라타는 추세추종 투자자야.
바닥을 맞히려 하지 마라. 이미 올라가고 있는 것을 확인하고 따라 들어간다.

아래 「사라」의 네 줄은 부탁이 아니라 **규칙이 강제한다.** 못 채운 종목은 네가
buy라고 해도 안 사진다. 그러니 그 네 줄은 최소 조건일 뿐이라고 생각하고, 그것을
채운 종목 안에서 뉴스와 흐름을 보고 정말 살 만한지를 골라라.

사라:
- 현재가가 5일 이동평균과 20일 이동평균을 모두 넘었을 때만
- 5일 이동평균이 20일 이동평균 위에 있을 때만 (흐름의 방향이 위)
- MACD가 신호선 위일 때만 (차이가 양수)
- RSI(14)가 70을 넘으면 사지 마. 이미 달아오른 뒤에 들어가는 것이다
- 52주 최고가 근처인 것은 막지 않는다. 추세추종에서는 신고가가 오히려 정상이다

팔아라:
- 현재가가 5일 이동평균 아래로 내려오고 MACD 차이가 음수로 꺾였으면
- RSI(14)가 75를 넘었으면 (과열은 되돌림이 크다)

이 종목들은 하루 3~5% 움직임이 흔하다. 하루 빠졌다고 흐름이 꺾인 것은 아니다.
5일 평균과 MACD가 함께 꺾였을 때만 꺾인 것으로 본다.

SOXL과 TQQQ는 위 종목들과 **정반대 자리**다. 둘 다 눌렸을 때 사는 딥매수 자리이고,
돌파 조건을 쓰지 않는다. 규칙이 먼저 거르니, 네게 물어보는 순간은 이미 살 자리다.

SOXL은 반도체 지수를 3배로 따라간다. 볼린저 하단 아래로 밀렸을 때 사서 20일 평균을
회복하면 판다. 며칠짜리 자리다. 네가 볼 것은 하나다 — **이 눌림이 곧 되돌아올
눌림인가, 업황이 꺾인 것인가.** 뉴스가 감산·재고조정·수요 둔화처럼 분기를 넘길
이야기를 하고 있으면 hold 해라. 하루 9% 흔들리는 것 자체는 이 종목에서 정상이니
그걸 이유로 삼지 마라. 다만 NVDA·AVGO를 이미 들고 있으면 같은 반도체에 세 번
거는 것이니, 그때는 한 번 더 따져 보고 애매하면 hold 해라.

TQQQ는 위 종목들과 **정반대 자리**다. 나스닥100을 3배로 따라가는 상품이고, 여기서는
돌파를 사는 것이 아니라 **지수가 눌렸을 때 사는** 자리로 쓴다. 규칙이 알아서 걸러
주니, 네게 물어보는 순간은 이미 "지수가 52주 고점 대비 10% 넘게 빠졌고 그런데도
200일선 위"인 때다. 그때 네가 볼 것은 하나다 — **이번 하락이 눌림인가, 무너짐의
시작인가.** 뉴스가 금리·실적·규제처럼 몇 달 갈 이야기를 하고 있으면 hold 해라.
그리고 TQQQ는 몇 달을 들고 가는 자리라 며칠 흔들린다고 팔지 않는다. 파는 것은
전고점을 되찾았을 때이고, 그것도 규칙이 한다.

이유에는 위에서 본 숫자를 그대로 넣어라.
자료가 없어 안 적힌 지표는 없는 셈 쳐라.
애매하면 hold 해라.
"""

# ── 클로드 코드가 뭐라 하든 지키는 선 ──────────────────────────────────────
# 판단은 클로드 코드가 하지만, 이 선은 규칙이 지킵니다. 클로드 코드가 죽어도 동작합니다.
STOP_LOSS_PCT = -20.0  # 이만큼 떨어지면 묻지 않고 손절
# -10%는 이 종목들에게 하루치 움직임이라, 흐름이 안 꺾였는데도 잘려 나갔습니다.
# 지난 1년 일봉으로 되돌려 보니 승률 75.7%인데 합치면 잃고 있었습니다(review.py).
TAKE_PROFIT_PCT = 3.0  # 이만큼 오르면 묻지 않고 익절
# 종목마다 손절선을 달리 하고 싶을 때만 적습니다. 없는 종목은 위 STOP_LOSS_PCT를 씁니다.
# SOXL은 반도체 지수를 3배로 따라가서 하루 9% 움직임이 흔합니다. -10%면 흐름이
# 안 꺾였는데도 거의 매번 잘립니다. 그래서 SOXL만 기본의 두 배로 넓게 잡습니다.
STOP_LOSS_PCTS = {"SOXL": -20.0, "TQQQ": -30.0}
# 종목마다 익절선을 달리 하고 싶을 때만 적습니다. None이면 %로는 익절하지 않습니다.
# 딥매수 자리는 %가 아니라 값(전고점·20일선)으로 팝니다. +3%에 팔아 버리면 이기는
# 폭이 지는 폭보다 작아져서, 승률이 아무리 높아도 합치면 잃습니다. 실제로 SOXL을
# 돌파+3%로 굴린 지난 2년이 승률 95%에 복리 +1.3% 였습니다.
TAKE_PROFIT_PCTS = {"TQQQ": None, "SOXL": None}

# 크게 버는 규칙보다 크게 잃지 않는 규칙이 오래갑니다.
MIN_TURNOVER_KRW = 10_000_000_000  # 국내 하루 거래대금 100억 미만이면 안 삼
MIN_TURNOVER_USD = 50_000_000  # 미국 하루 거래대금 5천만 달러 미만이면 안 삼
# 돌파매매라 신고가 돌파를 막지 않습니다. 100이면 52주 최고가를 넘는 순간 걸러져서,
# 정작 사려던 돌파를 놓칩니다. 120은 "52주 최고가보다 20% 넘게 뛴 값이면 사지 않는다"는
# 뜻입니다. 정상적인 돌파는 통과하고, 하루에 미친 듯이 솟은 자리만 거릅니다.
MAX_NEAR_HIGH_PCT = 120.0

# 이만큼 달아오른 것은 사지 않습니다. 아래 「사라」의 RSI 줄과 같은 값입니다.
RSI_TOO_HOT = 70.0


def decide(m):
    """한 종목을 보고 무엇을 할지 정합니다. ("buy"|"sell"|"hold", 이유)

    순서가 중요합니다. 클로드 코드에게 묻기 **전에** 규칙이 먼저 걸러야, 클로드 코드가
    조용한 날에도 손절이 돌고 사면 안 되는 종목을 사지 않습니다.
    """
    if m["held"]:
        # 손절·익절은 클로드 코드 의견을 묻지 않습니다. 넘으면 그냥 팝니다.
        stop = STOP_LOSS_PCTS.get(m["code"], STOP_LOSS_PCT)
        if m["pnl_pct"] <= stop:
            return "sell", f"손절 기준 {stop}% 도달 (현재 {m['pnl_pct']:+.2f}%)"

        if m["code"] in DIP_BUY:
            # 딥매수 자리는 %가 아니라 **값**으로 팝니다. 되찾을 자리를 정해 두고 갑니다.
            rule = DIP_BUY[m["code"]]
            if rule.get("exit") == "ma20":
                back = moving_average([float(c) for c in (m.get("closes") or [])],
                                      rule.get("band_days", 20))
                if back and m["price"] >= back:
                    return "sell", (
                        f"{rule.get('band_days', 20)}일 평균 {money(back, m)}을 회복해 "
                        f"익절합니다 (현재 {m['pnl_pct']:+.2f}%)"
                    )
            else:
                high = m.get("high_52w")
                if high and m["price"] >= high:
                    return "sell", (
                        f"52주 고점 {money(high, m)}을 회복해 익절합니다 "
                        f"(현재 {m['pnl_pct']:+.2f}%)"
                    )
        elif m["pnl_pct"] >= TAKE_PROFIT_PCT:
            return "sell", f"익절 기준 +{TAKE_PROFIT_PCT}% 도달 (현재 {m['pnl_pct']:+.2f}%)"
    else:
        skip = why_not_buy(m)
        if skip:
            return "hold", skip

    call = m.get("ai") or {}
    decision = call.get("decision")
    reason = (call.get("reason") or "").strip()
    if decision not in ("buy", "sell", "hold"):
        # 판단을 못 받았습니다. 모르는 상태에서 사지 않습니다.
        return "hold", "클로드 코드 판단을 받지 못해 이번에는 아무것도 하지 않습니다"
    if not reason:
        reason = "클로드 코드가 이유를 적지 않았습니다"

    if m["held"]:
        return ("sell", reason) if decision == "sell" else ("hold", reason)
    return ("buy", reason) if decision == "buy" else ("hold", reason)


def why_not_buy(m):
    """클로드 코드에게 묻기도 전에 거를 이유. 없으면 None.

    잘 고르는 것보다 안 사도 될 것을 거르는 쪽이 손실을 줄입니다.
    """
    floor = MIN_TURNOVER_USD if m["currency"] == "USD" else MIN_TURNOVER_KRW
    turnover = m.get("turnover")
    if turnover is None or turnover <= 0:
        return "거래대금을 확인하지 못해 이번에는 사지 않습니다"
    if turnover < floor:
        return f"거래가 너무 적어 팔 때 곤란할 수 있습니다 (거래대금 {money(turnover, m)})"

    # 딥매수 자리는 정반대 규칙입니다. 돌파를 기다리지 않고 눌린 자리를 삽니다.
    if m["code"] in DIP_BUY:
        return why_not_dip_buy(m)

    high = m.get("high_52w")
    if high and m["price"] >= high * MAX_NEAR_HIGH_PCT / 100:
        return f"52주 최고 {money(high, m)}에 가까워 지금은 사지 않습니다"

    # 돌파 조건은 부탁이 아니라 규칙입니다. INSTRUCTIONS 에만 적어 두면 클로드 코드가
    # 성실히 읽어 주기를 바라는 것뿐이고, 어느 회차에 대충 보면 그냥 사집니다.
    # 여기서 걸면 판단을 묻기 전에 한 번, 주문 직전에 또 한 번 걸립니다.
    closes = [float(c) for c in (m.get("closes") or [])]
    price = m["price"]

    quick, slow = moving_average(closes, 5), moving_average(closes, 20)
    if quick is None or slow is None:
        return "이동평균을 낼 만큼 시세가 쌓이지 않아 사지 않습니다"
    if price < quick or price < slow:
        return (
            f"아직 평균을 넘지 못했습니다 "
            f"(현재가 {money(price, m)} · 5일 {money(quick, m)} · 20일 {money(slow, m)})"
        )
    if quick < slow:
        return f"5일 평균 {money(quick, m)}이 20일 평균 {money(slow, m)} 아래라 흐름이 위가 아닙니다"

    line, signal = macd(closes)
    if line is None:
        return "MACD를 낼 만큼 시세가 쌓이지 않아 사지 않습니다"
    if line <= signal:
        return f"MACD {line:,.1f}이 신호선 {signal:,.1f} 아래라 아직 올라타지 않습니다"

    strength = rsi(closes)
    if strength is None:
        return "RSI를 낼 만큼 시세가 쌓이지 않아 사지 않습니다"
    if strength > RSI_TOO_HOT:
        return f"RSI {strength}로 이미 달아올라 지금 들어가지 않습니다"
    return None


def why_not_dip_buy(m):
    """딥매수 자리를 지금 사면 안 되는 이유. 없으면 None.

    보는 것은 이 종목이 아니라 **지수(MARKET_INDEX)** 입니다. 3배 상품은 변동성 때문에
    자기 200일선이 지수와 어긋납니다. 실제로 지수는 200일선 위인데 3배 상품은 아래인
    날이 있었고, 그날이 바로 사야 할 자리였습니다.
    """
    rule = DIP_BUY[m["code"]]

    if rule.get("entry") == "band":
        closes = [float(c) for c in (m.get("closes") or [])]
        days = rule.get("band_days", 20)
        mid = moving_average(closes, days)
        if mid is None:
            return f"{days}일 평균을 낼 만큼 시세가 쌓이지 않아 사지 않습니다"
        spread = stdev(closes[-days:])
        floor_price = mid - rule.get("band_mult", 2.0) * spread
        if m["price"] >= floor_price:
            return (
                f"아직 볼린저 하단 {money(floor_price, m)} 위입니다 "
                f"(현재 {money(m['price'], m)} · {days}일 평균 {money(mid, m)})"
            )
        return None

    index = [float(c) for c in (m.get("index_closes") or [])]
    days = rule["index_sma_days"]
    if len(index) < days:
        return f"지수({MARKET_INDEX}) 시세가 {days}일치도 없어 판단할 수 없습니다"

    now = index[-1]
    line = sum(index[-days:]) / days
    if now < line:
        return (
            f"지수가 {days}일 평균 아래입니다. 하락장에서 3배 상품을 받으면 "
            f"눌린 자리가 아니라 계속 떨어지는 자리입니다 (이격 {now / line - 1:+.1%})"
        )

    # 52주 고점은 지수 기준으로 봅니다. 최근 1년치가 없으면 있는 만큼만 씁니다.
    high = max(index[-252:])
    fall = (now / high - 1) * 100
    if fall > rule["entry_dip"]:
        return (
            f"지수가 아직 덜 빠졌습니다 (52주 고점 대비 {fall:+.1f}%, "
            f"{rule['entry_dip']:+.0f}% 이하여야 삽니다)"
        )
    return None


def facts(m):
    """클로드 코드에게 더 보여 줄 사실. 여기서 돌려준 줄이 --scan 출력에 그대로 붙습니다.

    지표를 넘기지 않으면 "흐름이 좋아 보인다" 같은 두루뭉술한 이유만 돌아옵니다.
    숫자를 주면 "5일 평균 71,200원을 넘었고 RSI 58" 처럼 확인할 수 있는 말이 됩니다.
    자료가 모자란 지표는 아예 적지 않습니다. 0으로 적으면 값이 0인 줄 압니다.
    """
    closes = [float(c) for c in (m.get("closes") or [])]
    lines = []
    for days in (5, 20, 60):
        avg = moving_average(closes, days)
        if avg is not None:
            lines.append(f"- {days}일 이동평균: {money(avg, m)}")
    strength = rsi(closes)
    if strength is not None:
        lines.append(f"- RSI(14): {strength} (70 위 과열 · 30 아래 과매도)")
    line, signal = macd(closes)
    if line is not None:
        # 차이의 부호가 곧 신호입니다. 양수면 신호선 위, 음수면 아래.
        lines.append(f"- MACD: {line:,.1f} · 신호선 {signal:,.1f} · 차이 {line - signal:+,.1f}")

    # 딥매수 자리는 자기 지표가 아니라 지수를 보고 판단합니다. 그 숫자를 같이 넘깁니다.
    if m["code"] in DIP_BUY:
        rule = DIP_BUY[m["code"]]
        lines.append("- 이 종목은 딥매수 자리입니다. 돌파가 아니라 눌린 자리를 삽니다")
        if rule.get("entry") == "band":
            days = rule.get("band_days", 20)
            mid = moving_average(closes, days)
            if mid is not None:
                edge = mid - rule.get("band_mult", 2.0) * stdev(closes[-days:])
                lines.append(f"- 볼린저 {days}일 · 중간 {money(mid, m)} · "
                             f"하단({rule.get('band_mult', 2.0)}σ) {money(edge, m)} "
                             f"({'하단 아래 — 살 자리' if m['price'] < edge else '아직 하단 위'})")
                if m["held"]:
                    lines.append(f"- 익절은 {days}일 평균 {money(mid, m)}을 회복할 때입니다. "
                                 f"%로 팔지 않습니다")
        else:
            index = [float(c) for c in (m.get("index_closes") or [])]
            if index:
                days = rule["index_sma_days"]
                now, high = index[-1], max(index[-252:])
                lines.append(f"- 지수({MARKET_INDEX}) 현재 {now:,.2f} · 52주 고점 {high:,.2f} "
                             f"· 낙폭 {(now / high - 1) * 100:+.1f}% "
                             f"(진입 기준 {rule['entry_dip']:+.0f}%)")
                if len(index) >= days:
                    avg = sum(index[-days:]) / days
                    lines.append(f"- 지수 {days}일 평균 {avg:,.2f} "
                                 f"({'위' if now >= avg else '아래'}, 이격 {now / avg - 1:+.1%})")
            if m["held"] and m.get("high_52w"):
                lines.append(f"- 익절은 이 종목이 자기 52주 고점 {money(m['high_52w'], m)}을 "
                             f"회복할 때입니다. %로 팔지 않습니다")
    return lines


def moving_average(closes, days):
    """최근 종가 평균. 자료가 모자라면 None."""
    if len(closes) < days:
        return None
    return sum(closes[-days:]) / days


def stdev(values):
    """표준편차(모집단). 볼린저 밴드 폭을 낼 때 씁니다."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5


def rsi(closes, days=14):
    """상대강도지수 0~100. 오른 폭과 내린 폭의 비율입니다."""
    if len(closes) < days + 1:
        return None
    changes = [b - a for a, b in zip(closes[-days - 1 : -1], closes[-days:], strict=False)]
    up = sum(c for c in changes if c > 0) / days
    down = -sum(c for c in changes if c < 0) / days
    if not down:
        return 100.0 if up else 50.0
    return round(100 - 100 / (1 + up / down), 1)


def _ema(closes, days):
    """지수이동평균 줄. 처음 days개의 평균에서 출발합니다."""
    if len(closes) < days:
        return []
    weight = 2 / (days + 1)
    out = [sum(closes[:days]) / days]
    for value in closes[days:]:
        out.append(value * weight + out[-1] * (1 - weight))
    return out


def macd(closes, fast=12, slow=26, smooth=9):
    """(MACD, 신호선). 신호선을 위로 뚫으면 상승 전환으로 봅니다."""
    quick, slack = _ema(closes, fast), _ema(closes, slow)
    if not quick or not slack:
        return None, None
    length = min(len(quick), len(slack))
    line = [q - s for q, s in zip(quick[-length:], slack[-length:], strict=False)]
    signal = _ema(line, smooth)
    if not signal:
        return None, None
    return round(line[-1], 2), round(signal[-1], 2)


def money(value, m):
    """국내는 원, 미국은 달러로 적습니다. 이유 문구에 그대로 쓰입니다."""
    if m.get("currency") == "USD":
        return f"${value:,.2f}"
    return f"{value:,.0f}원"
