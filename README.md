# bory

## 개요
던담(https://dundam.xyz)의 공대원 데미지(총딜)를 한 번에 확인하기 위한 Windows 데스크톱 도우미입니다. Python 3.11과 PySimpleGUI로 작성되며, 화면 캡쳐 → OCR → 던담 HTML 스크래핑 순으로 동작합니다.

## 목표/기능 (1차)
- **화면 캡쳐 & OCR**: 현재 화면을 캡쳐하고 Tesseract 기반 OCR로 공대원 텍스트를 추출합니다.
- **데미지 조회**: 추출된 공대원 이름을 기반으로 던담 페이지의 "총딜" 값을 파싱하여 테이블에 표시합니다.
- **초기화/종료**: UI 상태를 초기화하거나 프로그램을 종료합니다.

## 실행 환경
- OS: Windows 10/11
- 언어/런타임: Python 3.11
- UI 프레임워크: PySimpleGUI
- OCR: OpenCV + Tesseract (시스템에 Tesseract OCR 실행 파일이 설치되어 있어야 합니다)
- 배포: PyInstaller로 exe 번들링(옵션)

## 폴더 구조
```
src/
  cli.py            # 엔트리포인트
  core/             # OCR/스크래퍼 등 도메인 로직
  ui/               # PySimpleGUI 기반 UI
  io/               # 캡쳐 유틸
tests/              # pytest 테스트
```

## 빠른 시작
1. **의존성 설치**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Tesseract 설치** (Windows)
   - 예: [UB Mannheim 배포판](https://github.com/UB-Mannheim/tesseract/wiki) 설치 후, 시스템 PATH에 추가

3. **애플리케이션 실행**
   ```bash
   .venv\Scripts\activate
   python -m src.cli
   ```
   - 기본 URL 템플릿: `https://dundam.xyz/character?server=hilder&key={name}` (`{name}`가 캐릭터 이름으로 치환됨)
   - "시작(캡쳐)" → OCR로 캐릭터 목록 추출 → "데미지 조회"로 총딜 조회

## 테스트
- 단위 테스트 실행:
  ```bash
  python -m pytest
  ```

## 빌드/배포 (exe 생성)
- PyInstaller 원파일 빌드 예시:
  ```bash
  pyinstaller --onefile --name bory src/cli.py
  ```
- 생성된 `dist/bory.exe` 또는 `dist/bory`를 실행합니다.

## 한계/주의사항
- 던담 HTML 구조 변경 시 총딜 파싱이 실패할 수 있습니다. (정규식/텍스트 기반 백업 파서 사용)
- OCR 품질은 화면 해상도/폰트/배경에 영향을 받습니다. 텍스트가 선명하게 보이도록 캡쳐하세요.
- 네트워크 오류나 사이트 응답 지연 시 조회가 실패할 수 있으므로 UI 로그를 확인하세요.
