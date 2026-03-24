import streamlit as st
import pandas as pd

# ==========================================
# 1. 기본 설정 및 목표 데이터
# ==========================================
st.set_page_config(page_title="주간 실적 보고서 대시보드", layout="wide")
st.title("📊 주간/월간/분기별 실적 보고서 (URL 링크 연동)")

wemembers_target_data = {
    '월': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    '목표': [40, 50, 40, 40, 20, 30, 40, 50, 40, 50, 50, 50],
    '분기': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
}
df_we_target = pd.DataFrame(wemembers_target_data)

kt_target_data = {
    '월': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    '목표': [50, 50, 100, 150, 200, 300, 300, 300, 350, 400, 400, 400],
    '분기': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
}
df_kt_target = pd.DataFrame(kt_target_data)

# ==========================================
# 2. 공통 함수: 목요일~수요일 날짜 기준 계산
# ==========================================
def add_period_columns(df, date_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col]).copy() # 빈 행 제거
    
    # 해당 날짜가 속한 주차의 시작일(목요일)과 종료일(수요일) 계산
    # (월요일=0, 목요일=3)
    offset = (df[date_col].dt.weekday - 3) % 7
    start_thursday = df[date_col] - pd.to_timedelta(offset, unit='D')
    end_wednesday = start_thursday + pd.Timedelta(days=6)
    
    # 주차 표시를 "YY-MM-DD ~ MM-DD" 형태의 날짜로 생성 (예: 24-03-14 ~ 03-20)
    df['주차'] = start_thursday.dt.strftime('%y-%m-%d') + ' ~ ' + end_wednesday.dt.strftime('%m-%d')
    
    df['월'] = df[date_col].dt.month
    df['분기'] = df[date_col].dt.quarter
    return df

# ==========================================
# 3. 구글 스프레드시트 URL 설정 (CSV 다운로드 링크)
# ==========================================
DOCUMENT_ID = "1aEZgrhStJ09lFkdOJjUEuDXJb-cmxQvsfheKpXPgwP0"

url_we = f"https://docs.google.com/spreadsheets/d/{DOCUMENT_ID}/export?format=csv&gid=0"
url_kt = f"https://docs.google.com/spreadsheets/d/{DOCUMENT_ID}/export?format=csv&gid=645031752"
url_k  = f"https://docs.google.com/spreadsheets/d/{DOCUMENT_ID}/export?format=csv&gid=1610867875"

