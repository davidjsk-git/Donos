import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import parse_donation_html, parse_donation_csv
import os
import json
from datetime import datetime

st.set_page_config(page_title="통합 후원금 및 CRM 시스템", layout="wide")

# 데이터 및 설정 저장 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(BASE_DIR, "dashboard_config.json")
CRM_FILE = os.path.join(DATA_DIR, "crm_master.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ------------------------------------------------------------------------------
# 데이터 로드 및 저장 함수
# ------------------------------------------------------------------------------
def load_global_config():
    default_config = {"organizations": ["HOPE", "GLFocus"], "current_org": "HOPE", "org_settings": {}}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except:
            return default_config
    return default_config

def save_global_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_crm_data():
    if os.path.exists(CRM_FILE):
        try:
            with open(CRM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_crm_data(crm_data):
    with open(CRM_FILE, 'w', encoding='utf-8') as f:
        json.dump(crm_data, f, ensure_ascii=False, indent=4)

def get_org_data_path(org_name):
    return os.path.join(DATA_DIR, f"{org_name}_data.csv")

def load_org_data(org_name):
    path = get_org_data_path(org_name)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['날짜'] = pd.to_datetime(df['날짜'])
        return df
    return pd.DataFrame(columns=['날짜', '계정과목', 'ㅎ원자명', '전표제목', '적요', '지출 OR 차변', '수입 OR 대변'])

def save_org_data(org_name, df):
    path = get_org_data_path(org_name)
    df.to_csv(path, index=False, encoding='utf-8-sig')

# ------------------------------------------------------------------------------
# 세션 상태 초기화
# ------------------------------------------------------------------------------
if 'config' not in st.session_state:
    st.session_state.config = load_global_config()
if 'crm' not in st.session_state:
    st.session_state.crm = load_crm_data()

# ------------------------------------------------------------------------------
# 사이드바: 메뉴 및 단체 관리
# ------------------------------------------------------------------------------
st.sidebar.title("🏢 후원금 및 CRM 시스템")
menu = st.sidebar.radio("메뉴 선택", ["단체별 대시보드", "통합 분석 리포트", "후원자 관계 관리(CRM)"])

if menu == "단체별 대시보드":
    current_org = st.sidebar.selectbox("관리할 단체 선택", st.session_state.config["organizations"])
    
    with st.sidebar.expander("➕ 새 단체 추가"):
        new_org_name = st.text_input("단체명 입력")
        if st.button("추가"):
            if new_org_name and new_org_name not in st.session_state.config["organizations"]:
                st.session_state.config["organizations"].append(new_org_name)
                save_global_config(st.session_state.config)
                st.success(f"'{new_org_name}' 추가됨")
                st.rerun()

    st.sidebar.markdown("---")
    df = load_org_data(current_org)
    org_settings = st.session_state.config.get("org_settings", {})
    current_org_settings = org_settings.get(current_org, {"initial_balance": 0.0})
    
    new_init_bal = st.sidebar.number_input(f"{current_org} 기초 잔액", value=float(current_org_settings.get("initial_balance", 0.0)), format="%.0f")
    if new_init_bal != current_org_settings.get("initial_balance"):
        st.session_state.config["org_settings"][current_org] = {"initial_balance": new_init_bal}
        save_global_config(st.session_state.config)
        st.sidebar.success("기초 잔액 저장됨")

    st.sidebar.subheader("📁 데이터 업로드")
    uploaded_file = st.sidebar.file_uploader("HTML/CSV 파일 업로드", type=["htm", "html", "csv"])
    if uploaded_file:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        temp_path = os.path.join(DATA_DIR, f"temp_{current_org}{file_ext}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        new_df = parse_donation_html(temp_path) if file_ext in ['.htm', '.html'] else parse_donation_csv(temp_path)
        if not new_df.empty:
            df = pd.concat([df, new_df]).drop_duplicates().reset_index(drop=True)
            save_org_data(current_org, df)
            st.sidebar.success("업로드 완료!")
            os.remove(temp_path)
            st.rerun()

    st.title(f"📊 {current_org} 대시보드")
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        df['월'] = df['날짜'].dt.strftime('%Y-%m')
        total_in = df['수입 OR 대변'].sum()
        total_out = df['지출 OR 차변'].sum()
        curr_bal = new_init_bal + total_in - total_out
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("기초 잔액", f"{new_init_bal:,.0f}")
        c2.metric("총 수입", f"{total_in:,.0f}")
        c3.metric("총 지출", f"{total_out:,.0f}")
        c4.metric("현재 잔액", f"{curr_bal:,.0f}")
        
        monthly = df.groupby('월').agg({'수입 OR 대변':'sum', '지출 OR 차변':'sum'}).reset_index().sort_values('월')
        fig = px.line(monthly, x='월', y=['수입 OR 대변', '지출 OR 차변'], markers=True, template="plotly_white")
        fig.update_layout(yaxis=dict(tickformat=",d"))
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📝 전체 내역")
        edited_df = st.data_editor(df.drop(columns=['월']), num_rows="dynamic", use_container_width=True)
        if st.button("변경사항 저장"):
            save_org_data(current_org, edited_df)
            st.success("저장 완료")
            st.rerun()

elif menu == "통합 분석 리포트":
    st.title("🌐 통합 분석 리포트")
    all_data = []
    org_summaries = []
    for org in st.session_state.config["organizations"]:
        df_org = load_org_data(org)
        if not df_org.empty:
            df_org['단체'] = org
            df_analysis = df_org.copy()
            if org == 'GLFocus':
                df_analysis = df_analysis[~((df_analysis['계정과목'] == '계좌간거래') & (df_analysis['수입 OR 대변'] > 0))]
            all_data.append(df_analysis)
            init_bal = st.session_state.config.get("org_settings", {}).get(org, {}).get("initial_balance", 0.0)
            org_summaries.append({
                "단체": org, "기초 잔액": init_bal, "총 수입(장부)": df_org['수입 OR 대변'].sum(),
                "순수 후원수입": df_analysis['수입 OR 대변'].sum(), "총 지출": df_org['지출 OR 차변'].sum(),
                "현재 잔액": init_bal + df_org['수입 OR 대변'].sum() - df_org['지출 OR 차변'].sum()
            })
    if not all_data:
        st.info("데이터가 없습니다.")
    else:
        full_df = pd.concat(all_data)
        full_df['월'] = full_df['날짜'].dt.strftime('%Y-%m')
        summary_df = pd.DataFrame(org_summaries)
        
        st.subheader("💰 전체 재무 통합 현황")
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        t_col1.metric("전체 기초 잔액", f"{summary_df['기초 잔액'].sum():,.0f}")
        t_col2.metric("전체 총 수입", f"{summary_df['총 수입(장부)'].sum():,.0f}")
        t_col3.metric("전체 총 지출", f"{summary_df['총 지출'].sum():,.0f}")
        t_col4.metric("전체 합산 잔액", f"{summary_df['현재 잔액'].sum():,.0f}")
        st.table(summary_df.style.format({"기초 잔액": "{:,.0f}", "총 수입(장부)": "{:,.0f}", "순수 후원수입": "{:,.0f}", "총 지출": "{:,.0f}", "현재 잔액": "{:,.0f}"}))
        
        st.subheader("📊 단체별 수입 비교 추이")
        comp_df = full_df.groupby(['월', '단체'])['수입 OR 대변'].sum().reset_index()
        fig_comp = px.bar(comp_df, x='월', y='수입 OR 대변', color='단체', barmode='group', template="plotly_white")
        fig_comp.update_layout(yaxis=dict(tickformat=",d"))
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.divider()
        st.subheader("🔍 후원자 패턴 분석 (순수 후원 기준)")
        donor_stats = full_df[full_df['수입 OR 대변'] > 0].groupby('ㅎ원자명').agg(
            후원횟수=('날짜', 'count'), 후원개월수=('월', 'nunique'), 마지막후원일=('날짜', 'max'), 누적후원금=('수입 OR 대변', 'sum')
        ).reset_index().rename(columns={'ㅎ원자명': '후원자명'})
        
        all_months = sorted(full_df['월'].unique())
        total_months_count = len(all_months)
        six_months_ago = pd.Timestamp.now() - pd.DateOffset(months=6)
        
        loyal_donors = donor_stats[donor_stats['후원개월수'] >= total_months_count]
        one_time_donors = donor_stats[donor_stats['후원횟수'] == 1]
        irregular_donors = donor_stats[(donor_stats['후원횟수'] > 1) & (donor_stats['후원개월수'] < total_months_count) & (donor_stats['마지막후원일'] >= six_months_ago)]
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("🏆 **누적 후원 TOP 5**")
            top5 = donor_stats.sort_values('누적후원금', ascending=False).head(5)
            st.dataframe(top5[['후원자명', '누적후원금']].style.format({'누적후원금':'{:,.0f}'}), hide_index=True)
            st.markdown(f"⭐ **연속 후원자 ({len(loyal_donors)}명)**")
            st.write(", ".join(loyal_donors['후원자명'].tolist()) if not loyal_donors.empty else "없음")
            st.markdown(f"🎁 **일회성 후원자 ({len(one_time_donors)}명)**")
            if not one_time_donors.empty:
                st.dataframe(one_time_donors[['후원자명', '마지막후원일', '누적후원금']].sort_values('마지막후원일', ascending=False), hide_index=True, use_container_width=True)
        with col_b:
            st.markdown(f"⚠️ **불연속 후원자 (최근 6개월 기준, {len(irregular_donors)}명)**")
            if not irregular_donors.empty:
                st.dataframe(irregular_donors[['후원자명', '후원개월수', '마지막후원일', '누적후원금']].sort_values('마지막후원일', ascending=False).assign(마지막후원일=lambda x: x['마지막후원일'].dt.strftime('%Y-%m-%d')), hide_index=True, use_container_width=True)
                st.caption("※ 2회 이상 후원했으나 비정기적으로 후원 중인 분들입니다.")

else: # CRM 메뉴
    st.title("👤 후원자 관계 관리 (CRM)")
    
    # 전체 단체 데이터 통합 로드
    all_data = []
    for org in st.session_state.config["organizations"]:
        df_org = load_org_data(org)
        if not df_org.empty:
            df_org['단체'] = org
            all_data.append(df_org)
    
    if not all_data:
        st.info("데이터가 없습니다.")
    else:
        full_df = pd.concat(all_data)
        # 'ㅎ원자명' 컬럼에 NaN이나 문자열이 아닌 값이 섞여 있을 수 있으므로 처리
        full_df['ㅎ원자명'] = full_df['ㅎ원자명'].fillna('미지정').astype(str)
        donors = sorted(full_df['ㅎ원자명'].unique())
        
        # 1. 후원자 검색 및 상세 프로필
        st.subheader("🔍 후원자 상세 프로필 조회")
        selected_donor = st.selectbox("후원자 선택", donors)
        
        if selected_donor:
            # 날짜 정렬 시 에러 방지를 위해 datetime 변환 보장
            donor_df = full_df[full_df['ㅎ원자명'] == selected_donor].copy()
            donor_df['날짜'] = pd.to_datetime(donor_df['날짜'], errors='coerce')
            donor_df = donor_df.dropna(subset=['날짜']).sort_values('날짜', ascending=False)
            
            # 후원자 마스터 정보 로드/초기화
            if selected_donor not in st.session_state.crm:
                st.session_state.crm[selected_donor] = {"tags": [], "memo": ""}
            
            donor_info = st.session_state.crm[selected_donor]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info(f"👤 **{selected_donor}**")
                st.write(f"🔹 **총 후원 횟수:** {len(donor_df[donor_df['수입 OR 대변']>0])}회")
                st.write(f"🔹 **누적 후원액:** {donor_df['수입 OR 대변'].sum():,.0f}원")
                
                # 후원 기간 계산 (최초 후원일 ~ 마지막 후원일)
                if not donor_df[donor_df['수입 OR 대변']>0].empty:
                    actual_donor_df = donor_df[donor_df['수입 OR 대변']>0]
                    first_date = actual_donor_df['날짜'].min().strftime('%Y-%m-%d')
                    last_date = actual_donor_df['날짜'].max().strftime('%Y-%m-%d')
                    st.write(f"🔹 **후원 기간:** {first_date} ~ {last_date}")
                
                st.write(f"🔹 **최근 후원일:** {donor_df['날짜'].max().strftime('%Y-%m-%d')}")
                
                # 태그 관리
                existing_tags = donor_info.get("tags", [])
                new_tags = st.multiselect("태그 관리", ["기업", "개인", "정기", "일시", "핵심", "VIP", "잠재이탈"], default=existing_tags)
                if new_tags != existing_tags:
                    st.session_state.crm[selected_donor]["tags"] = new_tags
                    save_crm_data(st.session_state.crm)
                    st.success("태그 저장됨")
            
            with c2:
                # 메모 관리
                memo = st.text_area("활동 메모 (상담 내역, 특이사항 등)", value=donor_info.get("memo", ""), height=150)
                if st.button("메모 저장"):
                    st.session_state.crm[selected_donor]["memo"] = memo
                    save_crm_data(st.session_state.crm)
                    st.success("메모 저장됨")
            
            st.markdown("---")
            st.subheader(f"📜 {selected_donor} 후원 이력")
            st.dataframe(donor_df[['날짜', '단체', '계정과목', '수입 OR 대변', '적요']].style.format({'수입 OR 대변':'{:,.0f}'}), use_container_width=True, hide_index=True)

        # 2. 태그 기반 스마트 필터링
        st.divider()
        st.subheader("🎯 태그 기반 타겟팅 분석")
        all_available_tags = set()
        for info in st.session_state.crm.values():
            all_available_tags.update(info.get("tags", []))
            
        filter_tag = st.multiselect("필터링할 태그 선택", list(all_available_tags))
        
        if filter_tag:
            target_donors = []
            for d_name, d_info in st.session_state.crm.items():
                if any(t in d_info.get("tags", []) for t in filter_tag):
                    # 데이터 합산
                    d_data = full_df[full_df['ㅎ원자명'] == d_name]
                    target_donors.append({
                        "후원자명": d_name,
                        "태그": ", ".join(d_info.get("tags", [])),
                        "누적후원금": d_data['수입 OR 대변'].sum(),
                        "마지막후원": d_data['날짜'].max().strftime('%Y-%m-%d')
                    })
            
            if target_donors:
                st.dataframe(pd.DataFrame(target_donors).style.format({'누적후원금':'{:,.0f}'}), use_container_width=True, hide_index=True)
            else:
                st.write("해당 태그를 가진 후원자가 없습니다.")
        else:
            st.info("태그를 선택하여 특정 그룹을 분석해 보세요.")
