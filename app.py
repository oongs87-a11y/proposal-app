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
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #002b49 0%, #0f4c81 100%);
        padding: 20px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0,43,73,0.15);
    }
    .main-header h1 {
        font-size: 22px;
        font-weight: 700;
        margin: 0;
        color: #ffffff !important;
    }
    .main-header p {
        font-size: 13px;
        color: #b0cbe2;
        margin: 4px 0 0 0;
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
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
        f"- 구역: {item['zone']} | 제품군: {item['category']} | 제품명: {item['device']} | 수량: {item['qty']}대 | 방문주기: {item.get('cycle', '')} | 상세사양: {item['scent']} | 프로모션: {item.get('promo_text', '')}"
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
    1. `diagnosis_alert`: 업종 특성과 악취 요인을 결합한 1줄 진단명 작성
    2. `diagnosis_description`: {biz_type} 맞춤형 전문 진단 요약(2-3줄) 작성
    3. `care_solutions`: 기기별 방문주기와 세스코 정기 관리 3단계 작성
    4. `expected_values`: 좌측 하단용 {biz_type} 맞춤형 핵심 도입 효과 2~3개 작성
    5. `space_guides`: 각 구역별 도입 필요성과 기대 효과를 1~2줄씩 명확하게 작성
    6. `footer_notice`: 사은품 증정 내역, 설치비 면제, 약정 조건, 부가세/정기 케어 포함 여부를 고객이 읽기 쉬운 정식 공지 문장으로 매끄럽게 완성

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
        "footer_notice": "본 견적은 프로모션 적용 한정 조건이며, 모든 금액에는 부가세 및 세스코 전문 마스터의 정기 방문 케어와 소모품 비용이 포함되어 있습니다."
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
<div class="main-header">
    <h1>🛡️ CESCO 환경 솔루션 제안·견적 시스템</h1>
    <p>현장 진단부터 맞춤형 솔루션 견적서 즉시 발행</p>
</div>
""", unsafe_allow_html=True)

if "installed_items" not in st.session_state:
    st.session_state["installed_items"] = []

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. 기본 정보 & 업종 선택")
    client_name = st.text_input("업체명/고객명", placeholder="예: 연세바른병원, 스타벅스 압구정점, 홍길동 고객님 등")
    biz_type = st.selectbox("업종 선택 (업종별 맞춤 설명 자동 생성)", BUSINESS_TYPES)
    
    uploaded_photo = st.file_uploader("현장 전경 사진 업로드", type=["jpg", "jpeg", "png"])
    if uploaded_photo:
        st.image(uploaded_photo, caption="선택한 현장 사진", width=260)

    st.markdown("---")
    st.subheader("2. 현장 진단 (원클릭 체크)")
    st.caption("※ 체크할 내용이 없다면 바로 아래 특이사항 메모에 적어주세요.")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        c1 = st.checkbox("하수구/배관 악취", value=False)
        c2 = st.checkbox("습기·곰팡이 냄새", value=False)
        c3 = st.checkbox("음식물/유기물 부패취", value=False)
    with col_chk2:
        c4 = st.checkbox("화장실 요석/암모니아취", value=False)
        c5 = st.checkbox("소독약/화학 약품 냄새", value=False)
        c6 = st.checkbox("환기 부족/밀폐 답답함", value=False)

    selected_odors = []
    if c1: selected_odors.append("하수구 냄새")
    if c2: selected_odors.append("습기·곰팡이 냄새")
    if c3: selected_odors.append("음식물 부패취")
    if c4: selected_odors.append("화장실 요석 악취")
    if c5: selected_odors.append("소독약 냄새")
    if c6: selected_odors.append("환기 부족 복합취")

    custom_notes = st.text_input(
        "추가 특이사항 메모", 
        placeholder="체크할 내용이 없으면 이곳에 적어주세요 (예: 주방 환기 부족, 여성 고객 위주 등)"
    )

    st.markdown("---")
    st.subheader("3. 설치 구역 및 기기·가격 추가")
    
    with st.form("item_add_form", clear_on_submit=True):
        f_zone = st.text_input("설치 구역명", placeholder="예: 메인 홀, 주방, 진료실, 탈의실 등")
        
        c_cat_col, c_cycle_col = st.columns([1, 1])
        with c_cat_col:
            f_cat = st.selectbox("제품군 선택", CATEGORIES)
        with c_cycle_col:
            f_cycle = st.selectbox("방문주기 선택", VISIT_CYCLES, index=0)
            
        f_dev = st.text_input("제품 이름 (직접 입력)", placeholder="예: 판테온 트루살균 20평형, 에어퍼퓸200 등")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            f_qty = st.number_input("수량(대)", min_value=1, max_value=50, value=1)
        with c_p2:
            f_orig = st.number_input("정상가(대당/월)", min_value=0, value=0, step=1000)
        with c_p3:
            f_sale = st.number_input("할인가(대당/월)", min_value=0, value=0, step=1000)

        f_spec = st.text_input("선택 조향 / 상세 사양 (선택)", placeholder="예: 프리지아 향, 살균 케어, 썸머 향")
        f_promo_note = st.text_input("개별 프로모션 문구 (선택)", placeholder="예: 9개월 렌탈료 반값, 4개월 반값 프로모션")
        
        add_btn = st.form_submit_button("➕ 목록에 추가하기", use_container_width=True)
        
        if add_btn:
            if not f_dev:
                st.error("제품 이름을 입력해 주세요.")
            else:
                zone_final = f_zone if f_zone.strip() else "공용 공간"
                
                spec_parts = []
                if f_cycle not in ["해당없음", "상시/직접관리"]:
                    spec_parts.append(f_cycle)
                if f_spec.strip():
                    spec_parts.append(f_spec.strip())
                
                final_scent_spec = " / ".join(spec_parts) if spec_parts else "표준 케어 사양"

                st.session_state["installed_items"].append({
                    "zone": zone_final,
                    "category": f_cat,
                    "cycle": f_cycle,
                    "device": f_dev,
                    "qty": f_qty,
                    "orig_price": f_orig,
                    "sale_price": f_sale,
                    "scent": final_scent_spec,
                    "raw_spec": f_spec.strip(),
                    "promo_text": f_promo_note.strip()
                })
                st.rerun()

    if st.session_state["installed_items"]:
        st.write("**현재 설계된 기기 및 견적 목록:**")
        total_orig_calc = 0
        total_sale_calc = 0
        for idx, item in enumerate(st.session_state["installed_items"]):
            item_orig_sum = item["orig_price"] * item["qty"]
            item_sale_sum = item["sale_price"] * item["qty"]
            total_orig_calc += item_orig_sum
            total_sale_calc += item_sale_sum

            c_i1, c_i2 = st.columns([5, 1])
            with c_i1:
                st.markdown(f"**[{item['zone']}]** {item['device']} ({item['qty']}대) | 정상 {item_orig_sum:,}원 ➔ **할인 {item_sale_sum:,}원**")
                sub_infos = []
                if item.get("scent"):
                    sub_infos.append(f"⚙️ **사양/주기:** `{item['scent']}`")
                if item.get("promo_text"):
                    sub_infos.append(f"🎁 **프로모션:** <span style='color:#e11d48; font-weight:bold;'>{item['promo_text']}</span>")
                if sub_infos:
                    st.markdown("&nbsp;&nbsp;└ " + " | ".join(sub_infos), unsafe_allow_html=True)

            with c_i2:
                if st.button("삭제", key=f"del_{idx}"):
                    st.session_state["installed_items"].pop(idx)
                    st.rerun()

    st.markdown("---")
    st.subheader("4. 영업 특약 및 프로모션 안내 (사은품 / 계약조건 자유 기재)")
    promo_notes = st.text_area(
        "사은품, 결제 플로우, 프로모션 특약 자유 메모",
        placeholder="현장에서 제공하는 혜택을 편하게 적어주세요.\n\n예시 1:\n- 계약 시 손소독제 2세트 사은품 무상 증정\n- 초기 설치비/가입비 전액 면제 혜택\n\n예시 2:\n- 9개월 렌탈료 반값 프로모션 적용\n- 핸드제닉 손세정제 사은품 제공",
        height=120
    )

    generate_btn = st.button("🚀 맞춤 제안서 자동 생성", use_container_width=True, type="primary")

if generate_btn:
    if not client_name or not st.session_state["installed_items"]:
        st.warning("업체명과 기기를 최소 1개 이상 입력해 주세요.")
    else:
        with st.spinner(f"AI가 [{biz_type}] 업종에 맞춤화된 특약 제안서를 작성 중입니다..."):
            try:
                ai_data = call_deepseek_smart(client_name, biz_type, selected_odors, custom_notes, st.session_state["installed_items"], promo_notes)
                
                pricing_blocks = []
                total_sale_sum = 0
                has_any_promo = False
                for item in st.session_state["installed_items"]:
                    sum_sale = item["sale_price"] * item["qty"]
                    sum_orig = item["orig_price"] * item["qty"]
                    total_sale_sum += sum_sale
                    if item.get("promo_text"):
                        has_any_promo = True
                    
                    pricing_blocks.append({
                        "product_name": f"{item['device']} ({item['qty']}대)",
                        "original_price": f"{sum_orig:,}원" if sum_orig > 0 else "",
                        "discounted_price": f"{sum_sale:,}원",
                        "promo_text": item.get("promo_text", "")
                    })
                
                ai_data["pricing_blocks"] = pricing_blocks
                ai_data["solution_items"] = st.session_state["installed_items"]
                
                summary_rows = [
                    {"label": "1개월 차 (설치 당월)", "badge": "일할청구", "price_display": "설치일 기준 일할 계산 청구"},
                    {
                        "label": "매월 정기 결제액 (VAT 포함)",
                        "badge": "프로모션 적용" if (has_any_promo or promo_notes.strip()) else "할인가",
                        "price_display": f"월 {total_sale_sum:,}원"
                    }
                ]
                
                if "사은" in promo_notes or "증정" in promo_notes:
                    for line in promo_notes.split("\n"):
                        if "사은" in line or "증정" in line:
                            clean_gift = line.replace("-", "").strip()
                            summary_rows.append({
                                "label": "계약 사은 혜택",
                                "badge": "사은품",
                                "price_display": clean_gift
                            })
                            break
                            
                ai_data["summary_rows"] = summary_rows
                
                st.session_state["proposal_data"] = ai_data
                st.session_state["uploaded_photo_bytes"] = uploaded_photo.getvalue() if uploaded_photo else None
                st.success("제안서 자동 완성 성공!")
            except Exception as e:
                st.error(f"생성 실패: {e}")

with col2:
    st.subheader("2. 제안서 미리보기 및 PDF 발급")
    if "proposal_data" in st.session_state:
        data = st.session_state["proposal_data"]
        
        st.markdown(f"### {data.get('client_name')} 제안서 ({biz_type})")
        st.info(f"**진단 요약:** {data.get('diagnosis_alert')}")
        
        with st.expander("📌 결제 요약 및 안내사항 미리보기", expanded=True):
            for row in data.get("summary_rows", []):
                st.write(f"- {row.get('label')}: **{row.get('price_display')}** ({row.get('badge', '')})")
            st.markdown("---")
            st.write("**하단 안내 박스 문구:**")
            st.info(data.get("footer_notice"))

        try:
            pdf_bytes = build_pdf(data, st.session_state.get("uploaded_photo_bytes"))
            st.download_button(
                label="📥 A4 제안서 PDF 즉시 다운로드",
                data=pdf_bytes,
                file_name=f"{client_name}_환경솔루션_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF 렌더링 에러: {e}")
    else:
        st.info("좌측에 정보를 입력하고 생성 버튼을 누르면 다운로드 버튼이 활성화됩니다.")
