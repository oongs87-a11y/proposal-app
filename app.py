import streamlit as st
import os
from datetime import datetime
from deepseek_service import generate_proposal_content
from pdf_generator import build_pdf

# 페이지 기본 설정 (와이드 모드 & 모바일 친화적 레이아웃)
st.set_page_config(
    page_title="세스코 환경위생 솔루션 견적·제안 시스템",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모던 프리미엄 스타일 CSS 주입
st.markdown("""
<style>
    /* 전체 폰트 및 배경 감성 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 헤더 배너 스타일 */
    .hero-banner {
        background: linear-gradient(135deg, #0f4c81 0%, #002b49 100%);
        padding: 24px 28px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(0,43,73,0.15);
    }
    .hero-banner h1 {
        font-size: 24px;
        font-weight: 700;
        margin: 0 0 6px 0;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        font-size: 14px;
        color: #b0cbe2;
        margin: 0;
    }

    /* 카드형 컨테이너 */
    .section-card {
        background: #ffffff;
        border: 1px solid #eef2f6;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    .section-title {
        font-size: 17px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 8px;
    }

    /* 메인 강조 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #0072ce 0%, #0f4c81 100%);
        color: white !important;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 16px;
        box-shadow: 0 4px 14px rgba(0, 114, 206, 0.3);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 114, 206, 0.4);
    }

    /* PDF 다운로드 버튼 스타일 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 14px 24px;
        font-size: 16px;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }

    /* Streamlit 기본 여백 최적화 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# 상단 배너 타이틀
st.markdown("""
<div class="hero-banner">
    <h1>🛡️ CESCO Solution Suite</h1>
    <p>현장 맞춤형 환경위생 진단 및 One-Stop 견적 제안서 생성 시스템</p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.markdown('<div class="section-card"><div class="section-title">📍 1. 기본 정보 & 업종 선택</div>', unsafe_allow_html=True)
    client_name = st.text_input("업체명 / 고객명", placeholder="예: 연세바른병원, 스타벅스 강남점, 홍길동 고객님")
    
    biz_type = st.selectbox(
        "업종 구분 (AI 진단 프롬프트에 자동 반영)",
        ["병원 / 의원 / 클리닉", "일반 음식점 / 카페", "사무실 / 오피스", "어린이집 / 학원", "호텔 / 숙박시설", "물류 / 제조 시설", "기타 사업장"]
    )
    
    uploaded_photo = st.file_uploader("📸 현장 전경/문제 구역 사진 (선택)", type=["jpg", "jpeg", "png"])
    if uploaded_photo:
        st.session_state["uploaded_photo"] = uploaded_photo.read()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">🔍 2. 현장 환경 진단 (원클릭 체크)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        chk_drain = st.checkbox("하수구 / 배관 악취")
        chk_mold = st.checkbox("습기 · 곰팡이 냄새")
        chk_food = st.checkbox("음식물 / 유기물 부패취")
    with c2:
        chk_toilet = st.checkbox("화장실 요석 / 암모니아")
        chk_chem = st.checkbox("소독약 / 화학 약품취")
        chk_vent = st.checkbox("환기 부족 / 밀폐 답답함")

    diagnosis_memo = st.text_area("추가 특이사항 메모", placeholder="예: 주방 환기 불량, 여성 고객 중심 매장으로 향기 케어 필수 등", height=70)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">⚙️ 3. 설치 구역 및 솔루션 기기 설정</div>', unsafe_allow_html=True)
    
    if "rows" not in st.session_state:
        st.session_state["rows"] = [{"area": "홀 / 메인 공간", "device": "에어제닉 (자동분사 탈취기)", "cycle": "1개월", "fee": 35000}]

    def add_row():
        st.session_state["rows"].append({"area": "신규 구역", "device": "UV 파워 공기살균기", "cycle": "1개월", "fee": 45000})

    for idx, row in enumerate(st.session_state["rows"]):
        r1, r2, r3, r4 = st.columns([1.2, 1.8, 1.0, 1.2])
        row["area"] = r1.text_input(f"구역 #{idx+1}", row["area"], key=f"area_{idx}")
        row["device"] = r2.selectbox(f"설비 #{idx+1}", ["에어제닉 (자동분사 탈취기)", "UV 파워 공기살균기", "센스후레쉬 (소변기 케어)", "스마트 피톤치드 디퓨저", "실내 해충 안심 솔루션"], index=0, key=f"dev_{idx}")
        row["cycle"] = r3.selectbox(f"관리주기 #{idx+1}", ["1개월", "2개월", "3개월", "특약관리"], index=0, key=f"cyc_{idx}")
        row["fee"] = r4.number_input(f"월 관리비 #{idx+1}", value=row["fee"], step=1000, key=f"fee_{idx}")

    st.button("➕ 설치 구역/기기 추가", on_click=add_row)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">🎁 4. 프로모션 및 결제 조건</div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        initial_cost = st.number_input("초기 설치비 / 가입비 (원)", value=0, step=10000)
        promo_discount = st.text_input("약정 할인 조건", value="36개월 약정 기준 (설치비 전액 면제)")
    with p2:
        free_gift = st.text_input("특별 증정 혜택", value="향기 리필용 카트리지 1팩 무상 증정")
        special_terms = st.text_input("결제 방식 안내", value="자동이체 / 법인카드 결제 가능 (VAT 별도)")
    st.markdown('</div>', unsafe_allow_html=True)

    generate_btn = st.button("✨ AI 맞춤 제안서 자동 생성 및 견적 확정", use_container_width=True)

with col_right:
    st.markdown('<div class="section-card"><div class="section-title">📋 5. 제안서 실시간 검토 및 PDF 발급</div>', unsafe_allow_html=True)
    
    if generate_btn:
        if not client_name:
            st.warning("⚠️ 고객(업체)명을 먼저 입력해 주세요.")
        else:
            with st.spinner("🤖 DeepSeek AI가 맞춤형 환경 솔루션을 분석 중입니다..."):
                # 진단 체크 목록 정리
                active_issues = []
                if chk_drain: active_issues.append("하수구 악취")
                if chk_mold: active_issues.append("습기/곰팡이")
                if chk_food: active_issues.append("유기물 부패취")
                if chk_toilet: active_issues.append("화장실 요석취")
                if chk_chem: active_issues.append("약품 냄새")
                if chk_vent: active_issues.append("환기 부족")
                
                # 견적 합계 계산
                total_monthly = sum(r["fee"] for r in st.session_state["rows"])
                
                summary_rows = []
                for r in st.session_state["rows"]:
                    summary_rows.append({
                        "label": f"{r['area']} - {r['device']} ({r['cycle']})",
                        "price_display": f"{r['fee']:,}원 / 월"
                    })
                
                # AI 제안 콘텐츠 생성
                ai_result = generate_proposal_content(
                    client_name=client_name,
                    biz_type=biz_type,
                    issues=active_issues,
                    memo=diagnosis_memo,
                    devices=[r["device"] for r in st.session_state["rows"]]
                )
                
                st.session_state["proposal_data"] = {
                    "client_name": client_name,
                    "biz_type": biz_type,
                    "date": datetime.now().strftime("%Y년 %m월 %d일"),
                    "diagnosis_alert": ai_result.get("diagnosis_alert", "쾌적하고 위생적인 공간 환경 유지를 위한 맞춤 케어가 필요합니다."),
                    "solution_plan": ai_result.get("solution_plan", "구역별 최적 기기 배치 및 정기 관리를 통해 냄새 원인을 근본적으로 제거합니다."),
                    "effect_points": ai_result.get("effect_points", ["실내 공기질 정화 및 바이러스 차단", "고객 및 임직원 만족도 향상", "브랜드 신뢰도 증대"]),
                    "summary_rows": summary_rows,
                    "total_monthly": f"{total_monthly:,}원",
                    "initial_cost": f"{initial_cost:,}원" if initial_cost > 0 else "무상 (프로모션 적용)",
                    "promo_discount": promo_discount,
                    "free_gift": free_gift,
                    "special_terms": special_terms,
                    "footer_notice": "※ 본 견적서는 세스코 환경위생 관리 표준 규정에 의해 발행되었으며 유효기간은 발행일로부터 30일입니다."
                }
                st.success("🎉 제안서가 성공적으로 생성되었습니다!")

    if "proposal_data" in st.session_state:
        data = st.session_state["proposal_data"]
        
        st.info(f"**[{data['client_name']}] 맞춤 솔루션 브리핑**\n\n{data['diagnosis_alert']}")
        
        with st.expander("📌 상세 솔루션 구성 및 견적 요약", expanded=True):
            st.markdown(f"**솔루션 계획:** {data['solution_plan']}")
            st.markdown("---")
            for row in data["summary_rows"]:
                st.write(f"• {row['label']}: **{row['price_display']}**")
            st.markdown(f"**총 월 관리비:** `{data['total_monthly']}` (VAT 별도)")
            st.markdown(f"**프로모션:** {data['promo_discount']} / **혜택:** {data['free_gift']}")

        try:
            pdf_bytes = build_pdf(data, st.session_state.get("uploaded_photo"))
            st.download_button(
                label="📄 A4 제안서 PDF 즉시 다운로드",
                data=pdf_bytes,
                file_name=f"{client_name}_환경솔루션제안서_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF 렌더링 오류: {e}")
    else:
        st.info("👈 좌측에서 정보를 입력하고 생성 버튼을 누르면 실시간 미리보기와 PDF 발급 버튼이 활성화됩니다.")
        
    st.markdown('</div>', unsafe_allow_html=True)
