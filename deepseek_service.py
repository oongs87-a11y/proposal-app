import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def generate_proposal(client_name: str, site_notes: str, promo_notes: str = "") -> dict:
    prompt = f"""
    당신은 프리미엄 공간 케어 및 B2B 제안서 작성 전문가입니다.
    현장 실사 메모와 프로모션 조건을 분석하여 전문적인 1페이지 제안서 JSON을 작성하세요.

    [고객사/의뢰처]: {client_name}
    [현장 실사/진단 메모]:
    {site_notes}
    [프로모션 및 가격 메모]:
    {promo_notes}

    반드시 아래 JSON 포맷을 준수하여 순수 JSON만 출력하세요:
    {{
        "header_subtag": "PREMIUM SPACE CARE & SCENT BRANDING",
        "client_name": "{client_name}",
        "header_title": "공간 향기 & 환경 케어 맞춤 제안서",
        "header_description": "쾌적한 공간 환경 조성 및 브랜드 가치 제고를 위한 솔루션",
        
        "section1_title": "공간 케어의 가치 및 진단",
        "section1_quote": "공간을 들어서는 순간 느껴지는 첫인상이 고객의 신뢰를 결정합니다.",
        "section1_points": [
            {{"title": "✨ 첫인상의 품격 (First Impression)", "desc": "악취 및 유해 환경을 개선하여 맑고 청결한 인상 제공"}},
            {{"title": "🌿 고객 만족 및 심리적 안정", "desc": "치료 및 대기 공간의 쾌적성 극대화"}}
        ],
        
        "section2_title": "정기 케어 & 유지 관리",
        "section2_points": [
            {{"title": "🔄 정기 방문 맞춤 점검", "desc": "주기적 방문을 통한 소모품 교체 및 기기 분사 노즐 정밀 세척"}},
            {{"title": "🎨 환경 맞춤형 향/케어 교체", "desc": "계절 및 내부 환경 변화에 맞춰 최적의 옵션으로 유연한 교체 지원"}}
        ],
        
        "total_units": 7,
        "solution_items": [
            {{"zone": "로비", "device": "에어퍼퓸", "qty": 1, "spec": "오렌지블라썸 향 (발향+소취)"}},
            {{"zone": "복도 진료실라인", "device": "에어제닉", "qty": 2, "spec": "썸머 향 (발향+탈취)"}},
            {{"zone": "진료실 내부", "device": "에어제닉", "qty": 4, "spec": "블라썸 향 (발향+탈취)"}}
        ],
        "solution_benefits": [
            {{"title": "초기 셋팅", "desc": "현장 진단 기반 맞춤 조향 및 설치"}},
            {{"title": "무상 혜택", "desc": "정기 방문 주기마다 기기 점검 및 무상 향 교체 지원"}}
        ],
        
        "pricing_blocks": [
            {{
                "product_name": "에어퍼퓸 (홀/로비 1대)",
                "original_price": 87900,
                "discounted_price": 48900,
                "promo_text": "4개월간 렌탈료 50% 추가 반값 프로모션 (월 24,450원)"
            }},
            {{
                "product_name": "에어제닉 (복도 2대 + 진료실 4대 = 총 6대)",
                "original_price": 167400,
                "discounted_price": 115200,
                "promo_text": "대당 할인가 19,200원 적용"
            }}
        ],
        "summary_rows": [
            {{"label": "1개월 차 (설치 당월)", "badge": "일할계산", "price_display": "설치일 기준 일할 청구"}},
            {{"label": "2~5개월 차 (프로모션 적용)", "badge": "4개월 반값", "price_display": "월 139,650원"}},
            {{"label": "6개월 차 이후 정상 할인가", "badge": "", "price_display": "월 164,100원"}}
        ],
        "footer_notice": "계약 및 프로모션 안내: 한정 프로모션 적용 견적이며, 부가세 및 설치비가 포함되어 있습니다."
    }}
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a professional proposal generator. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    return json.loads(response.choices[0].message.content)