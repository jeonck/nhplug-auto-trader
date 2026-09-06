"""하루를 되돌아봅니다. **아무것도 주문하지 않고, 전략도 고치지 않습니다.**

  python review.py              오늘 한 일 + 백테스트를 JSON으로
  python review.py --days 120   백테스트 기간만 바꿔서

두 가지를 냅니다.

  오늘      회차들이 무엇을 왜 했는지, 그래서 지금 어떤지 (`.cache/board.json` 을 읽습니다)
  백테스트   **지금 규칙**을 과거 일봉에 그대로 돌려 본 결과

━━ 백테스트가 무엇을 재고 무엇을 못 재는지 ━━━━━━━━━━━━━━━━━━━━━━━━━━━

숫자를 믿기 전에 이것부터 알아야 합니다.

  ○ 잴 수 있는 것 — 사는 조건(5일·20일 평균 돌파 · MACD · RSI)과 나가는 조건
    (익절 +TAKE_PROFIT_PCT% · 손절 STOP_LOSS_PCT%). 지금은 이 둘 다 **규칙**이라
    코드가 그대로 재현합니다. 나가는 값은 증권사에 미리 걸어 두므로 실제와 같습니다.

  ✗ 못 재는 것 — **클로드 코드의 판단과 뉴스.** 실제로는 규칙을 통과한 종목 중에서
    클로드 코드가 다시 고릅니다. 그래서 여기 나오는 매수는 실제보다 **많습니다.**
    이 결과는 "규칙만으로 갔다면" 이고, 성적의 **위쪽 한계가 아니라 다른 전략**입니다.

  ✗ 하루 안의 순서 — 일봉에는 고가·저가만 있고 어느 쪽이 먼저였는지가 없습니다.
    같은 날 익절선과 손절선에 **둘 다** 닿았으면 **손절이 먼저**였다고 봅니다.
    실제보다 나쁘게 잡는 쪽입니다. 좋게 보이려고 유리한 쪽을 고르지 않습니다.

  ✗ 수수료·세금·환율·미끄러짐. 해외주식 수수료만 왕복 약 0.18%입니다. 익절이 +3%면
    그중 6분의 1이 수수료로 나갑니다. 아래 숫자에는 그것이 빠져 있습니다.

**그래서 이 결과로 전략을 자동으로 고치지 않습니다.** 사람에게 보여 주고 묻습니다.
"""

import argparse
import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import broker
import strategy

SEOUL = ZoneInfo("Asia/Seoul")
NEW_YORK = ZoneInfo("America/New_York")
BOARD = Path(__file__).with_name(".cache") / "board.json"
REVIEWS = Path(__file__).with_name(".cache") / "reviews"

# MACD(12·26·9)를 내려면 최소 35봉이 필요합니다. 그 전 날짜는 매매하지 않습니다.
WARMUP = 35


# ── 오늘 한 일 ────────────────────────────────────────────────────────
def today(now=None):
    """오늘 회차들이 무엇을 했는가. board.json 만 읽습니다(조회 없음)."""
    now = now or datetime.datetime.now(SEOUL)
    if not BOARD.exists():
        return {"날짜": now.strftime("%Y-%m-%d"), "회차수": 0, "메모": "아직 돈 회차가 없습니다"}

    saved = json.loads(BOARD.read_text(encoding="utf-8"))
    stamp = now.strftime("%m-%d")
    # 미국장은 한국 날짜로 이틀에 걸칩니다. 어제 밤부터가 오늘 한 장입니다.
    before = (now - datetime.timedelta(days=1)).strftime("%m-%d")
    rounds = [
        r for r in (saved.get("회차") or [])
        if str(r.get("시각", "")).startswith((stamp, before)) and not r.get("전환")
    ]

    acted, held_still = [], 0
    for entry in rounds:
        for item in entry.get("처리함") or []:
            kind = item.get("구분")
            if kind in ("매수", "매도", "예약"):
                acted.append({
                    "시각": entry.get("시각"),
                    "구분": kind,
                    "종목": item.get("종목"),
                    "한 일": item.get("한 일"),
                    "이유": item.get("이유", ""),
                    "뉴스": item.get("뉴스", ""),
                })
            elif kind == "안 함":
                held_still += 1

    return {
        "날짜": now.strftime("%Y-%m-%d"),
        "계좌": saved.get("계좌"),
        "회차수": len(rounds),
        "주문": acted,
        "막힌 것": held_still,
        "지금": saved.get("지금", {}),
        "한도": saved.get("한도", {}),
        "문제": saved.get("문제", ""),
    }


