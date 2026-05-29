import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# 웹페이지 UI 스타일 및 격자 설정 (넓은 화면 모드)
st.set_page_config(
    page_title="P2H 전세계 실시간 모니터링",
    page_icon="📊",
    layout="wide"
)

# ⚠️ 사용님의 Supabase 고유 주소와 키를 여기에 정확히 붙여넣으세요!
SUPABASE_URL = "https://xcplxbselajptcxdqino.supabase.co"
SUPABASE_KEY = "sb_publishable_j-ECpjbfSrRxr7-9c1tAVw_0frhKKy_"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"❌ 클라우드 서버 연동 초기화 실패: {e}")
    supabase = None

st.title("📡 P2H 설비 전세계 실시간 계측 수치 관제탑")
st.caption("연구실 방화벽을 우회하여 클라우드 서버로부터 데이터를 연동하므로 전 세계 어디서나 실시간 접속을 지원합니다. (3초 주기 자동 동기화)")
st.markdown("---")

# 실시간 대시보드 렌더링을 위한 전용 공간 선언
dashboard_pos = st.empty()

# 클라우드 연동이 성공했다면 실시간 감시 루프 가동
if supabase:
    while True:
        try:
            # 클라우드 DB의 맨 위 최신 행 1개만 원격으로 빠르게 조회
            response = supabase.table("p2h_monitoring").select("*").order("id", ascending=False).limit(1).execute()
            data_rows = response.data
            
            if data_rows and len(data_rows) > 0:
                latest_data = data_rows[0]
                
                # 시간 데이터 포맷 처리
                created_at_raw = latest_data.get('created_at', '')
                current_time = created_at_raw.split(" ")[-1] if " " in created_at_raw else created_at_raw
                if not current_time:
                    current_time = time.strftime('%H:%M:%S')
                
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
                    
                    # 🔴 섹션 2: 요청하신 모든 온도/유량 순시값을 가독성 좋게 3열 그리드로 배치
                    v_col1, v_col2, v_col3 = st.columns(3)
                    
                    with v_col1:
                        st.markdown("### 💧 실시간 유량")
                        st.subheader(f"• 축열유량 : `{latest_data.get('flow_acc', 0.0):.2f}`")
                        st.subheader(f"• 급수유량 : `{latest_data.get('flow_supply', 0.0):.2f}`")
                        st.write("")
                        st.caption(f"🕒 최종 클라우드 동기화 시간: `{current_time}`")
                        
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
                # 🟡 클라우드에 아직 데이터가 쌓이지 않았을 때 안내 메시지 표출 (멈춤 방지)
                with dashboard_pos.container():
                    st.info("⏳ 현재 클라우드 데이터베이스 장부가 비어있거나 수신 대기 중입니다.")
                    st.warning("사무실 PC에서 `run_serial_git.py` 수신기를 구동하여 실시간 패킷을 클라우드로 쏴주시면 수치판이 즉시 활성화됩니다.")
                    st.caption(f"🔄 클라우드 연결 상태 확인 완료 - 최종 스캔 시간: {time.strftime('%H:%M:%S')}")
        except Exception as err:
            with dashboard_pos.container():
                st.error(f"⚠️ 데이터 연동 중 오류 발생: {err}")
            
        # 3초 주기로 화면 강제 갱신 트리거 및 클라우드 재조회
        time.sleep(3)
        st.rerun()
else:
    st.error("❌ Supabase 환경 변수가 설정되지 않아 모니터링을 시작할 수 없습니다.")