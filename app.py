import os
import io
import json
import base64
import subprocess
from datetime import datetime
import streamlit as st
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

@st.cache_resource
def ensure_playwright_installed():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        pass

ensure_playwright_installed()

st.set_page_config(
    page_title="현장 세스코 솔루션 제안·견적기",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        background-color: #f8fafc;
        color: #1e293b;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1200px !important;
    }

    .hero-header {
        background: linear-gradient(135deg, #0b2545 0%, #133c55 50%, #1e5f74 100%);
        border-radius: 16px;
        padding: 28px 32px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(11, 37, 69, 0.2), 0 8px 10px -6px rgba(11, 37, 69, 0.1);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-header::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(0, 168, 232, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #90e0ef;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .hero-title {
        font-size: 24px !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        color: #ffffff !important;
        margin: 0 0 6px 0 !important;
    }
    .hero-sub {
        font-size: 13px !important;
        color: #cbd5e1 !important;
        font-weight: 400;
        margin: 0 !important;
    }

    .premium-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
    }
    .card-label {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea textarea {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: #0077b6 !important;
        box-shadow: 0 0 0 3px rgba(0, 119, 182, 0.15) !important;
        background-color: #ffffff !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0077b6 0%, #0096c7 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 20px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0, 119, 182, 0.3) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(0, 119, 182, 0.4) !important;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 20px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        transition: transform 0.15s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
    }

    .item-list-row {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0077b6;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

CATEGORIES = [
    "공기살균기", "공기청정기", "정수기", "비데", 
    "VBC", "향사업군", "FIC(포충등·에어커튼)", "기타(핸드드라이어 등)"
]

BUSINESS_TYPES = [
    "병원 / 의원 / 클리닉",
    "식음료 / 카페 / 베이커리 / 레스토랑",
    "피트니스 / 헬스장 / 필라테스",
    "사무실 / 기업 오피스",
    "학원 / 스터디카페 / 교육시설",
    "미용실 / 네일샵 / 에스테틱",
    "호텔 / 모텔 / 숙박시설",
    "일반 상가 / 매장 / 기타"
]

VISIT_CYCLES = [
    "1개월 주기",
    "2개월 주기",
    "3개월 주기",
    "4개월 주기",
    "6개월 주기",
    "12개월 주기",
    "연 9회 주기",
    "연 6회 주기",
    "상시/직접관리",
    "해당없음"
]

COMMITMENT_PERIODS = ["36개월", "60개월", "72개월"]
CONTRACT_PERIODS = ["60개월", "72개월", "해당없음"]

PROMO_DISCOUNT_TYPES = ["선택안함", "렌탈료 반값", "렌탈료 면제", "결합할인 적용", "특별 프로모션 적용"]
PROMO_MONTH_LIST = ["선택안함"] + [f"{i}개월" for i in range(1, 13)]

def get_deepseek_api_key():
    if "DEEPSEEK_API_KEY" in st.secrets:
        return st.secrets["DEEPSEEK_API_KEY"]
    return os.environ.get("DEEPSEEK_API_KEY", "")

def call_deepseek_smart(client_name: str, biz_type: str, odor_types: list, custom_notes: str, selected_items: list, custom_promo_text: str) -> dict:
    client = OpenAI(
        api_key=get_deepseek_api_key(),
        base_url="https://api.deepseek.com"
    )

    items_text = "\n".join([
        f"- 구역: {item['zone']} | 제품군: {item['category']} | 제품명: {item['device']} | 수량: {item['qty']}대 | 색상: {item.get('color', '기본')} | 약정기간: {item.get('commitment', '')} | 계약기간: {item.get('contract', '')} | 방문주기: {item.get('cycle', '')} | 상세사양: {item['scent']} | 프로모션: {item.get('promo_text', '')}"
        for item in selected_items
    ])

    odor_str = ", ".join(odor_types) if odor_types else "특이사항 메모 참조"

    prompt = f"""
    당신은 CESCO 환경 위생 솔루션 최고 영업 컨설턴트입니다.
    사용자가 입력한 정보와 [영업 특약 및 프로모션 안내]를 꼼꼼히 분석하여 고객이 한눈에 혜택을 이해할 수 있는 1페이지 제안서 JSON을 작성하세요.

    [고객사명]: {client_name}
    [업종 구분]: {biz_type}
    [현장 확인 요인]: {odor_str}
    [추가 특이사항]: {custom_notes}
    [설계 기기 목록]:
    {items_text}
    [영업 특약 / 사은품 / 프로모션 메모]:
    {custom_promo_text}

    ★ 작성 요구사항:
    1. `diagnosis_alert`: 업종 특성과 악취/향기 요인을 결합한 1줄 진단명 작성
    2. `diagnosis_description`: {biz_type} 맞춤형 전문 진단 요약(2-3줄) 작성
    3. `care_solutions`: 기기별 방문주기와 세스코 정기 관리 3단계 작성
    4. `expected_values`: 좌측 하단용 {biz_type} 맞춤형 핵심 도입 효과 2~3개 작성
    5. `space_guides`: 각 구역별 도입 필요성과 기대 효과를 1~2줄씩 명확하게 작성
    6. `footer_notice`: 약정/계약조건, 사은품 증정 내역, 설치비 무상 지원, 부가세 포함/정기 케어 포함 여부를 고객이 읽기 쉬운 정식 공지 문장으로 매끄럽게 완성

    반드시 마크다운 없이 순수 JSON 포맷으로만 응답하세요:
    {{
        "header_subtag": "CESCO ENVIRONMENTAL CARE CONSULTING",
        "client_name": "{client_name}",
        "header_description": "쾌적하고 안전한 공간 조성을 위한 맞춤형 환경 위생 솔루션 제안",
        "diagnosis_alert": "현장 진단 요약: {odor_str}",
        "diagnosis_description": "종합적인 환경 진단을 통해 도출된 문제점을 해결하고 공간의 위생과 브랜드 만족도를 극대화하는 맞춤 솔루션을 제안합니다.",
        "care_solutions": [
            {{"icon": "🔄", "title": "주기적 정기 방문 관리", "desc": "세스코 전문 마스터의 정밀 점검 및 기기 관리"}},
            {{"icon": "🧪", "title": "전용 소모품/케미컬 정품 교체", "desc": "주기에 맞춘 정품 필터·케미컬 교체 및 클리닝"}},
            {{"icon": "🛡️", "title": "공간별 최적 위생 밸런스 유지", "desc": "환경 변화에 맞춘 세심한 발향 및 위생 제어"}}
        ],
        "expected_values": [
            {{"title": "🌟 프리미엄 브랜드 이미지 구축", "desc": "입구부터 화장실까지 이어지는 완벽한 청결 관리로 고객 신뢰도 제고"}},
            {{"title": "🛡️ 24시간 실시간 위생·안전 케어", "desc": "상시 공기 살균 및 유해 세균 분해를 통한 안심 공간 조성"}}
        ],
        "space_guides": [
            {{"zone": "구역명", "desc": "해당 기기가 이 공간에 필요한 명확한 이유와 설치 후 기대 효과"}}
        ],
        "footer_notice": "본 제안서는 부가세가 포함되어 있으며 초기 설치비는 무상 지원됩니다. 세스코 전문 마스터의 정기 방문 케어 및 소모품 비용이 포함되어 있습니다."
    }}
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a professional proposal generator. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    return json.loads(response.choices[0].message.content)

def build_pdf(data: dict, uploaded_photo_bytes=None) -> bytes:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("template.html")
    
    photo_b64 = None
    if uploaded_photo_bytes:
        photo_b64 = base64.b64encode(uploaded_photo_bytes).decode("utf-8")

    html_content = template.render(data=data, photo_base64=photo_b64)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 794, "height": 1123})
        page.set_content(html_content, wait_until="networkidle")
        
        pdf_bytes = page.pdf(
            width="210mm",
            height="297mm",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        browser.close()
        
    return pdf_bytes

st.markdown("""
<div class="hero-header">
    <div class="hero-badge">CESCO PROFESSIONAL CARE</div>
    <div class="hero-title">🛡️ 세스코 환경 솔루션 견적·제안 시스템</div>
    <div class="hero-sub">현장 정밀 진단부터 맞춤형 패키지 견적서 발행까지 원스톱 지원</div>
</div>
""", unsafe_allow_html=True)

if "installed_items" not in st.session_state:
    st.session_state["installed_items"] = []

col1, col2 = st.columns([1.05, 0.95], gap="large")

with col1:
    st.markdown('<div class="premium-card"><div class="card-label">🏢 1. 기본 정보 & 컨설턴트 정보</div>', unsafe_allow_html=True)
    client_name = st.text_input("업체명 / 고객명", placeholder="예: (주)에이비씨컴퍼니, 늘푸른의원 등")
    biz_type = st.selectbox("업종 선택 (업종별 맞춤 설명 자동 생성)", BUSINESS_TYPES)
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        manager_name = st.text_input("세스코 담당자명", placeholder="예: 홍길동 팀장")
    with c_m2:
        manager_phone = st.text_input("담당자 연락처", placeholder="예: 010-1234-5678")

    st.markdown("<p style='font-size:13px; font-weight:700; margin:14px 0 2px 0; color:#1e293b;'>📸 현장 전경 사진 업로드 (선택)</p>", unsafe_allow_html=True)
    st.caption("⚠️ **가로 비율(4:3 또는 16:9) 사진 권장** (세로로 긴 사진은 제안서에서 잘려 보일 수 있습니다)")
    uploaded_photo = st.file_uploader("사진 파일 선택", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if uploaded_photo:
        st.image(uploaded_photo, caption="선택된 현장 사진", width=260)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="premium-card"><div class="card-label">🔍 2. 현장 환경 정밀 진단</div>', unsafe_allow_html=True)
    st.caption("※ 현장 상황에 해당하는 항목을 체크해 주세요.")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        c1 = st.checkbox("하수구 / 배관 악취", value=False)
        c2 = st.checkbox("습기 · 곰팡이 냄새", value=False)
        c3 = st.checkbox("음식물 / 유기물 부패취", value=False)
        c7 = st.checkbox("향기 컨설팅 필요", value=False)
    with col_chk2:
        c4 = st.checkbox("화장실 요석 / 암모니아취", value=False)
        c5 = st.checkbox("소독약 / 화학 약품 냄새", value=False)
        c6 = st.checkbox("환기 부족 / 밀폐 답답함", value=False)

    selected_odors = []
    if c1: selected_odors.append("하수구 냄새")
    if c2: selected_odors.append("습기·곰팡이 냄새")
    if c3: selected_odors.append("음식물 부패취")
    if c4: selected_odors.append("화장실 요석 악취")
    if c5: selected_odors.append("소독약 냄새")
    if c6: selected_odors.append("환기 부족 복합취")
    if c7: selected_odors.append("공간 향기 컨설팅 및 발향 케어")

    custom_notes = st.text_input(
        "추가 특이사항 메모", 
        placeholder="체크 외 특이사항 (예: 주방 환기 불량, 여성 고객 중심 공간 등)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="premium-card"><div class="card-label">⚙️ 3. 설치 구역 및 기기·조건 설정</div>', unsafe_allow_html=True)
    
    with st.form("item_add_form", clear_on_submit=True):
        f_zone = st.text_input("설치 구획명", placeholder="예: 메인 홀, 원장실, 남/여 화장실 등")
        
        c_cat_col, c_cycle_col = st.columns([1, 1])
        with c_cat_col:
            f_cat = st.selectbox("제품군 선택", CATEGORIES)
        with c_cycle_col:
            f_cycle = st.selectbox("방문주기 선택", VISIT_CYCLES, index=0)

        c_comm_col, c_cont_col = st.columns([1, 1])
        with c_comm_col:
            f_commitment = st.selectbox("약정기간 선택", COMMITMENT_PERIODS, index=0)
        with c_cont_col:
            f_contract = st.selectbox("계약기간 선택", CONTRACT_PERIODS, index=0)
            
        c_dev_col, c_color_col = st.columns([2, 1])
        with c_dev_col:
            f_dev = st.text_input("제품 이름 (직접 입력)", placeholder="예: 판테온 트루살균 20평형, 에어퍼퓸200")
        with c_color_col:
            f_color = st.text_input("제품 색상", placeholder="예: 화이트, 블랙")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            f_qty = st.number_input("수량(대)", min_value=1, max_value=50, value=1)
        with c_p2:
            f_orig = st.number_input("정상가(대당/월)", min_value=0, value=0, step=1000)
        with c_p3:
            f_sale = st.number_input("할인가(대당/월)", min_value=0, value=0, step=1000)

        f_spec = st.text_input("선택 조향 / 상세 사양 (선택)", placeholder="예: 프리지아, 901 썸머")
        
        st.markdown("<p style='font-size:12.5px; font-weight:700; margin:8px 0 4px 0; color:#334155;'>개별 프로모션 조건 선택 (선택)</p>", unsafe_allow_html=True)
        c_pr_m, c_pr_t = st.columns([1, 1])
        with c_pr_m:
            f_promo_month = st.selectbox("프로모션 개월수", PROMO_MONTH_LIST, index=0)
        with c_pr_t:
            f_promo_type = st.selectbox("할인 혜택 구분", PROMO_DISCOUNT_TYPES, index=0)

        f_promo_custom = st.text_input("기타 프로모션 직접 입력 (선택)", placeholder="직접 기재할 프로모션이 있는 경우만 작성 (예: 보증금 면제)")
        
        add_btn = st.form_submit_button("➕ 기기 목록에 추가", use_container_width=True)
        
        if add_btn:
            if not f_dev:
                st.error("제품 이름을 입력해 주세요.")
            else:
                zone_final = f_zone if f_zone.strip() else "공용 공간"
                
                spec_parts = []
                if f_commitment:
                    spec_parts.append(f"약정 {f_commitment}")
                if f_contract and f_contract != "해당없음":
                    spec_parts.append(f"계약 {f_contract}")
                if f_color.strip():
                    spec_parts.append(f"색상: {f_color.strip()}")
                if f_cycle not in ["해당없음", "상시/직접관리"]:
                    spec_parts.append(f_cycle)
                if f_spec.strip():
                    spec_parts.append(f_spec.strip())
                
                final_scent_spec = " / ".join(spec_parts) if spec_parts else "표준 케어 사양"

                final_promo_str = ""
                if f_promo_type != "선택안함" and f_promo_month != "선택안함":
                    final_promo_str = f"{f_promo_month} {f_promo_type}"
                elif f_promo_type != "선택안함":
                    final_promo_str = f"{f_promo_type}"
                elif f_promo_month != "선택안함":
                    final_promo_str = f"{f_promo_month} 프로모션"

                if f_promo_custom.strip():
                    if final_promo_str:
                        final_promo_str += f" / {f_promo_custom.strip()}"
                    else:
                        final_promo_str = f_promo_custom.strip()

                st.session_state["installed_items"].append({
                    "zone": zone_final,
                    "category": f_cat,
                    "cycle": f_cycle,
                    "commitment": f_commitment,
                    "contract": f_contract,
                    "color": f_color.strip(),
                    "device": f_dev,
                    "qty": f_qty,
                    "orig_price": f_orig,
                    "sale_price": f_sale,
                    "scent": final_scent_spec,
                    "raw_spec": f_spec.strip(),
                    "promo_text": final_promo_str
                })
                st.rerun()

    if st.session_state["installed_items"]:
        st.markdown("<p style='font-size:13px; font-weight:700; margin:12px 0 6px 0;'>📋 설계된 기기 내역</p>", unsafe_allow_html=True)
        total_orig_calc = 0
        total_sale_calc = 0
        for idx, item in enumerate(st.session_state["installed_items"]):
            item_orig_sum = item["orig_price"] * item["qty"]
            item_sale_sum = item["sale_price"] * item["qty"]
            total_orig_calc += item_orig_sum
            total_sale_calc += item_sale_sum

            c_i1, c_i2 = st.columns([5, 1])
            with c_i1:
                color_text = f" <span style='color:#64748b;'>({item['color']})</span>" if item.get("color") else ""
                orig_show = f"<span style='text-decoration:line-through; color:#94a3b8; margin-right:6px;'>월 {item_orig_sum:,}원</span>" if item_orig_sum > 0 else ""
                st.markdown(f"""
                <div class="item-list-row">
                    <div style="font-weight:700; font-size:14px; color:#0f172a;">
                        [{item['zone']}] {item['device']}{color_text} · {item['qty']}대
                        <span style="float:right; font-weight:700; color:#0077b6;">{orig_show}월 {item_sale_sum:,}원</span>
                    </div>
                    <div style="font-size:12px; color:#64748b; margin-top:4px;">
                        ⚙️ {item.get('scent', '')}
                    </div>
                    {f'<div style="font-size:12px; color:#e11d48; font-weight:600; margin-top:2px;">🎁 {item["promo_text"]}</div>' if item.get("promo_text") else ''}
                </div>
                """, unsafe_allow_html=True)

            with c_i2:
                if st.button("삭제", key=f"del_{idx}"):
                    st.session_state["installed_items"].pop(idx)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="premium-card"><div class="card-label">🎁 4. 영업 특약 & 프로모션 설정</div>', unsafe_allow_html=True)
    st.caption("※ 기본 혜택(부가세 포함, 설치비 무상 지원)은 정식 공지문으로 자동 포함됩니다.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        opt_vat = st.checkbox("부가세(VAT) 포함 안내", value=True)
        opt_install = st.checkbox("초기 설치비/가입비 무상 지원", value=True)
    with col_b2:
        opt_banner = st.checkbox("세스코 공식 홍보용 배너 지급", value=True)
        opt_care = st.checkbox("정기 방문 케어 및 소모품비 포함", value=True)

    promo_notes_custom = st.text_input(
        "추가 사은품 / 특별 혜택 직접 입력 (선택)",
        placeholder="예: 계약 체결 시 손소독제 2세트 무상 증정"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    generate_btn = st.button("🚀 AI 맞춤 제안서 자동 생성", use_container_width=True, type="primary")

if generate_btn:
    if not client_name or not st.session_state["installed_items"]:
        st.warning("⚠️ 업체명과 기기를 최소 1개 이상 입력해 주세요.")
    else:
        with st.spinner(f"⚡ [이웅희 AI] 가동 중... [{biz_type}] 업종 전용 솔루션을 칼같이 뽑아내고 있습니다! 🤖"):
            try:
                promo_bullet_list = []
                if opt_banner:
                    promo_bullet_list.append("세스코 홍보용 배너 지급")
                if opt_install:
                    promo_bullet_list.append("설치비 무상 지원")
                if opt_vat:
                    promo_bullet_list.append("부가세(VAT) 포함")
                if opt_care:
                    promo_bullet_list.append("정기 방문 케어 및 소모품 무상 제공")
                if promo_notes_custom.strip():
                    promo_bullet_list.append(promo_notes_custom.strip())

                promo_notes_combined = "\n".join([f"- {p}" for p in promo_bullet_list])

                ai_data = call_deepseek_smart(client_name, biz_type, selected_odors, custom_notes, st.session_state["installed_items"], promo_notes_combined)
                
                pricing_blocks = []
                total_sale_sum = 0
                total_orig_sum = 0
                has_any_promo = False
                for item in st.session_state["installed_items"]:
                    sum_sale = item["sale_price"] * item["qty"]
                    sum_orig = item["orig_price"] * item["qty"]
                    total_sale_sum += sum_sale
                    total_orig_sum += sum_orig
                    if item.get("promo_text"):
                        has_any_promo = True
                    
                    prod_name = f"{item['device']} ({item['qty']}대)"
                    if item.get("color"):
                        prod_name = f"{item['device']}({item['color']}) ({item['qty']}대)"
                    
                    pricing_blocks.append({
                        "product_name": prod_name,
                        "original_price": f"{sum_orig:,}원" if sum_orig > 0 else "",
                        "discounted_price": f"{sum_sale:,}원",
                        "promo_text": item.get("promo_text", "")
                    })
                
                ai_data["pricing_blocks"] = pricing_blocks
                ai_data["solution_items"] = st.session_state["installed_items"]
                ai_data["manager_name"] = manager_name.strip()
                ai_data["manager_phone"] = manager_phone.strip()
                
                total_discount_sum = total_orig_sum - total_sale_sum if total_orig_sum > total_sale_sum else 0
                ai_data["total_orig_display"] = f"월 {total_orig_sum:,}원" if total_orig_sum > 0 else ""
                ai_data["total_discount_display"] = f"-{total_discount_sum:,}원" if total_discount_sum > 0 else ""
                ai_data["total_sale_display"] = f"월 {total_sale_sum:,}원"
                
                summary_rows = [
                    {"label": "1개월 차 (설치 당월)", "badge": "일할청구", "price_display": "설치일 기준 일할 계산 청구"}
                ]
                
                if opt_banner:
                    summary_rows.append({
                        "label": "공식 홍보 배너",
                        "badge": "사은품",
                        "price_display": "세스코 홍보용 배너 1개 무상 지원"
                    })
                if promo_notes_custom.strip():
                    summary_rows.append({
                        "label": "특별 계약 혜택",
                        "badge": "사은품",
                        "price_display": promo_notes_custom.strip()
                    })
                            
                ai_data["summary_rows"] = summary_rows
                
                st.session_state["proposal_data"] = ai_data
                st.session_state["uploaded_photo_bytes"] = uploaded_photo.getvalue() if uploaded_photo else None
                st.success("🎉 [이웅희 AI] 제안서 생성 완료! 완벽한 견적이 준비되었습니다.")
            except Exception as e:
                st.error(f"생성 실패: {e}")

with col2:
    st.markdown('<div class="premium-card"><div class="card-label">📄 5. 제안서 미리보기 & PDF 발급</div>', unsafe_allow_html=True)
    if "proposal_data" in st.session_state:
        data = st.session_state["proposal_data"]
        
        st.markdown(f"#### 🏢 {data.get('client_name')} <span style='font-size:14px; font-weight:normal; color:#64748b;'>({biz_type})</span>", unsafe_allow_html=True)
        if data.get("manager_name") or data.get("manager_phone"):
            st.markdown(f"**컨설턴트:** {data.get('manager_name', '')} ({data.get('manager_phone', '')})")
        st.info(f"**🔍 진단 요약:** {data.get('diagnosis_alert')}")
        
        with st.expander("💳 결제 요약 및 특약 사항", expanded=True):
            if data.get("total_orig_display"):
                st.write(f"- 총 정상 렌탈료: **{data.get('total_orig_display')}**")
            if data.get("total_discount_display"):
                st.write(f"- 총 프로모션 할인 혜택: **:red[{data.get('total_discount_display')}]**")
            st.write(f"- 🌟 **최종 매월 정기 결제액: :blue[{data.get('total_sale_display')}]**")
            
            for row in data.get("summary_rows", []):
                st.write(f"- {row.get('label')}: **{row.get('price_display')}** ({row.get('badge', '')})")
            st.markdown("---")
            st.caption(f"**안내:** {data.get('footer_notice')}")

        try:
            pdf_bytes = build_pdf(data, st.session_state.get("uploaded_photo_bytes"))
            st.download_button(
                label="📥 A4 공식 제안서 PDF 다운로드",
                data=pdf_bytes,
                file_name=f"{client_name}_세스코제안서_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF 렌더링 에러: {e}")
    else:
        st.info("👈 좌측에서 고객 정보와 기기를 설정한 후 **'AI 맞춤 제안서 자동 생성'**을 클릭하세요.")
    st.markdown('</div>', unsafe_allow_html=True)
