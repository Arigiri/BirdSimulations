"""
Các tiện ích hỗ trợ cho module thời tiết
"""

def print_safe(text_vn, text_en=None):
    """In thông báo an toàn với tiếng Việt, nếu lỗi UnicodeEncodeError thì in phiên bản tiếng Anh"""
    try:
        print(text_vn)
    except UnicodeEncodeError:
        if text_en:
            print(text_en)
        else:
            # Tạo phiên bản không dấu
            text = text_vn.replace("à", "a").replace("á", "a").replace("ả", "a").replace("ã", "a").replace("ạ", "a")
            text = text.replace("è", "e").replace("é", "e").replace("ẻ", "e").replace("ẽ", "e").replace("ẹ", "e")
            text = text.replace("ì", "i").replace("í", "i").replace("ỉ", "i").replace("ĩ", "i").replace("ị", "i")
            text = text.replace("ò", "o").replace("ó", "o").replace("ỏ", "o").replace("õ", "o").replace("ọ", "o")
            text = text.replace("ù", "u").replace("ú", "u").replace("ủ", "u").replace("ũ", "u").replace("ụ", "u")
            text = text.replace("ỳ", "y").replace("ý", "y").replace("ỷ", "y").replace("ỹ", "y").replace("ỵ", "y")
            text = text.replace("đ", "d")
            print(text)
