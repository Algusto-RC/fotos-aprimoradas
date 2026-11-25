# Fotos Aprimoradas

Aplicativo do Lab Gusto para Windows 10 e 11 (x64). Aprimore uma foto na resolução original (1×) ou amplie em 2×, 3× ou 4× por lado com Lanczos. Escolha **Suave** para reduzir ruído, **Equilibrado** para uso geral ou **Detalhes** para realçar mais as bordas e texturas de fotos levemente borradas. A nitidez é aplicada à luminância em duas escalas, antes da ampliação.

Na prévia, mova o divisor para comparar. Selecione **Zoom 100%** e arraste com o botão direito para examinar outras áreas. O processamento é local e exporta em PNG, JPG ou WebP. O resultado depende da qualidade da origem, especialmente em fotos com desfoque forte.

O instalador inclui o aplicativo e suas dependências, grava em `C:\Program Files\labPontoGusto\Fotos Aprimoradas` e oferece atalho opcional na Área de Trabalho. O botão circular no rodapé consulta o GitHub Releases e verifica o SHA-256 antes de abrir o instalador da atualização.

## Desenvolvimento

Use Python 3.12 com Tk e instale as dependências com `python -m pip install -r requirements.txt`. Inicie com `python app.py`. A imagem de demonstração é incorporada no build Windows. O GitHub Actions empacota o aplicativo, testa a instalação e a inicialização e publica o executável.
