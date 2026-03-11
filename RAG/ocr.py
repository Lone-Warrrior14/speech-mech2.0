import pytesseract
from pdf2image import convert_from_path

def pdf_ocr(file_path):

    images = convert_from_path(file_path)

    text = ""

    for image in images:
        text += pytesseract.image_to_string(image)

    return text