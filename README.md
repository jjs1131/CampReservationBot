# Camping Reservation Bot (Multi-Site)

24시간 서버에서 여러 캠핑장 예약 사이트를 모니터링하고, 조건에 맞으면 예약까지 시도하는 Python 봇 골격입니다.

## 핵심 기능
- 멀티 사이트 지원: 사이트별 어댑터 분리
- 공통 플로우: 로그인 -> 조회 -> 조건 매칭 -> 예약 시도
- 스케줄 실행: APScheduler 기반 주기 실행
- 알림: 텔레그램 알림(선택)
- 안전장치: dry-run, 중복 실행 방지 락

## 빠른 시작
1. 가상환경 + 설치
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .
python -m playwright install chromium
```

2. 환경변수 설정
```bash
copy .env.example .env
```

3. 타깃 설정
- `cfg/targets.example.yaml`을 복사해서 `cfg/targets.yaml` 생성
- 사이트별 `adapter`와 조건 입력

4. 실행
```bash
python -m camping_bot.main --config cfg/targets.yaml
```

## 인터파크(안성맞춤) 사용
- `adapter: interpark_anseong` 사용
- `criteria.selectors` 값은 실제 DOM에 맞게 수정 필요
- 부정예매방지 문자는 자동 우회하지 않고, 콘솔 입력으로 진행
- 캡차 처리 모드는 `.env`의 `CAPTCHA_MODE` 또는 job의 `criteria.captcha_mode`로 선택
- 기본값 `manual`, 테스트용 `fixed`(코드는 `CAPTCHA_FIXED_CODE`)

## 디렉터리
- `src/camping_bot/main.py`: 엔트리포인트
- `src/camping_bot/runner.py`: 잡 실행 오케스트레이션
- `src/camping_bot/adapters/base.py`: 어댑터 인터페이스
- `src/camping_bot/captcha.py`: 캡차 솔버 레지스트리(교체 포인트)
- `src/camping_bot/adapters/mock_adapter.py`: 테스트용 샘플 어댑터
- `src/camping_bot/adapters/interpark_anseong_adapter.py`: 인터파크 전용 어댑터

## 실제 사이트 적용 방법
1. `src/camping_bot/adapters/your_site.py` 생성
2. `SiteAdapter` 상속 후 `login/search_slots/book_slot` 구현
3. `src/camping_bot/adapters/registry.py`에 어댑터 등록
4. `cfg/targets.yaml`에서 `adapter: your_site` 사용

## 주의
- 사이트 이용약관, 자동화 정책, 캡차/2FA 정책을 반드시 준수하세요.
- 기본값은 `dry_run=true`입니다. 실예약 전 충분히 검증하세요.
