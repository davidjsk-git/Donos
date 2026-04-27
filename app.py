import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import parse_donation_html, parse_donation_csv
import os
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Donos Liquid Dashboard", page_icon="💧", layout="wide")

# Liquid Glass Custom CSS
st.markdown("""
<style>
    /* Liquid Glass Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        background-attachment: fixed;
    }
    
    /* Glassmorphism Card Style */
    div.stMetric, div.stDataFrame, .stPlotlyChart, .stAlert, div.row-widget.stButton {
        background: rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Pretendard', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Button */
    .stButton > button {
        background: rgba(100, 149, 237, 0.3);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        color: #2c3e50;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: rgba(100, 149, 237, 0.5);
        transform: translateY(-2px);
    }
    
    /* Metric Labels */
    [data-testid="stMetricLabel"] {
        color: #5d6d7e !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 디렉토리 설정
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CONFIG_FILE = "dashboard_config.json"
CRM_FILE = os.path.join(DATA_DIR, "crm_master.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 하위 호환성 보장
            if 'organizations' not in config:
                config['organizations'] = ["HOPE", "GLFocus"]
            if 'current_org' not in config:
                config['current_org'] = "HOPE"
            if 'base_balances' not in config:
                config['base_balances'] = {org: 0 for org in config['organizations']}
            return config
    return {"organizations": ["HOPE", "GLFocus"], "current_org": "HOPE", "base_balances": {"HOPE": 0, "GLFocus": 0}}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_crm():
    if os.path.exists(CRM_FILE):
        with open(CRM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_crm(crm_data):
    with open(CRM_FILE, 'w', encoding='utf-8') as f:
        json.dump(crm_data, f, ensure_ascii=False, indent=4)

# 세션 상태 초기화
if 'config' not in st.session_state:
    st.session_state.config = load_config()
if 'crm' not in st.session_state:
    st.session_state.crm = load_crm()

# 사이드바 설정
st.sidebar.title("💧 Donos Liquid")
st.sidebar.markdown("---")

menu = st.sidebar.radio("📋 메뉴 선택", ["단체별 대시보드", "통합 분석 리포트", "후원자 관계 관리(CRM)"])

# 단체 선택 및 추가
st.sidebar.markdown("### 🏢 단체 관리")
current_org = st.sidebar.selectbox("관리할 단체 선택", st.session_state.config['organizations'], 
                                 index=st.session_state.config['organizations'].index(st.session_state.config['current_org']))

if current_org != st.session_state.config['current_org']:
    st.session_state.config['current_org'] = current_org
    save_config(st.session_state.config)
    st.rerun()

with st.sidebar.expander("➕ 새 단체 추가"):
    new_org_name = st.text_input("단체명 입력")
    if st.button("추가하기"):
        if new_org_name and new_org_name not in st.session_state.config['organizations']:
            st.session_state.config['organizations'].append(new_org_name)
            st.session_state.config['base_balances'][new_org_name] = 0
            save_config(st.session_state.config)
            st.success(f"'{new_org_name}' 단체가 추가되었습니다.")
            st.rerun()

# 기초 잔액 설정
st.sidebar.markdown("### 💰 잔액 설정")
base_balance = st.sidebar.number_input(f"{current_org} 기초 후원 잔액", 
                                     value=st.session_state.config['base_balances'].get(current_org, 0), step=10000)
if base_balance != st.session_state.config['base_balances'].get(current_org, 0):
    st.session_state.config['base_balances'][current_org] = base_balance
    save_config(st.session_state.config)
    st.sidebar.success("기초 잔액이 저장되었습니다.")

# 데이터 로드 함수
def get_org_data(org):
    file_path = os.path.join(DATA_DIR, f"{org}_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df['날짜'] = pd.to_datetime(df['날짜'])
        return df
    return pd.DataFrame(columns=["날짜", "계정과목", "ㅎ원자명", "전표제목", "적요", "지출 OR 차변", "수입 OR 대변"])

# 메인 화면 로직
if menu == "단체별 대시보드":
    st.title(f"🏢 {current_org} 후원금 대시보드")
    
    # 파일 업로드
    uploaded_file = st.sidebar.file_uploader("HTML 또는 CSV 파일 업로드", type=['htm', 'html', 'csv'])
    
    df = get_org_data(current_org)
    
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            new_data = parse_donation_csv(uploaded_file)
        else:
            new_data = parse_donation_html(uploaded_file)
            
        if not new_data.empty:
            if df.empty:
                df = new_data
            else:
                df = pd.concat([df, new_data]).drop_duplicates(subset=["날짜", "ㅎ원자명", "수입 OR 대변", "지출 OR 차변"], keep='last')
            
            df = df.sort_values('날짜', ascending=False)
            df.to_csv(os.path.join(DATA_DIR, f"{current_org}_data.csv"), index=False)
            st.success(f"{uploaded_file.name} 데이터가 성공적으로 통합되었습니다!")
            st.rerun()

    if not df.empty:
        # 요약 지표
        total_income = df['수입 OR 대변'].sum()
        total_expense = df['지출 OR 차변'].sum()
        current_balance = base_balance + total_income - total_expense
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("기초 잔액", f"{base_balance:,.0f} 원")
        m2.metric("총 수입", f"{total_income:,.0f} 원")
        m3.metric("총 지출", f"{total_expense:,.0f} 원")
        m4.metric("현재 잔액", f"{current_balance:,.0f} 원", f"{total_income - total_expense:,.0f} 원")

        # 월별 추이 그래프
        st.subheader("📈 월별 수입 및 지출 추이")
        df['월'] = df['날짜'].dt.strftime('%Y-%m')
        monthly_df = df.groupby('월')[['수입 OR 대변', '지출 OR 차변']].sum().reset_index()
        monthly_df = monthly_df.sort_values('월')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly_df['월'], y=monthly_df['수입 OR 대변'], name='수입', marker_color='#3498db', opacity=0.7))
        fig.add_trace(go.Bar(x=monthly_df['월'], y=monthly_df['지출 OR 차변'], name='지출', marker_color='#e74c3c', opacity=0.7))
        fig.update_layout(
            barmode='group', 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(tickformat=',d', title='금액 (원)'),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # 데이터 편집 섹션
        st.subheader("📝 전체 내역 및 편집")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("변경사항 저장"):
            edited_df.to_csv(os.path.join(DATA_DIR, f"{current_org}_data.csv"), index=False)
            st.success("데이터가 저장되었습니다.")
            st.rerun()
    else:
        st.info("데이터가 없습니다. 사이드바에서 파일을 업로드하거나 내역을 추가해 주세요.")

elif menu == "통합 분석 리포트":
    st.title("🌐 통합 분석 리포트")
    
    all_data = []
    total_base = sum(st.session_state.config['base_balances'].values())
    
    org_stats = []
    for org in st.session_state.config['organizations']:
        df_org = get_org_data(org)
        if not df_org.empty:
            df_org['단체'] = org
            all_data.append(df_org)
            
            # 단체별 순수 후원금 계산 (GLFocus의 계좌간거래 제외)
            pure_income = df_org['수입 OR 대변'].sum()
            if org == 'GLFocus':
                pure_income -= df_org[df_org['계정과목'] == '계좌간거래']['수입 OR 대변'].sum()
            
            org_stats.append({
                "단체": org,
                "기초잔액": st.session_state.config['base_balances'].get(org, 0),
                "총수입(장부)": df_org['수입 OR 대변'].sum(),
                "순수후원수입": pure_income,
                "총지출": df_org['지출 OR 차변'].sum(),
                "현재잔액": st.session_state.config['base_balances'].get(org, 0) + df_org['수입 OR 대변'].sum() - df_org['지출 OR 차변'].sum()
            })
    
    if all_data:
        full_df = pd.concat(all_data)
        
        # 통합 지표
        total_pure_income = sum(s['순수후원수입'] for s in org_stats)
        total_expense = sum(s['총지출'] for s in org_stats)
        total_balance = sum(s['현재잔액'] for s in org_stats)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("전체 기초 잔액", f"{total_base:,.0f} 원")
        c2.metric("전체 순수 후원수입", f"{total_pure_income:,.0f} 원")
        c3.metric("전체 합산 잔액", f"{total_balance:,.0f} 원")
        
        st.subheader("📊 단체별 재무 현황 비교")
        st.table(pd.DataFrame(org_stats).set_index("단체").style.format("{:,.0f}"))
        
        # 수입 비교 그래프 (순수 후원금 기준)
        st.subheader("📈 단체별 순수 수입 비교 추이")
        full_df['월'] = full_df['날짜'].dt.strftime('%Y-%m')
        
        # GLFocus 계좌간거래 제외 필터링
        plot_df = full_df.copy()
        mask = (plot_df['단체'] == 'GLFocus') & (plot_df['계정과목'] == '계좌간거래')
        plot_df = plot_df[~mask]
        
        monthly_comp = plot_df.groupby(['월', '단체'])['수입 OR 대변'].sum().reset_index()
        fig_comp = px.bar(monthly_comp, x='월', y='수입 OR 대변', color='단체', barmode='group',
                         color_discrete_sequence=['#3498db', '#2ecc71', '#9b59b6', '#f1c40f'])
        fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(tickformat=',d'))
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # 후원자 분석 (계좌간거래 제외)
        st.divider()
        st.subheader("👥 심층 후원자 패턴 분석")
        
        donor_df = plot_df[plot_df['수입 OR 대변'] > 0].copy()
        donor_stats = donor_df.groupby('ㅎ원자명').agg({
            '수입 OR 대변': 'sum',
            '날짜': ['count', 'min', 'max', lambda x: x.dt.to_period('M').nunique()]
        }).reset_index()
        donor_stats.columns = ['후원자명', '누적후원액', '후원횟수', '최초후원일', '마지막후원일', '후원개월수']
        
        # 1. TOP 5
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🏆 **누적 후원 TOP 5**")
            top5 = donor_stats.sort_values('누적후원액', ascending=False).head(5)
            st.dataframe(top5[['후원자명', '누적후원액', '후원횟수']], hide_index=True)
            
        # 2. 연속 후원자
        with col2:
            st.markdown("⭐ **연속 후원자 (충성도 높음)**")
            total_months = plot_df['날짜'].dt.to_period('M').nunique()
            loyal_donors = donor_stats[donor_stats['후원개월수'] >= total_months * 0.8] # 80% 이상 참여
            st.dataframe(loyal_donors[['후원자명', '누적후원액', '후원개월수']], hide_index=True)
            
        # 3. 일회성 및 불연속 후원자
        st.markdown("🔍 **후원 유지 관리 대상**")
        a1, a2 = st.columns(2)
        with a1:
            st.markdown("🎁 **일회성 후원자 (전체 기간 1회)**")
            one_time = donor_stats[donor_stats['후원횟수'] == 1]
            st.dataframe(one_time[['후원자명', '누적후원액', '마지막후원일']], hide_index=True)
            
        with a2:
            st.markdown("⚠️ **불연속 후원자 (최근 6개월 내 활동)**")
            six_months_ago = datetime.now() - pd.DateOffset(months=6)
            irregular = donor_stats[
                (donor_stats['후원횟수'] > 1) & 
                (donor_stats['후원개월수'] < total_months * 0.5) &
                (donor_stats['마지막후원일'] >= six_months_ago)
            ]
            st.dataframe(irregular[['후원자명', '마지막후원일', '후원개월수']], hide_index=True)
    else:
        st.info("통합 분석을 위한 데이터가 부족합니다.")

elif menu == "후원자 관계 관리(CRM)":
    st.title("👤 후원자 관계 관리(CRM)")
    
    all_data = []
    for org in st.session_state.config['organizations']:
        df_org = get_org_data(org)
        if not df_org.empty:
            df_org['단체'] = org
            all_data.append(df_org)
    
    if not all_data:
        st.info("데이터가 없습니다.")
    else:
        full_df = pd.concat(all_data)
        full_df['ㅎ원자명'] = full_df['ㅎ원자명'].fillna('미지정').astype(str)
        donors = sorted(full_df['ㅎ원자명'].unique())
        
        # 1. 후원자 검색 및 상세 프로필
        st.subheader("🔍 후원자 상세 프로필 조회")
        selected_donor = st.selectbox("후원자 선택", donors)
        
        if selected_donor:
            donor_df = full_df[full_df['ㅎ원자명'] == selected_donor].copy()
            donor_df['날짜'] = pd.to_datetime(donor_df['날짜'], errors='coerce')
            donor_df = donor_df.dropna(subset=['날짜']).sort_values('날짜', ascending=False)
            
            if selected_donor not in st.session_state.crm:
                st.session_state.crm[selected_donor] = {"tags": [], "memo": ""}
            
            donor_info = st.session_state.crm[selected_donor]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info(f"👤 **{selected_donor}**")
                st.write(f"🔹 **총 후원 횟수:** {len(donor_df[donor_df['수입 OR 대변']>0])}회")
                st.write(f"🔹 **누적 후원액:** {donor_df['수입 OR 대변'].sum():,.0f}원")
                
                if not donor_df[donor_df['수입 OR 대변']>0].empty:
                    actual_donor_df = donor_df[donor_df['수입 OR 대변']>0]
                    first_date = actual_donor_df['날짜'].min().strftime('%Y-%m-%d')
                    last_date = actual_donor_df['날짜'].max().strftime('%Y-%m-%d')
                    st.write(f"🔹 **후원 기간:** {first_date} ~ {last_date}")
                
                st.write(f"🔹 **최근 후원일:** {donor_df['날짜'].max().strftime('%Y-%m-%d')}")
                
                # 태그 관리
                existing_tags = donor_info.get("tags", [])
                new_tags = st.multiselect("태그 관리", ["기업", "개인", "정기", "일시", "핵심", "VIP", "잠재이탈"], default=existing_tags)
                
                # 메모 관리
                new_memo = st.text_area("활동 메모", value=donor_info.get("memo", ""), height=150)
                
                if st.button("CRM 정보 저장"):
                    st.session_state.crm[selected_donor] = {"tags": new_tags, "memo": new_memo}
                    save_crm(st.session_state.crm)
                    st.success("정보가 저장되었습니다.")
            
            with c2:
                st.markdown("📜 **전체 후원 이력 (통합)**")
                st.dataframe(donor_df[['날짜', '단체', '계정과목', '수입 OR 대변', '적요']], hide_index=True, use_container_width=True)

        # 2. 태그별 후원자 그룹 필터링
        st.divider()
        st.subheader("🎯 태그별 후원자 그룹 필터링")
        all_tags = set()
        for info in st.session_state.crm.values():
            all_tags.update(info.get("tags", []))
        
        filter_tag = st.selectbox("필터링할 태그 선택", ["전체"] + sorted(list(all_tags)))
        
        if filter_tag != "전체":
            filtered_donors = [name for name, info in st.session_state.crm.items() if filter_tag in info.get("tags", [])]
            if filtered_donors:
                st.write(f"'{filter_tag}' 태그를 가진 후원자: {len(filtered_donors)}명")
                res_list = []
                for name in filtered_donors:
                    d_df = full_df[full_df['ㅎ원자명'] == name]
                    res_list.append({
                        "후원자명": name,
                        "누적후원액": d_df['수입 OR 대변'].sum(),
                        "최근후원일": d_df['날짜'].max().strftime('%Y-%m-%d')
                    })
                st.table(pd.DataFrame(res_list).style.format({"누적후원액": "{:,.0f}"}))
            else:
                st.info("해당 태그를 가진 후원자가 없습니다.")
