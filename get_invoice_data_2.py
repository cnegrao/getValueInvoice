import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import spacy
import xml.etree.ElementTree as ET

# Configurar o caminho para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Carregar o modelo de linguagem do spaCy
nlp = spacy.load('pt_core_news_sm')

st.title('Extrator de Valores de Nota Fiscal de Consumidor Eletrônica (NFC-e)')

# Layout com duas colunas para os botões de upload
col1, col2 = st.columns(2)

with col1:
    st.header("Upload de Imagem")
    uploaded_image = st.file_uploader(
        "Faça upload da foto da NFC-e", type=["jpg", "jpeg", "png"])

with col2:
    st.header("Upload de XML")
    uploaded_xml = st.file_uploader(
        "Faça upload do arquivo XML da NFC-e", type=["xml"])

# Função para pré-processamento da imagem


def preprocess_image(image):
    # Converter para escala de cinza
    gray = image.convert('L')
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2)
    # Redimensionar a imagem para aumentar a resolução
    resized = enhanced.resize(
        (enhanced.width * 2, enhanced.height * 2), Image.BICUBIC)
    # Aplicar filtro de suavização
    smoothed = resized.filter(ImageFilter.SMOOTH_MORE)
    # Aplicar filtro de nitidez
    sharpened = smoothed.filter(ImageFilter.SHARPEN)
    return sharpened

# Função para limpar e corrigir o texto extraído


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove espaços extras
    # Remove caracteres especiais indesejados
    text = re.sub(r'[^\w\s.,/]', '', text)
    return text

# Função para extrair e limpar o CNPJ


def extract_cnpj(text):
    cnpj_match = re.search(
        r'\b(\d{2})[.\s]?(\d{3})[.\s]?(\d{3})[./\s]?\d{4}[.\s]?\d{2}\b', text)
    if cnpj_match:
        cnpj = f"{cnpj_match.group(1)}.{cnpj_match.group(2)}.{
            cnpj_match.group(3)}/{cnpj_match.group(4)}-{cnpj_match.group(5)}"
        return re.sub(r'\s+', '', cnpj)  # Remove espaços em branco
    return None

# Função para extrair e limpar o CPF


def extract_cpf(text):
    cpf_match = re.search(
        r'\b(\d{3})[.\s]?(\d{3})[.\s]?(\d{3})[-\s]?(\d{2})\b', text)
    if cpf_match:
        cpf = f"{cpf_match.group(1)}.{cpf_match.group(2)}.{
            cpf_match.group(3)}-{cpf_match.group(4)}"
        return re.sub(r'\s+', '', cpf)  # Remove espaços em branco
    return None

# Função para verificar se o valor é uma unidade de medida


def is_unit(text):
    unit_keywords = ['un', 'kg', 'litro', 'ml', 'g']
    return any(keyword in text.lower() for keyword in unit_keywords)

# Função para processar o texto extraído


