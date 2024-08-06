import subprocess


def check_tesseract_language_support(language='por'):
    try:
        # Executar o comando 'tesseract --list-langs'
        result = subprocess.run(['tesseract', '--list-langs'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Verificar se o idioma está na lista de idiomas suportados
        if language in result.stdout:
            print(f"O Tesseract suporta o idioma '{language}'.")
        else:
            print(f"O Tesseract não suporta o idioma '{language}'.")
    except FileNotFoundError:
        print("O Tesseract não está instalado ou não está no PATH do sistema.")


# Verificar suporte para o idioma português
check_tesseract_language_support()
