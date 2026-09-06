"""NH PLUG 공식 API 얇은 래퍼. 여기 있는 함수가 전부입니다.

호출 형태는 실계좌 주문으로 검증된 것을 그대로 씁니다. 추측한 필드는 없습니다.
"""

import datetime
import os
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# nhplug SDK는 편의를 위해 현재 폴더의 상위와 전역 설정까지 찾습니다. 이 프로젝트는
# 다른 폴더의 계정이 섞이면 위험하므로, SDK import 중 추가된 환경변수를 되돌린 뒤
# 이 파일 옆의 .env만 명시적으로 읽습니다. 원래부터 설정된 실제 환경변수는 보존합니다.
_ENV_BEFORE_SDK = dict(os.environ)
from nhplug import call
for _key in set(os.environ) - set(_ENV_BEFORE_SDK):
    os.environ.pop(_key, None)
for _key, _value in _ENV_BEFORE_SDK.items():
    if os.environ.get(_key) != _value:
        os.environ[_key] = _value
del _ENV_BEFORE_SDK, _key, _value

ENV = Path(__file__).with_name(".env")
load_dotenv(ENV, override=True)

# 인증은 항상 실서버에서 받습니다. 모의투자 계좌도 마찬가지입니다.
AUTH_URL = "https://api.nhplug.com:8443"
LIVE_URL = "https://api.nhplug.com:8443"
MOCK_URL = "https://moapi.nhplug.com:8443"

MOCK = os.getenv("NH_MOCK", "1") != "0"
BASE_URL = MOCK_URL if MOCK else LIVE_URL

os.environ["NHPLUG_AUTH_URL"] = AUTH_URL
os.environ["NHPLUG_BASE_URL"] = BASE_URL

_last_call = 0.0


def _call(path, payload, live_read=False):
    """공식 SDK 호출. NH 호출 간격 제한을 지키려고 1.1초씩 띄웁니다.

    시세는 모의 서버가 자주 실패해서(00007) 항상 실서버에서 읽습니다.
    읽기 전용이라 계좌를 고르거나 주문을 내지 않습니다.

    호출량 초과는 잠깐 기다리면 풀리는 일시적인 문제입니다. 여기서 몇 초 쉬었다
    다시 걸어야, 조회 한 번 실패했다고 매매 프로그램 전체가 멈추지 않습니다.
    다만 주문은 재시도하지 않습니다. 같은 주문이 두 번 나갈 수 있습니다.
    """
    global _last_call
    retriable = "/order/" not in path
    for attempt in range(4):
        wait = 1.1 - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        os.environ["NHPLUG_BASE_URL"] = LIVE_URL if live_read else BASE_URL
        try:
            return call(path, payload)
        except Exception as exc:
            last = exc
            if not retriable or attempt == 3:
                raise
            if getattr(exc, "category", "") != "rate_limit":
                raise
            time.sleep(2 * (attempt + 1))
        finally:
            os.environ["NHPLUG_BASE_URL"] = BASE_URL
    raise last


def accounts():
    """쓸 수 있는 계좌번호들. 모의는 03, 실전은 01·02 계좌입니다.

    번호로 정렬합니다. 계좌가 여러 개일 때 실행할 때마다 다른 계좌를 고르면
    어제 산 종목이 오늘 안 보이는 일이 생깁니다.
    """
    want = {"03"} if MOCK else {"01", "02"}
    found = [
        str(item.get("acct_no")).strip()
        for item in _call("/n2/acctinfo", {}).get("Output_0") or []
        if str(item.get("acct_type") or "").strip() in want
    ]
    return sorted(set(found))


def account():
    """실제로 쓸 계좌 하나."""
    found = accounts()
    if not found:
        raise SystemExit(
            f"{'모의' if MOCK else '실전'} 계좌를 찾지 못했습니다. NH에서 계좌를 확인해 주세요."
        )
    return found[0]


