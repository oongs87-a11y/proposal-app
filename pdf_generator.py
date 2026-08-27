import io
import base64
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

def render_html_to_pdf(data: dict, uploaded_image_bytes=None) -> bytes:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("template.html")
    
    photo_b64 = None
    if uploaded_image_bytes:
        photo_b64 = base64.b64encode(uploaded_image_bytes).decode('utf-8')

    def format_currency(val):
        try:
            return f"{int(val):,}"
        except:
            return str(val)
            
    html_out = template.render(
        data=data,
        photo_base64=photo_b64,
        format_currency=format_currency
    )
    
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_out,
        dest=pdf_buffer,
        encoding='utf-8'
    )
    
    if pisa_status.err:
        raise Exception("PDF 생성 중 에러가 발생했습니다.")
        
    pdf_buffer.seek(0)
    return pdf_buffer.read()