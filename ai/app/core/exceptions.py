class InvalidImageError(Exception):
    """업로드된 파일을 이미지로 열 수 없을 때 (깨진 파일, 이미지가 아닌 파일 등)"""