def quote(code):
    """국내 시세 한 번에. NH가 179개 필드를 주는데 현재가만 쓰면 아깝습니다.

    거래대금·52주 고저·PER 같은 값이 이미 같은 응답에 들어 있어, 이것들을 쓰는 데
    추가 호출이 들지 않습니다.
    """
    out = _call(
        "/krstock/quote/v1/currentPrice",
        {"iem_cd": code, "market_cd": "KRX"},
        live_read=True,
    ).get("Output_0") or {}
    value = int(float(out.get("stck_prpr") or 0))
    if value <= 0:
        raise RuntimeError(f"{code} 현재가를 받지 못했습니다.")

    def number(key, cast=float):
        try:
            return cast(out.get(key) or 0) or None
        except (TypeError, ValueError):
            return None

    return {
        "price": value,
        "name": str(out.get("iem_nm") or code).strip().lstrip("*#").strip(),
        "change_pct": number("prdy_ctrt") or 0.0,
        # NH는 국내 거래대금을 백만원 단위로 줍니다. 원 단위로 맞춥니다.
        "turnover": int((number("acml_tr_pbmn") or 0) * 1_000_000),
        "high_52w": number("w52_hgpr", int),
        "low_52w": number("w52_lwpr", int),
        "per": number("per"),
        "pbr": number("pbr"),
        # HTS 시가총액은 억원 단위입니다. 원 단위로 맞춥니다.
        "market_cap": int((number("hts_avls") or 0) * 100_000_000) or None,
        "industry": str(out.get("bstp_kor_isnm") or "").strip() or None,
    }


def price(code):
    """현재가 1개."""
    return quote(code)["price"]


def name(code):
    return quote(code)["name"]


def closes(code, days=20):
    """최근 일봉 종가를 오래된 것부터. 이동평균 같은 판단에 씁니다."""
    out = _call(
        "/krstock/quote/v1/period",
        {
            "iem_cd": code,
            "market_cd": "KRX",
            "gubun": "1",
            "array_cnt": str(days),
            "maxavg": "5",
            "today_cls_code": "0",
        },
        live_read=True,
    )
    rows = out.get("Output_1") or []
    values = [(str(r.get("bsop_date")), int(float(r.get("stck_prpr") or 0))) for r in rows]
    values = [(d, p) for d, p in values if d and p > 0]
    values.sort()  # NH는 최신순으로 주므로 뒤집습니다.
    return [p for _, p in values]


def cash(act):
    """주문 가능 현금."""
    out = _call(
        "/krstock/inquiry/v1/balance",
        {
            "act_no": act,
            "bnc_bse_cd": "5",
            "ltg_aot_dit_cd": "9",
            "aet_bse": "2",
            "qut_dit_cd": "UNT",
        },
    ).get("Output_0") or {}
    return int(float(out.get("dca") or 0))


def holdings(act):
    """보유 종목. {종목코드: {수량, 매입가, 현재가, 수익률}}

    NH는 당일 미결제 매수의 평가금액을 0으로 보고합니다. 그것을 '판 것'으로 읽으면
    방금 산 종목이 사라져 손절이 동작하지 않으므로, 수량 필드 중 가장 큰 값을 씁니다.
    """
    rows = (
        _call(
            "/krstock/inquiry/v1/balance",
            {
                "act_no": act,
                "bnc_bse_cd": "5",
                "ltg_aot_dit_cd": "9",
                "aet_bse": "2",
                "qut_dit_cd": "UNT",
            },
        ).get("Output_1")
        or []
    )
    result = {}
    for row in rows:
        code = str(row.get("iem_cd") or "").strip()
        qty = max(
            int(float(row.get("itg_bnc_qty") or 0)),
            int(float(row.get("rsdl_qty") or 0)),
            int(float(row.get("ny_stl_qty") or 0)),
        )
        if not code or qty <= 0:
            continue
        result[code] = {
            "name": str(row.get("iem_nm") or code).strip().lstrip("*#").strip(),
            "qty": qty,
            "avg": int(float(row.get("phs_pr") or 0)),
            "price": int(float(row.get("now_pr") or 0)),
            "pnl_pct": float(row.get("pft_rt") or 0),
        }
    return result


