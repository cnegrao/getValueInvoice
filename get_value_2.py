import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re

# Configurar o caminho para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title('Extrator de Valores de Nota Fiscal')

uploaded_file = st.file_uploader(
    "Faça upload da foto da nota fiscal", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Abrir a imagem
    image = Image.open(uploaded_file)

    # Pré-processamento da imagem
    image = image.convert('L')  # Converter para escala de cinza
    image = image.filter(ImageFilter.SHARPEN)  # Aumentar nitidez
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # aAumentar contraste

    st.image(image, caption='Nota Fiscal Carregada e Processada',
             use_column_width=True)

    # Realizar OCR na imagem .com configuração personalizada
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)

    # Exibir o texto extraído para depuração
    st.text("Texto extraído:")
    st.write(text)

    # Procurar todos os valores no formato 999,99
    valores = re.finditer(r'\d+,\d{2}', text)

    if valores:
        st.subheader('Valores Encontrados')
        for valor in valores:
            start, end = valor.span()
            valor_texto = valor.group()
            st.write(f'Valor encontrado: R$ {
                     valor_texto} (Início: {start}, Fim: {end})')
    else:
        st.error('Nenhum valor encontrado.')

    # Procurar pelo valor total usando pistas textuais
    st.subheader('Possíveis Valores Totais Encontrados')
    pattern = r'(Total|Valor Total|Total a Pagar|Total a pagar)[^\d]*(\d+,\d{2})'
    matches = re.finditer(pattern, text, re.IGNORECASE)

    if matches:
        for match in matches:
            start, end = match.span()
            chave = match.group(1)
            valor_total = match.group(2)
            st.write(f'Possível valor total encontrado: R$ {
                     valor_total} (Chave: {chave}, Início: {start}, Fim: {end})')
    else:
        st.error('Nenhum valor total encontrado com palavras-chave.')
