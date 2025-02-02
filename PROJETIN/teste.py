import cv2
import pytesseract
import numpy as np
import os
import sys
from pdf2image import convert_from_path
from PIL import Image
from docx import Document
from reportlab.pdfgen import canvas

# Configuração do caminho do Tesseract (Necessário para Windows)
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image(image_path):
    """Pré-processa a imagem para otimizar o reconhecimento de texto pelo OCR."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Carrega em escala de cinza
    image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)  # Melhora a resolução
    
    # Aplicação de técnicas de binarização e remoção de ruído
    blurred = cv2.GaussianBlur(image, (5, 5), 0)  # Reduz ruídos
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    
    return thresh

def extract_text(image_path):
    """Extrai o texto da imagem processada usando Tesseract OCR."""
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image, lang="eng+por")  # Suporte para inglês e português
    return text

def convert_pdf_to_images(pdf_path):
    """Converte um PDF em uma lista de imagens (uma por página)."""
    images = convert_from_path(pdf_path)
    image_paths = []
    for i, image in enumerate(images):
        img_path = f"page_{i+1}.png"
        image.save(img_path, "PNG")
        image_paths.append(img_path)
    return image_paths

def save_text_to_txt(text, output_path):
    """Salva o texto extraído em um arquivo .txt."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

def save_text_to_docx(text, output_path):
    """Salva o texto extraído em um arquivo .docx."""
    doc = Document()
    doc.add_paragraph(text)
    doc.save(output_path)

def save_text_to_pdf(text, output_path):
    """Salva o texto extraído em um arquivo .pdf."""
    c = canvas.Canvas(output_path)
    text_lines = text.split("\n")
    
    y_position = 800
    for line in text_lines:
        c.drawString(50, y_position, line)
        y_position -= 15
    
    c.save()

def recognize_key_fields(text):
    """Tenta identificar campos importantes como nome, data e assinatura."""
    key_fields = {"Nome": None, "Data": None, "Assinatura": None}
    
    # Identificação simples baseada em palavras-chave
    lines = text.split("\n")
    for line in lines:
        if "Nome" in line or "name" in line.lower():
            key_fields["Nome"] = line
        elif "Data" in line or "date" in line.lower():
            key_fields["Data"] = line
        elif "Assinatura" in line or "signature" in line.lower():
            key_fields["Assinatura"] = "Campo de assinatura identificado"

    return key_fields

def save_text_to_json(text, output_path):
    """Salva o texto extraído e campos-chave em formato JSON."""
    import json
    data = {"Texto Extraído": text, "Campos Reconhecidos": recognize_key_fields(text)}
    
    with open(output_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def main(input_path, output_format="txt"):
    """Processa a imagem ou PDF e salva o texto extraído no formato desejado."""
    if not os.path.exists(input_path):
        print("Erro: Arquivo não encontrado.")
        return
    
    extracted_text = ""
    
    if input_path.lower().endswith(".pdf"):
        images = convert_pdf_to_images(input_path)
        for img_path in images:
            extracted_text += extract_text(img_path) + "\n\n"
            os.remove(img_path)  # Remove imagens temporárias
    else:
        extracted_text = extract_text(input_path)

    # Salvar no formato desejado
    output_file = f"output.{output_format}"
    
    if output_format == "txt":
        save_text_to_txt(extracted_text, output_file)
    elif output_format == "docx":
        save_text_to_docx(extracted_text, output_file)
    elif output_format == "pdf":
        save_text_to_pdf(extracted_text, output_file)
    elif output_format == "json":
        save_text_to_json(extracted_text, output_file)
    else:
        print("Erro: Formato não suportado.")

    print(f"Texto extraído salvo em {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py <caminho_da_imagem_ou_pdf> [formato_saida]")
    else:
        input_file = sys.argv[1]
        output_type = sys.argv[2] if len(sys.argv) > 2 else "txt"
        main(input_file, output_type)