def sellable(act, code):
    """실제로 팔 수 있는 수량. 당일 매수분은 결제 전이라 0일 수 있습니다."""
    out = _call(
        "/krstock/inquiry/v1/sellableQuantity",
        {"act_no": act, "iem_cd": code, "cfd_lon_cd": "00"},
    ).get("Output_0") or {}
    return int(float(out.get("sll_pbl_qty") or 0))


def buyable(act, code, limit_price):
    """지정가 기준 매수 가능 수량."""
    out = _call(
        "/krstock/inquiry/v1/buyableQuantity",
        {
            "ost_dit_cd": "1",
            "act_no": act,
            "iem_cd": code,
            "nmn_pr_tp_cd": "01",
            "orr_pr": limit_price,
        },
    ).get("Output_0") or {}
    return int(float(out.get("csh_orr_pbl_qty") or 0))


def order(act, side, code, qty, limit_price):
    """지정가 매수·매도. 시장가는 쓰지 않습니다.

    지정가만 쓰면 화면에서 본 가격보다 불리하게 체결되지 않습니다.
    """
    path = "/krstock/order/v1/cashBuy" if side == "buy" else "/krstock/order/v1/cashSell"
    out = _call(
        path,
        {
            "act_no": act,
            "iem_cd": code,
            "orr_qty": int(qty),
            "nmn_pr_tp_cd": "01",
            "orr_pr": int(limit_price),
            "orr_cnd_dit_cd": "00",
            "ssl_nmn_pr_dit_cd": "00",
            "rmt_mkt_cd": "KRX",
            "sor_mkt_sli_yn": "N",
        },
    ).get("Output_0") or {}
    return out.get("mkt_orr_no")


# ── 미국장 ────────────────────────────────────────────────────────────
# 국내와 API가 완전히 달라서(gbstock) 함수를 따로 둡니다. 필드 이름도 다릅니다.

US_NATION = "200"  # 미국
NEW_YORK = ZoneInfo("America/New_York")
SEOUL = ZoneInfo("Asia/Seoul")


def us_session(now=None):
    """지금 미국장이 어느 구간인가. pre / regular / after / closed

    뉴욕 현지시각 기준입니다. 서머타임은 zoneinfo가 알아서 처리합니다.
    """
    local = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(NEW_YORK)
    if local.weekday() >= 5 or local.date() in us_holidays(local.year):
        return "closed"
    clock = local.time()
    if datetime.time(9, 30) <= clock < datetime.time(16, 0):
        return "regular"
    if datetime.time(4, 0) <= clock < datetime.time(9, 30):
        return "pre"
    if datetime.time(16, 0) <= clock < datetime.time(20, 0):
        return "after"
    return "closed"


def us_order_type(session):
    """구간마다 받는 주문유형 코드가 다릅니다. 연장 세션은 지정가만 받습니다."""
    return {"pre": "61", "after": "62"}.get(session, "00")


def us_holidays(year):
    """미국 거래소 정규 휴장일.

    고정 날짜만으로는 부족합니다. 마틴 루터 킹 데이처럼 '몇째 주 월요일'인 날과,
    7월 4일이 토요일이면 전날 쉬는 대체휴일을 빼먹으면 휴장일에 주문을 넣습니다.
    """

    def nth_monday(month, nth, weekday=0):
        first = datetime.date(year, month, 1)
        return first + datetime.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (nth - 1))

    def observed(day):
        # 토요일이면 전날 금요일, 일요일이면 다음날 월요일에 쉽니다.
        return day - datetime.timedelta(days=1) if day.weekday() == 5 else (
            day + datetime.timedelta(days=1) if day.weekday() == 6 else day
        )

    # 부활절(성금요일 계산용) — Anonymous Gregorian 알고리즘
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    f, g = (b + 8) // 25, 0
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month, day = divmod(h + m - 7 * n + 114, 31)
    easter = datetime.date(year, month, day + 1)

    # 다음 해 1월 1일이 토요일이면 올해 12월 31일이 대체휴일입니다. 올해 날짜만
    # 계산하면 그 금요일에 미국장이 열렸다고 잘못 판단합니다. Juneteenth는
    # 거래소가 휴장일로 적용하기 시작한 2022년부터 넣습니다.
    fixed = [
        datetime.date(year, 1, 1),
        datetime.date(year, 7, 4),
        datetime.date(year, 12, 25),
        datetime.date(year + 1, 1, 1),
    ]
    if year >= 2022:
        fixed.append(datetime.date(year, 6, 19))
    days = {day for holiday in fixed if (day := observed(holiday)).year == year}
    days |= {nth_monday(1, 3), nth_monday(2, 3), nth_monday(9, 1)}
    days |= {nth_monday(11, 4, weekday=3)}  # 추수감사절(넷째 목요일)
    days |= {easter - datetime.timedelta(days=2)}  # 성금요일
    last_may = datetime.date(year, 5, 31)
    days |= {last_may - datetime.timedelta(days=last_may.weekday())}  # 메모리얼 데이
    return days