# ==========================================
# 4. 데이터 로드 및 화면 구성
# ==========================================
try:
    with st.spinner('구글 스프레드시트에서 데이터를 읽어오는 중입니다...'):
        df_we_raw = pd.read_csv(url_we)
        df_kt_raw = pd.read_csv(url_kt)
        df_k_raw = pd.read_csv(url_k)

    tab1, tab2, tab3 = st.tabs(["🔵 위멤버스", "🟢 경리나라T", "🟡 경리나라"])

    # --- 탭 1: 위멤버스 ---
    with tab1:
        st.header("위멤버스 가입 현황")
        df_we = add_period_columns(df_we_raw.copy(), '가입일자')
        
        we_weekly = df_we.pivot_table(index='주차', columns='제품명', values='가입일자', aggfunc='count', fill_value=0).reset_index()
        we_weekly.columns.name = None # 표를 더 깔끔하게 만들기 위해 컬럼명 초기화
        
        we_monthly = df_we.pivot_table(index='월', columns='제품명', values='가입일자', aggfunc='count', fill_value=0)
        we_quarterly = df_we.pivot_table(index='분기', columns='제품명', values='가입일자', aggfunc='count', fill_value=0)
        
        we_monthly['실적합계'] = we_monthly.sum(axis=1)
        we_monthly_report = we_monthly.merge(df_we_target[['월', '목표']], on='월', how='left')
        we_monthly_report['달성률(%)'] = (we_monthly_report['실적합계'] / we_monthly_report['목표']) * 100

        we_q_target = df_we_target.groupby('분기')['목표'].sum().reset_index()
        we_quarterly['실적합계'] = we_quarterly.sum(axis=1)
        we_quarterly_report = we_quarterly.merge(we_q_target, on='분기', how='left')
        we_quarterly_report['달성률(%)'] = (we_quarterly_report['실적합계'] / we_quarterly_report['목표']) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("월별 달성률")
            # hide_index=True 를 추가하여 맨 앞의 쓸모없는 0,1,2 열을 삭제합니다
            st.dataframe(we_monthly_report.style.format({'달성률(%)': '{:.1f}%'}), hide_index=True)
        with col2:
            st.subheader("분기별 달성률")
            st.dataframe(we_quarterly_report.style.format({'달성률(%)': '{:.1f}%'}), hide_index=True)
        
        st.subheader("주차별 가입 현황 (제품별)")
        st.dataframe(we_weekly, hide_index=True)

    # --- 탭 2: 경리나라T ---
    with tab2:
        st.header("경리나라T 현황")
        df_kt = df_kt_raw.copy()
        
        # 가입일자 기준
        df_kt_join = add_period_columns(df_kt.copy(), '가입일자')
        kt_join_weekly = df_kt_join.groupby('주차')['가입일자'].count().reset_index(name='가입건수')
        kt_join_monthly = df_kt_join.groupby('월')['가입일자'].count().reset_index(name='실적합계')
        kt_join_quarterly = df_kt_join.groupby('분기')['가입일자'].count().reset_index(name='실적합계')

        kt_monthly_report = kt_join_monthly.merge(df_kt_target[['월', '목표']], on='월', how='left')
        kt_monthly_report['달성률(%)'] = (kt_monthly_report['실적합계'] / kt_monthly_report['목표']) * 100

        kt_q_target = df_kt_target.groupby('분기')['목표'].sum().reset_index()
        kt_quarterly_report = kt_join_quarterly.merge(kt_q_target, on='분기', how='left')
        kt_quarterly_report['달성률(%)'] = (kt_quarterly_report['실적합계'] / kt_quarterly_report['목표']) * 100

        # 설치일자 기준
        df_kt_install = add_period_columns(df_kt.copy(), '설치일자')
        kt_install_weekly = df_kt_install.groupby('주차')['설치일자'].count().reset_index(name='설치건수')

        st.subheader("가입일자 기준 목표 달성률")
        c1, c2 = st.columns(2)
        with c1:
            st.write("월별")
            st.dataframe(kt_monthly_report.style.format({'달성률(%)': '{:.1f}%'}), hide_index=True)
        with c2:
            st.write("분기별")
            st.dataframe(kt_quarterly_report.style.format({'달성률(%)': '{:.1f}%'}), hide_index=True)
        
        st.subheader("가입 및 설치 주차별 현황")
        c3, c4 = st.columns(2)
        with c3:
            st.write("가입일자 기준 주별")
            st.dataframe(kt_join_weekly, hide_index=True)
        with c4:
            st.write("설치일자 기준 주별")
            st.dataframe(kt_install_weekly, hide_index=True)

    # --- 탭 3: 경리나라 ---
    with tab3:
        st.header("경리나라 설치 현황 (위멤버스클럽_신규)")
        df_k = df_k_raw.copy()
        
        df_k_filtered = df_k[df_k['유입채널구분'] == '위멤버스클럽_신규'].copy()
        df_k_filtered = add_period_columns(df_k_filtered, '설치일자')
        
        k_weekly = df_k_filtered.groupby('주차')['설치일자'].count().reset_index(name='설치건수')
        k_monthly = df_k_filtered.groupby('월')['설치일자'].count().reset_index(name='설치건수')
        k_quarterly = df_k_filtered.groupby('분기')['설치일자'].count().reset_index(name='설치건수')

        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("주차별")
            st.dataframe(k_weekly, hide_index=True)
        with col2:
            st.subheader("월별")
            st.dataframe(k_monthly, hide_index=True)
        with col3:
            st.subheader("분기별")
            st.dataframe(k_quarterly, hide_index=True)

except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다.\n\n오류 내용: {e}")