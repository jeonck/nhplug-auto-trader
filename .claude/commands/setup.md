---
description: 설정 화면(setup.py)을 띄우고 주소만 알려 줍니다
allowed-tools: Bash(pgrep:*), Bash(nohup .venv/bin/python setup.py:*), Bash(tail:*), Bash(sleep:*)
argument-hint: [--live]
---

키 입력·계좌 전환을 하는 설정 화면을 띄워 주세요. 추가 인자: $ARGUMENTS

1. `pgrep -f setup.py` 로 이미 떠 있는지 봅니다.
2. 없으면 띄웁니다. `nohup .venv/bin/python setup.py $ARGUMENTS > setup.log 2>&1 &`
   - 실제 계좌로 넘어가는 중이면 `--live` 를 붙입니다. 화면이 순서를 안내합니다.
3. `setup.log` 의 `FORWARD_PORT=숫자` 로 주소를 만들어 **주소만** 줍니다.

**키는 묻지도, 대신 넣지도 마세요.** 사용자가 그 화면에서 직접 넣습니다.
`.env` 는 읽지도 고치지도 않습니다. 계좌 전환은 이 화면 1단계에서만 합니다.

사용자가 "모의투자"라고 해서 이 화면을 띄운 것이라면, 1단계에서
[모의투자 계좌]를 고르고 저장하면 된다고 한 줄로 알려 주세요.
