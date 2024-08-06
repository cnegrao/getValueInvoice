import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import xml.etree.ElementTree as ET

# Configurar o caminho para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title('Extrator de Valores de Nota Fiscal')

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

# Função para pré-processamento da imagem


def preprocess_image(image):
    # Converter para escala de cinza
    gray = image.convert('L')
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2)
    # Aumentar nitidez
    enhanced = enhanced.filter(ImageFilter.SHARPEN)
    return enhanced

# Função para limpar e corrigir o texto extraído


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove espaços extras
    # Remove caracteres especiais indesejados
    text = re.sub(r'[^\w\s.,/]', '', text)
    return text

# Função para limpar o CNPJ


def clean_cnpj(cnpj):
    st.text("----------------------")
    st.text("Entrando na função clean_cnpj")
    st.text(f"CNPJ original: {cnpj}")
    # Remover todos os espaços em branco
    cnpj = cnpj.replace(" ", "")
    # Corrigir formato específico do CNPJ
    cnpj = re.sub(
        r'(\d{2})\.?(\d{3})\.?(\d{3})/(\d{4})-?(\d{2})', r'\1.\2.\3/\4-\5', cnpj)
    # Corrigir número incorreto detectado pelo OCR
    cnpj = cnpj.replace("486.", "48.")

    # Verificar e corrigir possíveis caracteres adicionais
    if len(cnpj) > 18:
        cnpj = cnpj[:18]

    # Imprimir o CNPJ limpo
    st.text(f"CNPJ limpo: {cnpj}")
    st.text("Saindo da função clean_cnpj")
    st.text("----------------------")
    return cnpj

# Função para realizar OCR usando Tesseract com configurações avançadas


def perform_ocr_tesseract(image):
    custom_config = r'--oem 3 --psm 6 -l por'
    text = pytesseract.image_to_string(image, config=custom_config)
    return text


# Processamento de Imagem
if uploaded_image is not None:
    st.subheader('Imagem Processada')
    # Abrir a imagem
    image = Image.open(uploaded_image)
    image = preprocess_image(image)
    st.image(image, caption='Nota Fiscal Carregada e Processada',
             use_column_width=True)

    # Realizar OCR na imagem com configuração personalizada
    text = perform_ocr_tesseract(image)

    # Exibir o texto extraído para depuração
    st.text("Texto extraído:")
    st.write(text)

    # Limpar texto extraído
    text = clean_text(text)
    st.text("Texto limpo:")
    st.write(text)

    # Procurar todos os valores no formato 999,99
    valores = re.findall(r'\d+,\d{2}', text)

    if valores:
        st.subheader('Valores Encontrados')
        for valor in valores:
            st.write(f'Valor encontrado: R$ {valor}')
    else:
        st.error('Nenhum valor encontrado.')

    # Procurar pelo valor total usando pistas textuais
    st.subheader('Possíveis Valores Totais Encontrados')
    pattern = r'(Total|Valor Total|Total a Pagar|Total a pagar)[^\d]*(\d+,\d{2})'
    matches = re.finditer(pattern, text, re.IGNORECASE)

    if matches:
        for match in matches:
            chave = match.group(1)
            valor_total = match.group(2)
            st.write(f'Possível valor total encontrado: R$ {
                     valor_total} (Chave: {chave})')
    else:
        st.error('Nenhum valor total encontrado com palavras-chave.')

    # Procurar pelo CNPJ usando regex
    cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
    if cnpj_match:
        cnpj = clean_cnpj(cnpj_match.group())
        st.subheader('CNPJ')
        st.write(cnpj)
    else:
        st.error('Nenhum CNPJ encontrado.')

# Processamento de XML
if uploaded_xml is not None:
    st.subheader('Arquivo XML Processado')
    # Ler o conteúdo do arquivo XML
    content = uploaded_xml.read()
    root = ET.fromstring(content)

    # Extrair valores do XML
    valores = []
    for elem in root.iter():
        if elem.tag.endswith('BaseCalculo') or elem.tag.endswith('ValorLiquidoNfse') or elem.tag.endswith('ValorServicos'):
            valores.append((elem.tag, elem.text))

    if valores:
        st.subheader('Valores Encontrados no XML')
        for chave, valor in valores:
            chave_limpa = chave.split('}')[-1]  # Remover namespace da chave
            st.write(f'{chave_limpa}: R$ {valor}')
    else:
        st.error('Nenhum valor encontrado no XML.')
