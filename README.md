# Fotos Aprimoradas

Aplicativo do Lab Gusto para Windows 10 e 11 (x64). Amplia imagens 2×, 3× ou 4× por lado com interpolação Lanczos, nitidez e redução opcional de ruído. Compara a foto original com o resultado e exporta em PNG, JPG ou WebP. O processamento é local. Ampliação e nitidez não recuperam detalhes ausentes do arquivo original.

O instalador inclui o aplicativo e suas dependências, grava em `C:\Program Files\labPontoGusto\Fotos Aprimoradas` e oferece atalho opcional na Área de Trabalho. O botão circular no rodapé consulta o GitHub Releases e verifica o SHA-256 antes de abrir o instalador da atualização.

## Desenvolvimento

Use Python 3.12 com Tk e instale as dependências com `python -m pip install -r requirements.txt`. Inicie com `python app.py`. A imagem de demonstração é incorporada no build Windows. O GitHub Actions empacota o aplicativo, testa a instalação e a inicialização e publica o executável.
