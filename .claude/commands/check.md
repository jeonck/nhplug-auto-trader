---
description: 프로젝트 검사와 전략 검사를 돌립니다
allowed-tools: Bash(python -m unittest:*), Bash(.venv/bin/python -m unittest:*), Bash(python check.py:*), Bash(.venv/bin/python check.py:*)
---

두 가지를 돌리고 결과만 쉬운 말로 알려 주세요.

1. `python -m unittest discover -s tests` — 프로그램 자체가 멀쩡한지
2. `python check.py` — 지금 전략이 장중에 안 터지는지

둘 다 통과하면 "이상 없습니다" 한 줄이면 됩니다. 로그를 통째로 붙여넣지 마세요.

**하나라도 실패하면 거기서 멈추고** 무엇이 왜 실패했는지 한국어로 설명한 뒤,
고칠지 사용자에게 물어보세요. 통과 못 한 전략은 그대로 두지 않습니다.
