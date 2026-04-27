@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    후원금 및 지출 대시보드 (Windows)
echo ==========================================

:: 1. 파이썬 설치 여부 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [오류] 파이썬이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo https://www.python.org/ 에서 파이썬을 설치해 주세요.
    pause
    exit /b
)

:: 2. 가상 환경 설정
if not exist "venv_win" (
    echo 가상 환경을 생성합니다 (venv_win)...
    python -m venv venv_win
)

:: 3. 가상 환경 활성화 및 의존성 설치
call venv_win\Scripts\activate
echo 필요한 라이브러리를 설치/업데이트합니다...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. 대시보드 실행
echo 대시보드를 실행합니다. 잠시만 기다려 주세요...
streamlit run app.py

pause