def us_quote(ticker):
    """미국 시세 한 번에. 52주 고저와 PER은 응답에 없어 다른 데서 채웁니다."""
    out = _call("/gbstock/quote/v1/current", {"iem_cd": ticker}, live_read=True).get("Output_0") or {}
    value = float(out.get("trdprc") or 0)
    if value <= 0:
        raise RuntimeError(f"{ticker} 현재가를 받지 못했습니다.")

    def number(key):
        try:
            return float(out.get(key) or 0) or None
        except (TypeError, ValueError):
            return None

    return {
        "price": round(value, 2),
        "name": str(out.get("kor_name") or out.get("iem_nm") or ticker).strip() or ticker,
        "change_pct": number("pctchng") or 0.0,
        "turnover": int(number("turnover") or 0),
        "high_52w": number("w52high_prc"),
        "low_52w": number("w52low_prc"),
        "per": number("per_prc"),
        "industry": str(out.get("industry_name") or "").strip() or None,
    }


def us_price(ticker):
    return us_quote(ticker)["price"]


def us_name(ticker):
    return us_quote(ticker)["name"]


def us_bars(ticker, days=20):
    """최근 일봉을 오래된 것부터. [{"date","open","high","low","close"}, …]

    종가만으로는 그날 익절선이나 손절선에 닿았는지 알 수 없습니다. 고가·저가가 있어야
    되돌아보기(review.py)가 "그날 팔렸을 것"을 판정할 수 있습니다.
    """
    today = datetime.datetime.now(NEW_YORK).strftime("%Y%m%d")
    out = _call(
        "/gbstock/quote/v1/period",
        {
            "iem_cd": ticker,
            "end_dt": today,
            "count": str(days),
            "maxavg": "5",
            "gubun": "3",
            "xtick": "0001",
            "today_cls": "1",
            "market_cls": "1",
        },
        live_read=True,
    )
    bars = []
    for row in out.get("Output_1") or []:
        day = str(row.get("trade_date") or row.get("bsop_date") or "")
        close = float(row.get("close_prc") or 0)
        if not day or close <= 0:
            continue
        bars.append({
            "date": day,
            "open": round(float(row.get("open_prc") or close), 2),
            "high": round(float(row.get("high") or close), 2),
            "low": round(float(row.get("low") or close), 2),
            "close": round(close, 2),
        })
    bars.sort(key=lambda b: b["date"])
    return bars


def us_closes(ticker, days=20):
    """최근 일봉 종가를 오래된 것부터."""
    return [bar["close"] for bar in us_bars(ticker, days)]


def us_holdings(act):
    """미국 보유 종목. 잔고는 iem_cd에 티커가 들어옵니다(국내와 다름)."""
    rows = (
        _call(
            "/gbstock/inquiry/v1/balance",
            {
                "act_no": act,
                "qut_iqr_dit_cd": "9",
                "fc_sec_trd_nat_cd": US_NATION,
                "cur_cd": "USD",
            },
        ).get("Output_1")
        or []
    )
    result = {}
    for row in rows:
        ticker = str(row.get("tck_iem_cd") or row.get("iem_cd") or "").strip()
        qty = int(float(row.get("cns_bse_bnc_qty") or 0))
        if not ticker or qty <= 0:
            continue
        result[ticker] = {
            "name": str(row.get("iem_nm") or ticker).strip(),
            "qty": qty,
            "avg": round(float(row.get("fc_phs_uit_pr") or 0), 2),
            "price": round(float(row.get("fc_sec_end_pr") or 0), 2),
            "pnl_pct": float(row.get("eal_pft_rt") or 0),
            "krw": int(float(row.get("krw_eal_amt") or 0)),
        }
    return result


