#!/bin/bash

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

echo "=========================================="
echo "   후원금 및 지출 대시보드 실행 중...   "
echo "=========================================="

# 가상 환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "가상 환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
echo "필요한 라이브러리를 설치/업데이트합니다..."
pip install --upgrade pip
pip install -r requirements.txt

# Streamlit 실행
echo "대시보드를 실행합니다. 잠시만 기다려 주세요..."
streamlit run app.py
