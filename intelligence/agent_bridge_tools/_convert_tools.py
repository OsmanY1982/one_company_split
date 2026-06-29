"""格式转换工具 Mixin：PDF ↔ DOCX ↔ PPTX ↔ 图片"""

import os


class _ConvertToolsMixin:
    """格式转换工具注册"""

    # ── 1. pdf_to_docx ──
    def _reg_pdf_to_docx(self):
        def handler(pdf_path: str, docx_path: str = "") -> dict:
            try:
                if not os.path.isfile(pdf_path):
                    return {"error": f"文件不存在: {pdf_path}"}

                if not docx_path:
                    docx_path = os.path.splitext(pdf_path)[0] + ".docx"

                from pdf2docx import Converter
                cv = Converter(pdf_path)
                cv.convert(docx_path)
                cv.close()

                return {
                    "input": pdf_path,
                    "output": docx_path,
                    "message": "PDF 转 DOCX 成功",
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="pdf_to_docx",
            description="将 PDF 文件转换为 Word 文档（.docx）",
            parameters={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string", "description": "PDF 文件绝对路径"},
                    "docx_path": {"type": "string", "description": "输出 DOCX 路径，默认同名 .docx", "default": ""},
                },
                "required": ["pdf_path"],
            },
            category="convert",
        )(handler)

    # ── 2. docx_to_pdf ──
    def _reg_docx_to_pdf(self):
        def handler(docx_path: str, pdf_path: str = "") -> dict:
            try:
                if not os.path.isfile(docx_path):
                    return {"error": f"文件不存在: {docx_path}"}

                if not pdf_path:
                    pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

                from docx2pdf import convert
                convert(docx_path, pdf_path)

                return {
                    "input": docx_path,
                    "output": pdf_path,
                    "message": "DOCX 转 PDF 成功",
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="docx_to_pdf",
            description="将 Word 文档（.docx）转换为 PDF",
            parameters={
                "type": "object",
                "properties": {
                    "docx_path": {"type": "string", "description": "DOCX 文件绝对路径"},
                    "pdf_path": {"type": "string", "description": "输出 PDF 路径，默认同名 .pdf", "default": ""},
                },
                "required": ["docx_path"],
            },
            category="convert",
        )(handler)

    # ── 3. convert_image ──
    def _reg_convert_image(self):
        def handler(
            image_path: str,
            output_format: str = "png",
            output_path: str = "",
        ) -> dict:
            try:
                if not os.path.isfile(image_path):
                    return {"error": f"文件不存在: {image_path}"}

                from PIL import Image
                img = Image.open(image_path)

                if not output_path:
                    base = os.path.splitext(image_path)[0]
                    output_path = f"{base}.{output_format}"

                if output_format.lower() == "ico":
                    img.save(output_path, format="ICO", sizes=[(256, 256)])
                elif output_format.lower() in ("jpg", "jpeg"):
                    img = img.convert("RGB")
                    img.save(output_path, format="JPEG", quality=95)
                else:
                    img.save(output_path, format=output_format.upper())

                return {
                    "input": image_path,
                    "output": output_path,
                    "format": output_format,
                    "message": f"图片格式转换成功: → {output_format}",
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="convert_image",
            description="图片格式互转（PNG ↔ JPG ↔ GIF ↔ WebP ↔ BMP ↔ ICO）",
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "源图片文件绝对路径"},
                    "output_format": {"type": "string", "description": "目标格式: png/jpg/gif/webp/bmp/ico", "default": "png"},
                    "output_path": {"type": "string", "description": "输出路径，默认同名改后缀", "default": ""},
                },
                "required": ["image_path", "output_format"],
            },
            category="convert",
        )(handler)

    # ── 4. images_to_pdf ──
    def _reg_images_to_pdf(self):
        def handler(image_paths: list, pdf_path: str) -> dict:
            try:
                if not image_paths:
                    return {"error": "图片列表为空"}

                from PIL import Image

                images = []
                for p in image_paths:
                    if not os.path.isfile(p):
                        return {"error": f"文件不存在: {p}"}
                    img = Image.open(p).convert("RGB")
                    images.append(img)

                images[0].save(
                    pdf_path,
                    save_all=True,
                    append_images=images[1:] if len(images) > 1 else [],
                )

                return {
                    "count": len(image_paths),
                    "output": pdf_path,
                    "message": f"已将 {len(image_paths)} 张图片合并为 PDF",
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="images_to_pdf",
            description="将多张图片合并为一个 PDF",
            parameters={
                "type": "object",
                "properties": {
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "图片路径列表（按顺序）",
                    },
                    "pdf_path": {"type": "string", "description": "输出 PDF 路径"},
                },
                "required": ["image_paths", "pdf_path"],
            },
            category="convert",
        )(handler)
