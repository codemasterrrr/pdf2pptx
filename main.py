import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
from io import BytesIO
import os

st.set_page_config(page_title="PDF 흑백 반전 변환기", layout="centered")

# 제목 & 설명
st.title("🌓 PDF 흑/백 반전 변환기")
st.write("PDF를 업로드하면 각 페이지의 색상을 반전시켜 새로운 PDF로 만들어 드립니다. (검정↔흰색 포함 전체 색상 반전)")

# 파일 업로더
uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type="pdf")

def invert_pdf_colors(pdf_bytes, zoom=2.0):
    """
    pdf_bytes: 원본 PDF 바이트
    zoom: 렌더링 배율(기본 2.0 → 해상도 개선)
    return: 반전 처리된 PDF 바이트 (BytesIO)
    """
    # 원본 PDF 열기
    src_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 결과 PDF 생성
    out_doc = fitz.open()

    # 진행률 표시
    progress = st.progress(0, text="반전 처리 중...")

    # 페이지별 처리
    for i in range(len(src_doc)):
        page = src_doc.load_page(i)
        rect = page.rect

        # 렌더 매트릭스 (해상도 향상)
        matrix = fitz.Matrix(zoom, zoom)

        # 페이지 → 픽스맵 렌더링
        pix = page.get_pixmap(matrix=matrix, alpha=False)  # 알파 제거(RGB)

        # 픽스맵 → PIL 이미지
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 색상 반전 (검정↔흰색 포함 전체 색상)
        inverted = ImageOps.invert(img)

        # 이미지 → 바이트
        img_bytes = BytesIO()
        inverted.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # 새 페이지 생성 (원본 페이지 크기 유지)
        new_page = out_doc.new_page(width=rect.width, height=rect.height)

        # 반전 이미지를 전체 페이지에 삽입
        # 주의: 렌더 배율(zoom)을 적용했으므로, 이미지가 page rect에 맞게 자동 스케일됩니다.
        new_page.insert_image(rect, stream=img_bytes.getvalue(), keep_proportion=False)

        progress.progress((i + 1) / len(src_doc), text=f"반전 처리 중... ({i + 1}/{len(src_doc)})")

    progress.empty()

    # 결과 PDF를 메모리에 저장 후 반환
    out_bytes = BytesIO()
    out_doc.save(out_bytes)
    out_doc.close()
    src_doc.close()
    out_bytes.seek(0)
    return out_bytes

# 처리 & 다운로드
if uploaded_file is not None:
    # 출력 파일명 지정: 원본 이름 + (반전).pdf
    base, _ = os.path.splitext(uploaded_file.name)
    output_filename = f"{base}(반전).pdf"

    with st.spinner("PDF 반전 변환 중입니다..."):
        result_pdf = invert_pdf_colors(uploaded_file.read(), zoom=2.0)

    st.success("반전 변환이 완료되었습니다! ✅")

    # 다운로드 버튼
    st.download_button(
        label="📥 반전된 PDF 다운로드",
        data=result_pdf,
        file_name=output_filename,
        mime="application/pdf"
    )

    # 옵션 안내
    with st.expander("⚙️ 고급 설정 안내 (참고)"):
        st.markdown(
            "- 기본 렌더 배율은 **2.0**이며, 더 선명하게 원하시면 코드의 `zoom` 값을 2.5~3.0으로 조절하세요.\n"
            "- 이 코드는 **전체 색상 반전**을 수행합니다. (검정/흰색 포함)\n"
            "- 큰 PDF의 경우 메모리 사용량이 증가할 수 있습니다.\n"
        )
