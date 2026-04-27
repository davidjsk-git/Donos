import pandas as pd
import os
from data_processor import parse_donation_csv

# 1. 테스트용 CSV 파일 생성 (다양한 케이스 포함: 콤마 있는 금액, 한글 등)
test_csv_path = "test_upload_sample.csv"
test_data = {
    "날짜": ["2026-04-01", "2026-04-02", "2026-04-03"],
    "계정과목": ["일반후원", "사무비", "특별후원"],
    "ㅎ원자명": ["테스터1", "알파문구", "테스터2"],
    "전표제목": ["자동이체", "비품구매", "일시후원"],
    "적요": ["4월 정기", "A4용지", "기념기부"],
    "지출 OR 차변": ["0", "15,500", "0"],
    "수입 OR 대변": ["100,000", "0", "500,000"]
}

# UTF-8-SIG 인코딩으로 저장 (엑셀 호환 한글)
df_test = pd.DataFrame(test_data)
df_test.to_csv(test_csv_path, index=False, encoding='utf-8-sig')

print(f"--- 테스트 파일 생성 완료: {test_csv_path} ---")

# 2. 파싱 함수 호출 및 결과 확인
parsed_df = parse_donation_csv(test_csv_path)

if not parsed_df.empty:
    print("\n✅ 파싱 성공!")
    print("데이터 샘플:")
    print(parsed_df)
    
    # 데이터 타입 검증
    print("\n--- 데이터 타입 검증 ---")
    print(f"날짜 타입: {parsed_df['날짜'].dtype}")
    print(f"수입 타입: {parsed_df['수입 OR 대변'].dtype}")
    print(f"지출 타입: {parsed_df['지출 OR 차변'].dtype}")
    
    # 값 검증
    if parsed_df['수입 OR 대변'].iloc[0] == 100000.0 and parsed_df['지출 OR 차변'].iloc[1] == 15500.0:
        print("\n✅ 금액 변환 검증 완료 (콤마 제거 및 숫자 변환 정상)")
    else:
        print("\n❌ 금액 변환 검증 실패")
else:
    print("\n❌ 파싱 실패: 데이터를 읽어오지 못했습니다.")

# 테스트 파일 삭제
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)
