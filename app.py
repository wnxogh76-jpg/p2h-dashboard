import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta  # 🛠️ [바뀜] 시차 계산을 위해 datetime 불러오기
from supabase import create_client, Client

# 웹페이지 UI 스타일 및 격자 설정 (사이드바 없이 넓게)
st.set_page_config(
    page_title="P2H 전세계 실시간 모니터링",
    page_icon="📊",
    layout="wide"
)

# 소스코드 보안 유지 (스트림릿 금고 사용)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"❌ 클라우드 서버 연동 초기화 실패: {e}")
    supabase = None

st.title("📡 P2H 실시간 계측 수치 관제탑")
st.caption(" (3초 주기 자동 동기화)")
st.markdown("---")

# 전체 화면을 지우지 않고 내부 수치만 스무스하게 덮어쓰기 위해 최상단 컨테이너 공간 선언
dashboard_pos = st.empty()

if supabase:
    while True:
        try:
            # 최신 버전의 supabase-py 문법에 맞춰 id 역순 정렬로 1개 조회
            response = supabase.table("p2h_monitoring").select("*").order("id", desc=True).limit(1).execute()
            data_rows = response.data
            
            if data_rows and len(data_rows) > 0:
                latest_data = data_rows[0]
                
                # 🛠️ [바뀜] Supabase의 세계 표준시(UTC) 문자열을 파이썬 시간 객체로 변환한 뒤 한국 시간(+9시간)으로 보정
                created_at_raw = latest_data.get('created_at', '')
                try:
                    # '2026-05-29 01:49:23' 형태의 문자열을 파싱
                    utc_time = datetime.strptime(created_at_raw, "%Y-%m-%d %H:%M:%S")
                    # 한국 시차인 9시간을 강제로 더해줌
                    kst_time = utc_time + timedelta(hours=9)
                    current_time = kst_time.strftime("%H:%M:%S")
                except Exception:
                    # 만약 날짜 포맷이 다르거나 파싱 실패 시, 문자열 슬라이싱 대안 혹은 현재 시스템 시간 사용
                    current_time = created_at_raw.split(" ")[-1] if " " in created_at_raw else created_at_raw
                    if not current_time:
                        current_time = time.strftime('%H:%M:%S')
                
                # dashboard_pos.container() 안쪽 영역만 실시간으로 갈아끼움
                with dashboard_pos.container():
                    # 🔴 섹션 1: 실시간 3대 핵심 성능 지표 카드 매트릭스
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="🌡️ dT (HP 입출구 온도차)", value=f"{latest_data.get('dt', 0.0):.2f} °C")
                    with col2:
                        st.metric(label="🔥 R290 순시 열량", value=f"{latest_data.get('heat_r290', 0.0):.1f} W")
                    with col3:
                        st.metric(label="📈 R290 COP", value=f"{latest_data.get('cop_r290', 0.0):.2f}")
                    
                    st.markdown("---")
                    
                    # 🔴 섹션 2: 모든 온도/유량 순시값을 가독성 좋게 3열 그리드로 배치
                    v_col1, v_col2, v_col3 = st.columns(3)
                    
                    with v_col1:
                        st.markdown("### 💧 실시간 유량")
                        st.subheader(f"• 축열유량 : `{latest_data.get('flow_acc', 0.0):.2f}`")
                        st.subheader(f"• 급수유량 : `{latest_data.get('flow_supply', 0.0):.2f}`")
                        st.write("")
                        st.caption(f"🕒 최종 클라우드 동기화 시간(KST): `{current_time}`") # 🛠️ [바뀜] 표시 문구 조정
                        
                    with v_col2:
                        st.markdown("### 🌡️ 히트펌프 및 외부 온도")
                        st.subheader(f"• HP 입구온도 : `{latest_data.get('t_hp_in', 0.0):.2f} °C`")
                        st.subheader(f"• HP 출구온도 : `{latest_data.get('t_hp_out', 0.0):.2f} °C`")
                        st.subheader(f"• 외부온도 : `{latest_data.get('t_out', 0.0):.2f} °C`")
                        
                    with v_col3:
                        st.markdown("### 📦 PCM 축열조 온도")
                        st.subheader(f"• 축열조 입구 : `{latest_data.get('t_pcm_in', 0.0):.2f} °C`")
                        st.subheader(f"• 축열조 출구 : `{latest_data.get('t_pcm_out', 0.0):.2f} °C`")
                        st.markdown("---")
                        
                        p1, p2 = st.columns(2)
                        with p1:
                            st.write(f"• PCM 1번: **{latest_data.get('t_pcm1', 0.0):.2f} °C**")
                            st.write(f"• PCM 2번: **{latest_data.get('t_pcm2', 0.0):.2f} °C**")
                        with p2:
                            st.write(f"• PCM 3번: **{latest_data.get('t_pcm3', 0.0):.2f} °C**")
                            st.write(f"• PCM 4번: **{latest_data.get('t_pcm4', 0.0):.2f} °C**")
                            
                    st.markdown("---")
            else:
                with dashboard_pos.container():
                    st.info("⏳ 현재 클라우드 데이터베이스 장부가 비어있거나 수신 대기 중입니다.")
                    st.warning("사무실 PC에서 수신기를 구동하여 실시간 패킷을 클라우드로 쏴주시면 수치판이 즉시 활성화됩니다.")
        except Exception as err:
            with dashboard_pos.container():
                st.error(f"⚠️ 데이터 연동 중 오류 발생: {err}")
            
        # 3초 동안 멈춘 뒤 대시보드 내부 영역만 스무스하게 무한 반복 갱신
        time.sleep(3)
else:
    st.error("❌ Supabase 환경 변수가 설정되지 않아 모니터링을 시작할 수 없습니다.")
