---
description: 현황 화면(board.py)을 띄우고 주소만 알려 줍니다
allowed-tools: Bash(pgrep:*), Bash(nohup .venv/bin/python board.py:*), Bash(tail:*), Bash(sleep:*)
---

지금 들고 있는 종목과 손익을 볼 수 있는 현황 화면을 사용자에게 띄워 주세요.

1. `pgrep -f board.py` 로 이미 떠 있는지 봅니다. 떠 있으면 새로 띄우지 않습니다.
2. 없으면 띄웁니다. `.venv` 가 없으면 `python` 을 씁니다.
   `nohup .venv/bin/python board.py > board.log 2>&1 &`
3. `board.log` 에서 `FORWARD_PORT=숫자` 를 읽습니다.
   - 이 컴퓨터에서 도는 중이면 `http://127.0.0.1:그포트`
   - 원격 서버면 포트 전달(웹 미리보기)로 열어서 나온 주소
4. 사용자에게는 **주소 한 줄**만 줍니다. 터미널 명령이나 ssh 줄은 보여주지 마세요.

보기만 하는 화면입니다. 끄지 말고 그대로 두세요. 숫자를 메시지에 옮겨 적지 말고,
사용자가 물어볼 때만 말해 주세요.
