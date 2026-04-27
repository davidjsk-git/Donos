import pandas as pd
from bs4 import BeautifulSoup
import os

def clean_donation_df(df):
    """
    데이터프레임의 공통 정제 로직 (금액 변환, 날짜 변환 등)
    """
    # '합계액' 행 또는 날짜가 비어있는 행 제거
    if '날짜' in df.columns:
        df = df[df['날짜'].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}', na=False)].copy()

    # 금액 컬럼에서 콤마 제거 및 숫자로 변환
    amount_cols = ['지출 OR 차변', '수입 OR 대변']
    for col in amount_cols:
        if col in df.columns:
            # 문자열에서 숫자와 소수점만 남기고 제거 (콤마 등 처리)
            df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # 날짜 변환 (에러 발생 시 NaT로 처리 후 제거)
    if '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        df = df.dropna(subset=['날짜'])
        
    return df

def parse_donation_html(file_path):
    """
    HTML 파일을 읽어 데이터프레임으로 변환합니다.
    """
    try:
        with open(file_path, 'r', encoding='cp949') as f:
            html_content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return pd.DataFrame()

    rows = table.find_all('tr')
    data = []
    
    # 첫 번째 행은 헤더
    headers = [td.get_text(strip=True) for td in rows[0].find_all('td')]
    
    for row in rows[1:]:
        cols = row.find_all('td')
        cols = [ele.get_text(strip=True) for ele in cols]
        if len(cols) == len(headers):
            data.append(cols)
            
    df = pd.DataFrame(data, columns=headers)
    return clean_donation_df(df)

def parse_donation_csv(file_path):
    """
    CSV 파일을 읽어 데이터프레임으로 변환합니다. (인코딩 자동 시도)
    """
    encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            # 필수 헤더가 포함되어 있는지 확인
            required_cols = ['날짜', '지출 OR 차변', '수입 OR 대변']
            if all(col in df.columns for col in required_cols):
                return clean_donation_df(df)
        except Exception:
            continue
    return pd.DataFrame()

def analyze_trends(df):
    """
    월별 수입/지출 증감 및 원인 분석
    """
    if df.empty:
        return None
        
    df['YearMonth'] = df['날짜'].dt.to_period('M')
    monthly_summary = df.groupby('YearMonth').agg({
        '수입 OR 대변': 'sum',
        '지출 OR 차변': 'sum'
    }).reset_index()
    
    monthly_summary['수입_변화'] = monthly_summary['수입 OR 대변'].diff()
    monthly_summary['지출_변화'] = monthly_summary['지출 OR 차변'].diff()
    
    return monthly_summary

def get_donor_analysis(df):
    """
    후원자별 분석 (신규, 이탈 등)
    """
    if df.empty or 'ㅎ원자명' not in df.columns:
        return None
        
    df['YearMonth'] = df['날짜'].dt.to_period('M')
    donor_monthly = df[df['수입 OR 대변'] > 0].groupby(['YearMonth', 'ㅎ원자명'])['수입 OR 대변'].sum().reset_index()
    
    return donor_monthly
