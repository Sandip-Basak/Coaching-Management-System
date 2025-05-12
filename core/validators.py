from django.core.exceptions import ValidationError


def validate_file_extension(value):
    """Validate file extension for uploaded files"""
    import os
    from django.core.exceptions import ValidationError
    
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.xls']
    
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Allowed extensions are: pdf, doc, docx, xlsx, xls')


def validate_pdf_extension(value):
    """Validate file is a PDF"""
    import os
    from django.core.exceptions import ValidationError
    
    ext = os.path.splitext(value.name)[1]
    
    if not ext.lower() == '.pdf':
        raise ValidationError('Only PDF files are allowed.')


def validate_excel_extension(value):
    """Validate file is an Excel spreadsheet"""
    import os
    from django.core.exceptions import ValidationError
    
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.xlsx', '.xls']
    
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only Excel files (xlsx, xls) are allowed.')


def validate_image_extension(value):
    """Validate file is an image"""
    import os
    from django.core.exceptions import ValidationError
    
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only image files (jpg, jpeg, png, gif) are allowed.')


def validate_video_embed_code(value):
    """Validate video embed code"""
    if not ('<iframe' in value.lower() and '</iframe>' in value.lower()):
        raise ValidationError('Invalid embed code. Please provide a valid iframe embed code.')