def _us_orderable(act, ticker, price, order_type, side):
    payload = {
        "act_no": act,
        "pcs_dit": "2" if side == "buy" else "3",
        "fc_sec_trd_nat_cd": US_NATION,
        "iem_cd": ticker,
        # 모의계좌는 달러 증거금만, 실계좌는 원화 증거금을 씁니다.
        "wtm_cur_knd_cd": "1" if MOCK else "2",
        "oss_orr_knd_cd": "1",
        "ahi_nmn_pr_tp_cd": order_type,
        "fc_orr_uit_pr": price,
    }
    return _call("/gbstock/inquiry/v1/buyableAmount", payload).get("Output_0") or {}


def us_buyable(act, ticker, price, order_type):
    return int(float(_us_orderable(act, ticker, price, order_type, "buy").get("byn_pbl_qty") or 0))


def us_sellable(act, ticker, price, order_type):
    return int(float(_us_orderable(act, ticker, price, order_type, "sell").get("sll_pbl_qty") or 0))


def us_open_sells(act):
    """아직 안 채워진 미국 매도 주문. {티커: [{주문번호, 남은수량, 단가}, …]}

    익절을 미리 걸어 두면 그 수량은 묶입니다. 손절이 나야 할 때 걸린 주문을 먼저
    취소하지 않으면 "팔 수 있는 수량 0주"가 되어 손절이 조용히 실패합니다.

    주문일자는 NH가 어느 날짜로 적는지(한국 날짜인지 뉴욕 날짜인지) 확실치 않은데,
    미국 정규장은 한국 날짜로 이틀에 걸칩니다. 그래서 오늘과 어제를 둘 다 봅니다.
    """
    result = {}
    for day in _us_days():
        try:
            rows = _call(
                "/gbstock/inquiry/v1/unexecuted",
                {
                    "orr_dt": day,
                    "act_no": act,
                    "oss_sby_dit_cd": "1",  # 매도만
                    "sot_dit": "1",
                    "ost_cns_dit": "2",  # 미체결만
                },
            ).get("Output_0") or []
        except Exception as exc:
            # 그날 주문이 하나도 없으면 NH가 "데이터가 존재하지 않습니다"로 답합니다.
            # 그것은 오류가 아니라 "없음"입니다. 오류로 읽으면 익절 예약이 영영
            # 걸리지 않습니다. 나머지 오류는 그대로 올립니다.
            if getattr(exc, "code", "") != "11512":
                raise
            continue
        for row in rows:
            ticker = str(row.get("iem_cd") or "").strip()
            left = int(float(row.get("ny_cns_orr_qty") or 0))
            order_no = str(row.get("orr_no") or "").strip()
            if not ticker or not order_no or left <= 0:
                continue
            result.setdefault(ticker, []).append({
                "orr_no": order_no,
                "qty": left,
                "price": round(float(row.get("fc_orr_uit_pr") or 0), 2),
            })
    return result


def _us_days():
    """예약주문을 찾을 날짜들. 미국 정규장은 한국 날짜로 이틀에 걸칩니다."""
    seoul = datetime.datetime.now(SEOUL)
    return sorted({
        seoul.strftime("%Y%m%d"),
        (seoul - datetime.timedelta(days=1)).strftime("%Y%m%d"),
        datetime.datetime.now(NEW_YORK).strftime("%Y%m%d"),
    })


