# 🕵️ 마피아 게임 AI (콘솔 기반)

GPT-4o 기반 AI 플레이어들이 참여하는 콘솔 기반 마피아 게임입니다. AI는 시민과 마피아 역할을 맡아 자연스럽게 대화하고, 추론하며, 자동으로 투표하고 살해 대상을 결정합니다.

---

## 📁 파일 구성

```
mafia_game/
├── player.py      # 게임 메인 로직
├── chat_ai.py     # GPT 기반 발언, 투표, 살해 판단
├── env_set.py     # (옵션) API 키 설정
└── README.md      # 설명 파일
```

---

## 🚀 실행 방법

```bash
python player.py
```

5명의 AI가 자동으로 게임을 진행합니다. 각자 역할을 부여받고 토론 및 투표를 통해 게임이 진행됩니다.

---

## 🤖 핵심 기능

* **conversation\_gpt**: 플레이어의 발언 생성
* **voter\_gpt**: 대화 로그를 기반으로 AI가 투표
* **murderer\_gpt**: 밤에 마피아가 살해 대상 자동 선택

모든 판단은 LangChain 기반 GPT 시스템 메시지를 통해 수행되며, 결과는 Pydantic을 사용해 JSON 형태로 파싱됩니다.

---

## 🧩 클래스 구성

* `Player`: 이름, 역할, 생존 상태, 대화 기록 보유. `speak`, `vote` 시 GPT 호출
* `Game`: 게임 흐름 전반 담당 (낮/밤, 역할 배정, 승리 체크 등)

---

## 설치 요구사항

```bash
pip install langchain-openai openai tiktoken pydantic
```

Python 3.9 이상 필요

---

## 💡 확장 아이디어

* 웹 UI 적용
* 경찰/의사 등 특수 직업 추가
* 대화 로그 기반 전략적 추론 강화

---

## 라이선스

MIT License
(OpenAI API 요금 주의)
