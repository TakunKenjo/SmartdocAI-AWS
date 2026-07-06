"""
SmartDocAI - Language Detector
Phát hiện ngôn ngữ của câu truy vấn và tạo prompt theo ngôn ngữ tương ứng.
Hỗ trợ: Tiếng Việt (vi) và Tiếng Anh (en).
"""
import re
import logging

logger = logging.getLogger(__name__)

# Tối ưu: Chuyển sang SET để tìm kiếm O(1) nhanh hơn LIST
VIETNAMESE_WORDS = {
    "của", "và", "là", "có", "trong", "cho", "được", "này",
    "không", "với", "các", "một", "những", "đã", "từ", "về",
    "đến", "hay", "như", "tại", "khi", "để", "theo", "năm",
    "người", "cũng", "nhiều", "sau", "trên", "vào", "ra",
    "nếu", "thì", "bạn", "tôi", "hãy", "gì", "nào", "sao",
    "thế", "rằng", "bởi", "vì", "nên", "mà", "còn", "đây",
    "đó", "ở", "rất", "lại", "chỉ", "do", "cần", "phải",
}

# Các ký tự đặc trưng từ hình ảnh (dùng để check nhanh)
VNI_CHARS_SIMPLE = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'

def detect_language(text: str) -> str:
    """
    Phát hiện ngôn ngữ của đoạn văn bản đầu vào.

    Thuật toán 2 bước:
    1. Kiểm tra ký tự có dấu tiếng Việt (nhanh, O(n) ký tự).
    2. Fallback: kiểm tra từ phổ biến tiếng Việt không dấu.

    Args:
        text: Văn bản cần phát hiện ngôn ngữ.

    Returns:
        'vi' nếu là tiếng Việt, 'en' cho tất cả các ngôn ngữ khác.
    """
    if not text or not text.strip():
        return "en"
    
    text_lower = text.lower()
    
    # Cách 1: Kiểm tra ký tự tiếng Việt (Theo logic trong hình)
    if any(char in text_lower for char in VNI_CHARS_SIMPLE):
        return "vi"
    
    # Cách 2: Kiểm tra từ phổ biến (Dự phòng cho tiếng Việt không dấu)
    words = text_lower.split()
    if any(w in VIETNAMESE_WORDS for w in words):
        return "vi"
        
    return "en"

def get_prompt_template(language: str, context: str, user_input: str) -> str:
    """
    Tạo prompt chuẩn theo Listing 6 trong tài liệu.
    """
    if language == "vi":
        return f"""Su dung ngu canh sau day de tra loi cau hoi. 
Neu ban khong biet, chi can noi la ban khong biet. 
Tra loi ngan gon (3-4 cau) BAT BUOC bang tieng Viet.

Ngu canh: {context}

Cau hoi: {user_input}

Tra loi:"""
    else:
        return f"""Use the following context to answer the question. 
If you don't know the answer, just say you don't know. 
Keep answer concise (3-4 sentences).

Context: {context}

Question: {user_input}

Answer:"""

def get_language_instruction(language: str) -> str:
    """
    Trả về hướng dẫn ngôn ngữ cho prompt template.

    Args:
        language: Mã ngôn ngữ ('vi' hoặc 'en')

    Returns:
        Chuỗi hướng dẫn cho LLM
    """
    if language == "vi":
        return (
            "Hãy trả lời bằng Tiếng Việt. "
            "Sử dụng ngôn ngữ rõ ràng, dễ hiểu."
        )
    else:
        return (
            "Please answer in English. "
            "Use clear and concise language."
        )
