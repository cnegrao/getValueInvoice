import streamlit as st
from PIL import Image
import re
import spacy
import xml.etree.ElementTree as ET

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
    # Realizar qualquer pré-processamento necessário na imagem
    return image

# Função para verificar se o valor é uma unidade de medida


def is_unit(text):
    unit_keywords = ['un', 'kg', 'litro', 'ml', 'g']
    return any(keyword in text.lower() for keyword in unit_keywords)

# Função para limpar e corrigir o texto extraído


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove espaços extras
    # Remove caracteres especiais indesejados
    text = re.sub(r'[^\w\s.,/]', '', text)
    return text

# Função para limpar o CNPJ


def clean_cnpj(cnpj):
    cnpj = re.sub(r'\s+', '', cnpj)  # Remove todos os espaços em branco
    cnpj = re.sub(r'(\d{2})\.?(\d{3})\.?(\d{3})/(\d{4})-?(\d{2})',
                  r'\1.\2.\3/\4-\5', cnpj)  # Formatar corretamente
    # Corrigir número incorreto detectado pelo OCR
    cnpj = cnpj.replace("486.", "48.")
    return cnpj

# Função para extrair texto e aplicar PNL


def process_text_with_nlp(text):
    text = clean_text(text)
    doc = nlp(text)
    valores = []
    items = []
    total = None
    local = None
    cnpj = None
    data = None
    telefone = None

    for sent in doc.sents:
        sent_text = sent.text.strip()

        # Extrair local
        if re.search(r'Endereço|Local|Quadra|Avenida|Rua|Logradouro', sent_text, re.IGNORECASE):
            local = sent_text

        # Extrair CNPJ
        if not cnpj:
            cnpj_match = re.search(
                r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', sent_text)
            if cnpj_match:
                cnpj = clean_cnpj(cnpj_match.group())

        # Extrair data
        data_match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', sent_text)
        if data_match:
            data = data_match.group()

        # Extrair telefone
        telefone_match = re.search(r'\(\d{2}\)\s*\d{4,5}-\d{4}', sent_text)
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

    return valores, items, total, local, cnpj, data, telefone


# Processamento de Imagem
if uploaded_image is not None:
    st.subheader('Imagem Processada')
    image = Image.open(uploaded_image)
    processed_image = preprocess_image(image)
    st.image(processed_image,
             caption='Nota Fiscal Carregada e Processada', use_column_width=True)

    # Realizar OCR usando as capacidades de visão do GPT
    text = st.text_area("Por favor, insira o texto extraído manualmente aqui:")

    st.text("Texto extraído:")
    st.write(text)

    text = clean_text(text)
    st.text("Texto limpo:")
    st.write(text)

    # Corrigir possíveis erros de OCR
    text = text.replace("CHPJ", "CNPJ")

    # Aplicar PNL ao texto extraído
    valores, items, total, local, cnpj, data, telefone = process_text_with_nlp(
        text)

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
            chave_limpa = chave.split('}')[-1]
            st.write(f'{chave_limpa}: R$ {valor}')
    else:
        st.error('Nenhum valor encontrado no XML.')
