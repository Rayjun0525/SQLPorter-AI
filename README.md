# SQLPorter-AI
SQL Porting AI tool



sqlporter_ai/
├── sqlporter.yaml                  # ✅ 사용자 설정 파일 (루트에 위치)
├── main.py                         # ✅ 실행 진입점
│
├── config/                         # 설정 로딩 관련 유틸
│   ├── __init__.py
│   ├── loader.py                   # 설정 YAML을 읽고 파싱
│
├── agents/                         # fast-agent 기반 에이전트 모듈
│   ├── __init__.py
│   ├── converters.py               # converter_1 ~ converter_3
│   ├── merge.py                    # 병합 agent
│   ├── evaluator.py                # 평가 agent
│   └── pipeline.py                 # 평가 루프 (evaluator_optimizer)
│
├── core/                           # 실행 로직과 기능 유틸
│   ├── __init__.py
│   ├── runner.py                   # 전체 워크플로우 수행
│   ├── file_io.py                  # 파일 입출력 유틸
│   └── mcp_utils.py                # (선택) MCP 상태전달 등
│
├── ASIS/                           # Oracle SQL 원본 저장
│   └── .gitkeep                    # 빈 폴더 유지용
├── TOBE/                           # 변환된 PostgreSQL SQL 결과
│   └── .gitkeep
├── reports/                        # 성공/실패/리포트 저장
│   └── .gitkeep
│
├── requirements.txt               # Python dependency 목록
└── README.md
