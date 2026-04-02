import streamlit as st
import pandas as pd

# ==========================================
# 1. 기본 설정 및 목표 데이터
# ==========================================
st.set_page_config(page_title="통합 실적 보고서", layout="wide")
st.title("📊 주간 실적 보고")

# 목표 데이터
df_we_target = pd.DataFrame({'월': range(1, 13), '목표': [40,50,40,40,20,30,40,50,40,50,50,50], '분기': [1,1,1,2,2,2,3,3,3,4,4,4]})
df_kt_target = pd.DataFrame({'월': range(1, 13), '목표': [50,50,100,150,200,300,300,300,350,400,400,400], '분기': [1,1,1,2,2,2,3,3,3,4,4,4]})

# ==========================================
# 2. 유틸리티 함수
# ==========================================
def add_period_columns(df, date_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col]).copy()
    offset = (df[date_col].dt.weekday - 3) % 7
    st_thu = df[date_col] - pd.to_timedelta(offset, unit='D')
    ed_wed = st_thu + pd.Timedelta(days=6)
    df['주차_시작일'] = st_thu
    df['주차'] = st_thu.dt.strftime('%y-%m-%d') + ' ~ ' + ed_wed.dt.strftime('%m-%d')
    df['월'] = df[date_col].dt.month
    df['분기'] = df[date_col].dt.quarter
    return df

def apply_last_month_delta(df_pivot):
    """마지막 행(최신달)에만 숫자(▲증감) 형식을 적용"""
    if df_pivot.empty: return df_pivot
    df_res = df_pivot.copy()
    last_idx = df_res.index[-1]
    # 제외할 컬럼들
    exclude = ['월', '실적합계', '목표', '달성률', '분기']
    cols = [c for c in df_res.columns if c not in exclude]
    
    for col in cols:
        val = df_res.at[last_idx, col]
        try:
            num = int(float(val))
            df_res.at[last_idx, col] = f"{num}(▲{num})" if num > 0 else f"{num}(-)"
        except: pass
    return df_res

# ==========================================
# 3. 데이터 로드 및 탭 구성
# ==========================================
DOC_ID = "1aEZgrhStJ09lFkdOJjUEuDXJb-cmxQvsfheKpXPgwP0"
urls = {
    "we": f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid=0",
    "kt": f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid=645031752",
    "k": f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid=1610867875"
}

try:
    with st.spinner('실시간 실적 데이터를 집계 중입니다...'):
        df_we_raw = pd.read_csv(urls["we"])
        df_kt_raw = pd.read_csv(urls["kt"])
        df_k_raw = pd.read_csv(urls["k"])

    tabs = st.tabs(["🔵 위멤버스", "🟢 경리나라T", "🟡 경리나라"])

    # --- 탭 1 & 2: 위멤버스 & 경리나라T ---
    for tab, df_raw, target_df, title, d_col in zip(tabs[:2], [df_we_raw, df_kt_raw], [df_we_target, df_kt_target], ["위멤버스", "경리나라T"], ["가입일자", "가입일자"]):
        with tab:
            df = add_period_columns(df_raw.copy(), d_col)
            
            # 1. 연간 성과 요약
            st.header(f"🏆 {title} 연간 성과")
            annual_actual = len(df)
            annual_target = target_df['목표'].sum()
            annual_rate = (annual_actual / annual_target) * 100
            
            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("누적 달성률", f"{annual_rate:.1f}%")
            col_kpi2.metric("누적 실적", f"{annual_actual}건")
            col_kpi3.metric("연간 목표", f"{annual_target}건")
            st.divider()

            # 2. 월별 실적 (마지막 달 증감 표시)
            st.subheader("📅 월별 상세 실적 (최신월 증감 포함)")
            # [수정완료] '製品명' -> '제품명'으로 교체
            m_p = df.pivot_table(index='월', columns='제품명', values=d_col, aggfunc='count', fill_value=0).reset_index()
            m_p_display = apply_last_month_delta(m_p)
            
            m_calc = df.groupby('월').size().reset_index(name='실적합계')
            m_report = m_p_display.merge(m_calc, on='월').merge(target_df[['월', '목표']], on='월')
            m_report['달성률'] = (m_report['실적합계'] / m_report['목표'] * 100)
            st.dataframe(m_report.style.format({'달성률': '{:.1f}%'}), hide_index=True, use_container_width=True)

            # 3. 분기별 실적
            st.subheader("📊 분기별 실적")
            q_p = df.pivot_table(index='분기', columns='제품명', values=d_col, aggfunc='count', fill_value=0).reset_index()
            q_target = target_df.groupby('분기')['목표'].sum().reset_index()
            q_report = q_p.merge(q_target, on='분기')
            q_report['실적합계'] = q_p.drop('분기', axis=1).sum(axis=1)
            q_report['달성률'] = (q_report['실적합계'] / q_report['목표'] * 100)
            st.dataframe(q_report.style.format({'달성률': '{:.1f}%'}), hide_index=True, use_container_width=True)

            # 4. 주차별 수치
            st.subheader("📈 주차별 단순 가입 수치")
            w_p = df.pivot_table(index=['주차_시작일', '주차'], columns='제품명', values=d_col, aggfunc='count', fill_value=0).reset_index().sort_values('주차_시작일', ascending=False)
            st.dataframe(w_p.drop('주차_시작일', axis=1), hide_index=True, use_container_width=True)

    # --- 탭 3: 경리나라 ---
    with tabs[2]:
        df_k = df_k_raw[df_k_raw['유입채널구분'] == '위멤버스클럽_신규'].copy()
        df_k = add_period_columns(df_k, '설치일자')
        
        st.header("🏆 경리나라 연간 성과")
        st.metric("전체 누적 설치", f"{len(df_k)}건")
        st.divider()

        # 월별 설치 (마지막 달 증감)
        st.subheader("📅 월별 설치 (최신월 증감)")
        k_m = df_k.groupby('월').size().reset_index(name='설치건수')
        k_m['설치건수'] = k_m['설치건수'].astype(object)
        if not k_m.empty:
            l_idx = k_m.index[-1]
            l_val = k_m.at[l_idx, '설치건수']
            k_m.at[l_idx, '설치건수'] = f"{l_val}(▲{l_val})"
        st.dataframe(k_m, hide_index=True)

        # 분기별 & 주차별
        c_q, c_w = st.columns([1, 2])
        with c_q:
            st.subheader("📊 분기별 설치")
            st.dataframe(df_k.groupby('분기').size().reset_index(name='설치건수'), hide_index=True)
        with c_w:
            st.subheader("📈 주차별 설치 수치")
            k_w = df_k.groupby(['주차_시작일', '주차']).size().reset_index(name='설치건수').sort_values('주차_시작일', ascending=False)
            st.dataframe(k_w.drop('주차_시작일', axis=1), hide_index=True)

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")