def us_reserved_stops(act):
    """살아 있는 STOP 손절 예약. {티커: [{주문일자, 접수번호, 수량, 기준가}, …]}

    손절은 지정가로 미리 걸 수 없습니다(지금 값 아래에 걸면 즉시 팔립니다).
    NH는 그것을 **예약주문**으로 받습니다. 값이 닿으면 그때 시장가로 나갑니다.
    """
    result = {}
    for day in _us_days():
        try:
            rows = _call(
                "/gbstock/inquiry/v1/reservedInquiry",
                {
                    "fc_mkt_dit_cd": US_NATION,
                    "bkg_orr_dt": day,
                    "act_no": act,
                    "sby_dit_cd": "1",  # 매도만
                    "bkg_orr_can_yn": "1",  # 접수된 것만 (취소·완료 제외)
                    "oss_orr_knd_cd": "0",
                    "bkg_orr_tp_cd": "0",
                    "wtm_cur_knd_cd": "0",
                },
            ).get("Output_0") or []
        except Exception as exc:
            if getattr(exc, "code", "") != "11512":  # 그날 예약이 없음
                raise
            continue
        for row in rows:
            ticker = str(row.get("iem_cd") or "").strip()
            if not ticker or str(row.get("orr_pdt_dit_cd") or "").strip() != "03":
                continue
            result.setdefault(ticker, []).append({
                "day": day,
                "no": str(row.get("bkg_rtn_orr_no") or "").strip(),
                "qty": int(float(row.get("orr_qty") or 0)),
                "stop": round(float(row.get("fc_stop_orr_bse_pr") or 0), 2),
            })
    return result


def us_reserve_stop(act, ticker, qty, stop_price):
    """STOP(시장가) 손절을 예약합니다. 오늘 하루짜리로 겁니다.

    며칠짜리로 걸면 나중에 어느 날짜로 등록했는지 알아야 찾을 수 있습니다. 하루짜리면
    오늘만 보면 되고, 회차가 15분마다 도니 매일 첫 회차가 알아서 다시 겁니다.
    """
    day = datetime.datetime.now(SEOUL).strftime("%Y%m%d")
    return (
        _call(
            "/gbstock/order/v1/reservedSubmit",
            {
                "act_no": act,
                "fc_sec_trd_nat_cd": US_NATION,
                "iem_cd": ticker,
                "oss_sby_dit_cd": "1",  # 매도
                "orr_qty": int(qty),
                "nmn_pr_tp_cd": "15",  # STOP(시장가)
                "fc_stop_orr_bse_pr": round(float(stop_price), 2),
                "orr_pdt_dit_cd": "03",  # 미국Stop예약주문
                "bkg_orr_tp_cd": "1",  # 일반예약
                "bkg_orr_sta_dt": day,
                "bkg_orr_end_dt": day,
            },
        ).get("Output_0")
        or {}
    ).get("bkg_rtn_orr_no")


def us_reserved_cancel(act, ticker, day, reserved_no):
    """걸어 둔 STOP 예약을 취소합니다."""
    return _call(
        "/gbstock/order/v1/reservedCancel",
        {
            "act_no": act,
            "fc_mkt_dit_cd": US_NATION,
            "bkg_orr_dt": day,
            "bkg_rtn_orr_no": reserved_no,
            "iem_cd": ticker,
            "orr_pdt_dit_cd": "03",
        },
    )


def us_cancel(act, ticker, order_no):
    """걸어 둔 미국 주문을 통째로 취소합니다."""
    return (
        _call(
            "/gbstock/order/v1/cancel",
            {
                "act_no": act,
                "org_orr_no": order_no,
                "fc_sec_trd_nat_cd": US_NATION,
                "iem_cd": ticker,
                "all_pat_dit_cd": "1",  # 전체 취소
            },
        ).get("Output_0")
        or {}
    ).get("orr_no")


def us_order(act, side, ticker, qty, price, order_type):
    """미국 지정가 주문. 매도에는 증거금 통화 항목이 없습니다(공식 스펙)."""
    payload = {
        "act_no": act,
        "fc_sec_trd_nat_cd": US_NATION,
        "iem_cd": ticker,
        "orr_qty": int(qty),
        "ahi_nmn_pr_tp_cd": order_type,
        "fc_orr_uit_pr": round(float(price), 2),
    }
    if side == "buy":
        payload["wtm_cur_knd_cd"] = "1" if MOCK else "2"
    path = "/gbstock/order/v1/buy" if side == "buy" else "/gbstock/order/v1/sell"
    return (_call(path, payload).get("Output_0") or {}).get("orr_no")
