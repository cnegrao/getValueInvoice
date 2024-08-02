import streamlit as st
from PIL import Image
import pytesseract
import re

# Configurar o caminho para o executável do Tesseract se necessário
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title('Extrator de Valor Total de Nota Fiscal')

uploaded_file = st.file_uploader(
    "Faça upload da foto da nota fiscal", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Abrir a imagem
    image = Image.open(uploaded_file)
    st.image(image, caption='Nota Fiscal Carregada', use_column_width=True)

    # Realizar OCR na imagem
    text = pytesseract.image_to_string(image)

    # Exibir o texto extraído para depuração
    st.text("Texto extraído:")
    st.write(text)

    # Procurar pelo valor total usando pistas textuais
    pattern = r'(Total|Valor Total|Total a Pagar|Total a pagar|Valor Pago)[^\d]*(\d+,\d{2})'
    matches = re.findall(pattern, text, re.IGNORECASE)

    if matches:
        # Assumir que o valor total é o último valor encontrado após as palavras-chave
        valor = matches[-1][1]
        st.success(f'O valor total da nota fiscal é: R$ {valor}')
    else:
        st.error('Valor total da nota fiscal não encontrado.')
