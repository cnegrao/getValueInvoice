import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# Configurar o caminho para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title('Extrator de Valores de Nota Fiscal')

# Função para extrair dados de imagem


def extrair_dados_imagem(uploaded_image):
    # Abrir a imagem
    image = Image.open(uploaded_image)

    # Pré-processamento da imagem
    image = image.convert('L')  # Converter para escala de cinza
    image = image.filter(ImageFilter.SHARPEN)  # Aumentar nitidez
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Aumentar contraste

    st.image(image, caption='Nota Fiscal Carregada e Processada',
             use_column_width=True)

    # Realizar OCR na imagem com configuração personalizada
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)

    # Exibir o texto extraído para depuração
    st.text("Texto extraído:")
    st.write(text)

    # Extração de data
    data = re.search(r'\d{2}/\d{2}/\d{4}', text)
    data = data.group() if data else "Data não encontrada"

    # Extração de localização
    localizacao = re.search(
        r'(?i)(localização|endereço|av\.\s|r\.\s|quadra\s|lote\s).+', text)
    localizacao = localizacao.group() if localizacao else "Localização não encontrada"

    # Extração de itens e valores
    itens = re.findall(r'(.+)\s+(\d+[.,]\d{2})', text)
    valores = re.findall(r'\d+[.,]\d{2}', text)

    # Extração do valor total
    valor_total = re.search(
        r'(Total|Valor Total|Total a Pagar|Total a pagar)[^\d]*(\d+[.,]\d{2})', text, re.IGNORECASE)
    valor_total = valor_total.group(
        2) if valor_total else "Valor total não encontrado"

    return data, localizacao, itens, valor_total

# Função para extrair dados de XML


def extrair_dados_xml(uploaded_xml):
    content = uploaded_xml.read()
    root = ET.fromstring(content)

    # Extração de data
    data = root.find('.//{*}DataEmissao')
    data = data.text if data is not None else "Data não encontrada"

    # Extração de localização
    localizacao = root.find('.//{*}Endereco/{*}Endereco')
    localizacao = localizacao.text if localizacao is not None else "Localização não encontrada"

    # Extração de itens e valores
    itens = []
    for item in root.findall('.//{*}ItemListaServico'):
        descricao = item.find('.//{*}Descricao')
        valor = item.find('.//{*}ValorServicos')
        if descricao is not None and valor is not None:
            itens.append((descricao.text, valor.text))

    # Extração do valor total
    valor_total = root.find('.//{*}ValorLiquidoNfse')
    valor_total = valor_total.text if valor_total is not None else "Valor total não encontrado"

    return data, localizacao, itens, valor_total


# Layout com duas colunas para os botões de upload
col1, col2 = st.columns(2)

with col1:
    st.header("Upload de Imagem")
    uploaded_image = st.file_uploader(
        "Faça upload da foto da nota fiscal", type=["jpg", "jpeg", "png"])

with col2:
    st.header("Upload de XML")
    uploaded_xml = st.file_uploader(
        "Faça upload do arquivo XML da nota fiscal", type=["xml"])

# Processamento de Imagem
if uploaded_image is not None:
    st.subheader('Dados Extraídos da Imagem')
    data, localizacao, itens, valor_total = extrair_dados_imagem(
        uploaded_image)

    st.write(f"Data: {data}")
    st.write(f"Localização: {localizacao}")
    st.write(f"Valor Total: {valor_total}")
    st.subheader("Itens Consumidos:")
    for item, valor in itens:
        st.write(f"{item}: R$ {valor}")

# Processamento de XML
if uploaded_xml is not None:
    st.subheader('Dados Extraídos do XML')
    data, localizacao, itens, valor_total = extrair_dados_xml(uploaded_xml)

    st.write(f"Data: {data}")
    st.write(f"Localização: {localizacao}")
    st.write(f"Valor Total: {valor_total}")
    st.subheader("Itens Consumidos:")
    for item, valor in itens:
        st.write(f"{item}: R$ {valor}")