def process_text_with_nlp(text):
    text = clean_text(text)
    doc = nlp(text)
    valores = []
    items = []
    total = None
    local = None
    cnpj = None
    cpf = None
    data = None
    telefone = None
    estabelecimento = None

    for sent in doc.sents:
        sent_text = sent.text.strip()
        st.text(f"Sentença processada: {sent_text}")

        # Extrair estabelecimento
        if not estabelecimento and re.search(r'^(.*?)(LTDA|ME|EPP|SA)\b', sent_text, re.IGNORECASE):
            estabelecimento = sent_text

        # Extrair local
        if re.search(r'Endereço|Local|Quadra|Avenida|Rua|Logradouro', sent_text, re.IGNORECASE):
            local = sent_text

        # Extrair CNPJ
        if not cnpj:
            cnpj_raw = re.search(
                r'CNPJ[:\s]*(\d{2}[.\s]?\d{3}[.\s]?\d{3}[./\s]?\d{4}[.\s]?\d{2})', sent_text)
            if cnpj_raw:
                st.text(f"CNPJ bruto encontrado: {cnpj_raw.group(1)}")
                cnpj = extract_cnpj(cnpj_raw.group(1))
                if cnpj:
                    st.text(f"CNPJ limpo encontrado: {cnpj}")

        # Extrair CPF com a palavra-chave 'CPF'
        if 'CPF' in sent_text:
            cpf_raw = re.search(
                r'CPF[:\s]*(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2})', sent_text)
            if cpf_raw:
                st.text(f"CPF bruto encontrado: {cpf_raw.group(1)}")
                cpf = extract_cpf(cpf_raw.group(1))
                if cpf:
                    st.text(f"CPF limpo encontrado: {cpf}")

        # Extrair data
        data_match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', sent_text)
        if data_match:
            data = data_match.group()

        # Extrair telefone
        telefone_match = re.search(
            r'Fone\s?[:\s]?\(?\d{2}\)?\s?\d{4,5}-\d{4}', sent_text)
        if telefone_match:
            telefone = telefone_match.group()

        # Extrair valores monetários no formato 999,99
        value_matches = re.findall(r'\d+,\d{2}', sent_text)
        for value in value_matches:
            surrounding_text = sent_text.split(value)[0][-10:]
            if not is_unit(surrounding_text):
                valores.append(value)

        # Extrair itens e valores
        item_match = re.match(
            r'(\d+)\s+(.+?)\s+(\d+[.,]\d{4})?\s+(\d+[.,]\d{2})', sent_text)
        if item_match:
            numero_item = item_match.group(1)
            descricao = item_match.group(2)
            unidade = item_match.group(3) if item_match.group(3) else ''
            valor_total = item_match.group(4)
            if not is_unit(valor_total):
                items.append((numero_item, descricao, unidade, valor_total))

        # Procurar pelo valor total usando pistas textuais
        total_match = re.search(
            r'(Total|Valor Total|Total a Pagar|Total a pagar)[^\d]*(\d+,\d{2})', sent_text, re.IGNORECASE)
        if total_match:
            total = total_match.group(2)

    return valores, items, total, local, cnpj, cpf, data, telefone, estabelecimento


# Processamento de Imagem
if uploaded_image is not None:
    st.subheader('Imagem Processada')
    image = Image.open(uploaded_image)
    image = preprocess_image(image)
    st.image(image, caption='NFC-e Carregada e Processada',
             use_column_width=True)

    # Realizar OCR na imagem com configuração personalizada
    custom_config = r'--oem 3 --psm 6 -l por'
    text = pytesseract.image_to_string(image, config=custom_config)

    st.text("Texto extraído:")
    st.write(text)

    # Aplicar processamento de texto ao texto extraído
    valores, items, total, local, cnpj, cpf, data, telefone, estabelecimento = process_text_with_nlp(
        text)

    if estabelecimento:
        st.subheader('Estabelecimento')
        st.write(estabelecimento)
    else:
        st.error('Nenhum estabelecimento encontrado.')

    if local:
        st.subheader('Local')
        st.write(local)
    else:
        st.error('Nenhum local encontrado.')

    if cnpj:
        st.subheader('CNPJ')
        st.write(cnpj)
    else:
        st.error('Nenhum CNPJ encontrado.')

    if cpf:
        st.subheader('CPF')
        st.write(cpf)
    else:
        st.error('Nenhum CPF encontrado.')

    if data:
        st.subheader('Data')
        st.write(data)
    else:
        st.error('Nenhuma data encontrada.')

    if telefone:
        st.subheader('Telefone')
        st.write(telefone)
    else:
        st.error('Nenhum telefone encontrado.')

    if valores:
        st.subheader('Valores Encontrados')
        for valor in valores:
            st.write(f'Valor encontrado: R$ {valor}')
    else:
        st.error('Nenhum valor encontrado.')

    if total:
        st.subheader('Valor Total')
        st.write(f'Valor Total: R$ {total}')
    else:
        st.error('Nenhum valor total encontrado.')

    if items:
        st.subheader('Itens e Valores')
        for numero_item, descricao, unidade, valor_total in items:
            st.write(
                f'{numero_item} - {descricao}: Unidade: {unidade}, Valor Total: R$ {valor_total}')
    else:
        st.error('Nenhum item encontrado.')

# Processamento de XML
if uploaded_xml is not None:
    st.subheader('Arquivo XML Processado')
    content = uploaded_xml.read()
    root = ET.fromstring(content)

    valores = []
    for elem in root.iter():
        if elem.tag.endswith('vProd') or elem.tag.endswith('vNF'):
            valores.append((elem.tag, elem.text))

    if valores:
        st.subheader('Valores Encontrados no XML')
        for chave, valor in valores:
            chave_limpa = chave.split('}')[-1]  # Remover namespace da chave
            st.write(f'{chave_limpa}: R$ {valor}')
    else:
        st.error('Nenhum valor encontrado no XML.')
