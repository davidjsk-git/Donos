import json
import os
import pandas as pd
from datetime import datetime

# 테스트용 데이터 경로 설정
DATA_DIR = "data"
CRM_FILE = os.path.join(DATA_DIR, "crm_master.json")
HOPE_DATA = os.path.join(DATA_DIR, "HOPE_data.csv")
GLFOCUS_DATA = os.path.join(DATA_DIR, "GLFocus_data.csv")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def run_test():
    print("--- 👤 CRM 기능 종합 테스트 시작 ---")
    
    # 1. 가상의 후원 데이터 생성 (HOPE, GLFocus 양쪽에 있는 후원자 '홍길동')
    hope_data = {
        "날짜": ["2026-01-10", "2026-02-10"],
        "계정과목": ["일반후원", "일반후원"],
        "ㅎ원자명": ["홍길동", "이몽룡"],
        "전표제목": ["1월분", "2월분"],
        "적요": ["정기", "정기"],
        "지출 OR 차변": [0, 0],
        "수입 OR 대변": [100000, 50000]
    }
    glfocus_data = {
        "날짜": ["2026-03-15"],
        "계정과목": ["특별후원"],
        "ㅎ원자명": ["홍길동"],
        "전표제목": ["창립기념"],
        "적요": ["일시"],
        "지출 OR 차변": [0],
        "수입 OR 대변": [200000]
    }
    
    pd.DataFrame(hope_data).to_csv(HOPE_DATA, index=False)
    pd.DataFrame(glfocus_data).to_csv(GLFOCUS_DATA, index=False)
    print("✅ 테스트용 단체별 데이터 생성 완료")

    # 2. CRM 마스터 데이터 생성 (태그 및 메모 저장 테스트)
    test_crm = {
        "홍길동": {
            "tags": ["VIP", "정기"],
            "memo": "오랫동안 후원해주신 핵심 후원자님입니다."
        }
    }
    with open(CRM_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_crm, f, ensure_ascii=False, indent=4)
    print("✅ CRM 마스터 데이터(태그/메모) 저장 완료")

    # 3. 데이터 로드 및 통합 검증 (프로필 조회 로직)
    df_hope = pd.read_csv(HOPE_DATA)
    df_gl = pd.read_csv(GLFOCUS_DATA)
    full_df = pd.concat([df_hope, df_gl])
    
    donor_name = "홍길동"
    donor_df = full_df[full_df['ㅎ원자명'] == donor_name]
    total_donation = donor_df['수입 OR 대변'].sum()
    
    print(f"\n--- 후원자 '{donor_name}' 프로필 검증 ---")
    print(f"통합 누적 후원액: {total_donation:,.0f}원 (기대값: 300,000원)")
    if total_donation == 300000:
        print("✅ 두 단체 데이터 통합 합산 성공")
    else:
        print("❌ 데이터 통합 합산 오류")

    # 4. 태그 필터링 검증
    with open(CRM_FILE, 'r', encoding='utf-8') as f:
        loaded_crm = json.load(f)
    
    target_tag = "VIP"
    found_donors = [name for name, info in loaded_crm.items() if target_tag in info.get("tags", [])]
    
    print(f"\n--- 태그 '{target_tag}' 필터링 검증 ---")
    print(f"검색된 후원자: {found_donors}")
    if donor_name in found_donors:
        print(f"✅ 태그 기반 필터링 성공")
    else:
        print(f"❌ 태그 필터링 오류")

    # 5. 메모 로드 검증
    memo_content = loaded_crm[donor_name].get("memo", "")
    print(f"\n--- 메모 로드 검증 ---")
    print(f"저장된 메모: {memo_content}")
    if "핵심 후원자" in memo_content:
        print("✅ 메모 저장 및 로드 성공")
    else:
        print("❌ 메모 로드 오류")

    print("\n--- 👤 CRM 기능 종합 테스트 완료 ---")

if __name__ == "__main__":
    run_test()
