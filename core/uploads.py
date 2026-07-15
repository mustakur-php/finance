"""تحقق موحّد من الملفات المرفوعة — النوع والحجم."""
import os

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_CONTENT_TYPES = {
    'application/pdf',
    'image/jpeg', 'image/png', 'image/gif',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

ALLOWED_EXTENSIONS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.gif',
    '.doc', '.docx', '.xls', '.xlsx',
}


def validate_upload(f, max_size=MAX_UPLOAD_SIZE):
    """يرجّع (True, '') إذا الملف سليم، أو (False, رسالة الخطأ)."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, 'نوع الملف غير مسموح. المسموح: PDF, صور, Word, Excel'
    if f.content_type not in ALLOWED_CONTENT_TYPES:
        return False, 'نوع الملف غير مسموح. المسموح: PDF, صور, Word, Excel'
    if f.size > max_size:
        return False, f'حجم الملف يتجاوز الحد المسموح ({max_size // (1024 * 1024)} MB)'
    return True, ''