# ── 백테스트 ──────────────────────────────────────────────────────────
def rules_say_buy(closes, price):
    """지금 규칙이 이 종목을 살 만하다고 보는가. strategy.why_not_buy 를 그대로 씁니다.

    거래대금과 52주는 여기서 못 재므로 통과시킵니다. 우리가 보는 종목은 전부
    거래가 많고, 52주 조건은 실제 운영에서 따로 걸립니다.
    """
    m = {
        "currency": "USD",
        "price": price,
        "closes": closes,
        "turnover": float("inf"),
        "high_52w": None,
    }
    return strategy.why_not_buy(m) is None


def simulate(bars, take_pct, stop_pcts, base_stop, budgets, base_budget, most):
    """규칙대로 사고팔았다면 어떻게 됐을지. 거래 목록을 돌려줍니다.

    하루 안의 순서를 모르므로, 같은 날 두 선에 다 닿으면 **손절이 먼저**였다고 봅니다.
    """
    days = sorted({bar["date"] for rows in bars.values() for bar in rows})
    index = {t: {bar["date"]: i for i, bar in enumerate(rows)} for t, rows in bars.items()}

    open_now, trades = {}, []
    for day in days:
        # 1) 들고 있는 것부터 정리합니다. 자리를 비워야 새로 삽니다.
        for ticker in list(open_now):
            i = index[ticker].get(day)
            if i is None:
                continue
            bar, pos = bars[ticker][i], open_now[ticker]
            stop = pos["avg"] * (1 + stop_pcts.get(ticker, base_stop) / 100)
            target = pos["avg"] * (1 + take_pct / 100)
            out = stop if bar["low"] <= stop else (target if bar["high"] >= target else None)
            if out is None:
                continue
            trades.append({
                "종목": ticker, "산 날": pos["day"], "판 날": day,
                "산 값": round(pos["avg"], 2), "판 값": round(out, 2),
                "수량": pos["qty"],
                "손익": round((out - pos["avg"]) * pos["qty"], 2),
                "수익률": round((out / pos["avg"] - 1) * 100, 2),
                "이유": "손절" if out < pos["avg"] else "익절",
            })
            del open_now[ticker]

        # 2) 빈 자리가 있으면 규칙에 맞는 것을 삽니다.
        for ticker, rows in bars.items():
            if len(open_now) >= most or ticker in open_now:
                continue
            i = index[ticker].get(day)
            if i is None or i < WARMUP:
                continue
            closes = [b["close"] for b in rows[: i + 1]]
            price = rows[i]["close"]
            if not rules_say_buy(closes, price):
                continue
            qty = int(budgets.get(ticker, base_budget) // price)
            if qty < 1:
                continue
            open_now[ticker] = {"day": day, "avg": price, "qty": qty}

    # 아직 들고 있는 것은 마지막 값으로 평가만 합니다(판 것으로 세지 않습니다).
    holding = [
        {
            "종목": t, "산 날": pos["day"], "산 값": round(pos["avg"], 2),
            "지금 값": bars[t][-1]["close"], "수량": pos["qty"],
            "평가손익": round((bars[t][-1]["close"] - pos["avg"]) * pos["qty"], 2),
        }
        for t, pos in open_now.items()
    ]
    return trades, holding


def score(trades):
    """거래 목록을 사람이 읽을 숫자로."""
    if not trades:
        return {"거래수": 0, "메모": "조건에 맞는 거래가 한 번도 없었습니다"}
    wins = [t for t in trades if t["손익"] > 0]
    losses = [t for t in trades if t["손익"] <= 0]

    worst_streak = streak = 0
    for t in trades:
        streak = streak + 1 if t["손익"] <= 0 else 0
        worst_streak = max(worst_streak, streak)

    def days_between(a, b):
        fmt = "%Y%m%d"
        return (datetime.datetime.strptime(b, fmt) - datetime.datetime.strptime(a, fmt)).days

    return {
        "거래수": len(trades),
        "이긴 횟수": len(wins),
        "진 횟수": len(losses),
        "승률": f"{len(wins) / len(trades) * 100:.1f}%",
        "총손익": f"${sum(t['손익'] for t in trades):,.2f}",
        "이겼을 때 평균": f"{sum(t['수익률'] for t in wins) / len(wins):+.2f}%" if wins else "-",
        "졌을 때 평균": f"{sum(t['수익률'] for t in losses) / len(losses):+.2f}%" if losses else "-",
        "가장 나빴던 거래": f"{min(t['수익률'] for t in trades):+.2f}%",
        "연속으로 진 최대 횟수": worst_streak,
        "평균 보유일": round(sum(days_between(t["산 날"], t["판 날"]) for t in trades) / len(trades), 1),
    }


def backtest(days=250, sweep=True):
    """지금 설정으로 한 번, 그리고 익절·손절선을 바꿔 가며 비교."""
    symbols = list(getattr(strategy, "US_SYMBOLS", []))
    if not symbols:
        return {"메모": "미국 종목이 없어 백테스트할 것이 없습니다"}

    bars = {}
    for ticker in symbols:
        rows = broker.us_bars(ticker, days)
        if len(rows) > WARMUP:
            bars[ticker] = rows
    if not bars:
        return {"메모": "일봉을 충분히 받지 못했습니다"}

    take = getattr(strategy, "TAKE_PROFIT_PCT", 0)
    base_stop = getattr(strategy, "STOP_LOSS_PCT", 0)
    stop_pcts = dict(getattr(strategy, "STOP_LOSS_PCTS", {}))
    budgets = dict(getattr(strategy, "US_BUY_AMOUNTS", {}))
    base_budget = getattr(strategy, "US_BUY_AMOUNT", 0)
    most = getattr(strategy, "MAX_HOLDINGS", 1)

    trades, holding = simulate(bars, take, stop_pcts, base_stop, budgets, base_budget, most)
    out = {
        "기간": f"{min(r[0]['date'] for r in bars.values())} ~ {max(r[-1]['date'] for r in bars.values())}",
        "종목": sorted(bars),
        "지금 설정": {"익절": f"+{take}%", "손절": f"{base_stop}%", "종목별 손절": stop_pcts or "없음"},
        "성적": score(trades),
        "아직 들고 있는 것": holding,
        "거래 내역": trades,
    }

    if sweep:
        # 같은 일봉을 다시 쓰므로 조회가 늘지 않습니다.
        table = []
        for t_pct in (2.0, 3.0, 5.0, 8.0, 12.0):
            for s_pct in (-8.0, -10.0, -15.0, -20.0, -30.0):
                # 종목별 손절선도 같은 비율로 함께 움직입니다(SOXL은 늘 두 배로 넓게).
                scaled = {k: v / base_stop * s_pct for k, v in stop_pcts.items()} if base_stop else {}
                got, _ = simulate(bars, t_pct, scaled, s_pct, budgets, base_budget, most)
                if got:
                    table.append({
                        "익절": f"+{t_pct}%", "손절": f"{s_pct}%",
                        "거래수": len(got),
                        "승률": f"{len([x for x in got if x['손익'] > 0]) / len(got) * 100:.1f}%",
                        "총손익": round(sum(x["손익"] for x in got), 2),
                    })
        table.sort(key=lambda r: r["총손익"], reverse=True)
        out["다르게 했다면"] = table[:8]
        out["주의"] = (
            "이 표에서 제일 좋은 값을 그대로 가져다 쓰면 지나간 값에만 맞춘 전략이 됩니다. "
            "과거에 잘 맞았다는 것과 앞으로 잘 맞는다는 것은 다릅니다. 수수료·세금·"
            "미끄러짐도 빠져 있습니다. 차이가 크고 이유를 말로 설명할 수 있을 때만 바꾸세요."
        )
    return out


def main():
    parser = argparse.ArgumentParser(description="하루 되돌아보기. 주문하지 않습니다.")
    parser.add_argument("--days", type=int, default=250, help="백테스트에 쓸 일봉 개수")
    parser.add_argument("--no-sweep", action="store_true", help="익절·손절선 비교표를 빼고")
    args = parser.parse_args()

    result = {"오늘": today(), "백테스트": backtest(args.days, sweep=not args.no_sweep)}

    # 날마다 남겨 두어야 어제와 비교할 수 있습니다.
    REVIEWS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(SEOUL).strftime("%Y%m%d")
    (REVIEWS / f"{stamp}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
