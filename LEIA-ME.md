# Tabela SAJ — atualização dos cartões e filtros de notícias

Esta atualização **não modifica o conteúdo jurídico da tabela**. Ela altera somente o painel de notícias, a classificação das manchetes e a automação de publicação.

## Arquivos a enviar ao seu repositório

Extraia `Tabela_SAJ_Correcao_Noticias_Filtros.zip` e envie **as pastas**, preservando os caminhos. Os arquivos substituem os existentes com o mesmo nome:

- `site/assets/news.js` — manchetes clicáveis, imagem de prévia quando fornecida pela fonte, busca própria e filtros.
- `site/assets/live.css` — novo visual dos cartões de notícias.
- `scripts/collect_news.py` — coleta imagem disponibilizada em RSS ou `og:image` de páginas públicas e classifica notícias por assunto.
- `tests/test_collector.py` — testes automatizados da coleta e classificação.
- `.github/workflows/publicar.yml` — automação diária para coletar notícias e publicar a pasta `site` no Pages.

**Não é necessário apagar nem substituir `site/index.html`.**

## Pelo navegador do GitHub

1. Abra `https://github.com/erodrigues848-boop/Tabela-SAJ-2.0` e clique em **Code**.
2. Escolha **Add file → Upload files**.
3. Arraste as pastas extraídas `site`, `scripts`, `tests`, `.github` **preservando os nomes e a estrutura**. Caso o navegador não aceite pastas, substitua cada arquivo pela opção **Edit this file** na localização indicada acima.
4. Clique em **Commit changes**.
5. Abra **Actions** e selecione o workflow cujo arquivo é `.github/workflows/publicar.yml`, chamado **Atualizar notícias e publicar Tabela SAJ**. Clique em **Run workflow → Run workflow**.
6. Ao aparecer um círculo verde, abra `https://erodrigues848-boop.github.io/Tabela-SAJ-2.0/` e atualize com **Ctrl+F5**.
7. Apenas depois de confirmar o sucesso, remova os workflows duplicados `.github/workflows/main.yml` e/ou `.github/workflows/static.yml`, **se** forem exemplos antigos. Não remova `publicar.yml`.

**Atenção:** o arquivo `workflows/publicar.yml` na raiz do repositório não executa GitHub Actions. O caminho correto é `.github/workflows/publicar.yml`.

## Resultado esperado

- Cartões apresentam **manchete + data + fonte**, com **miniatura da publicação** quando encontrada no RSS ou nos metadados públicos da página. Quando não há imagem, o site apresenta um cartão visual de identificação da fonte (não uma captura falsa).
- Clicar na miniatura, na manchete ou em **Ler notícia** abre a matéria.
- Filtros **Todos / Telecom / Ferrovias / Rodovias / etc.** mostram apenas notícias corretamente classificadas. Notícias genéricas ficam em **Todos**, sem aparecer indevidamente em todos os setores.
- **Tipo de atualização** e **Pesquisar notícias…** atuam sobre os cartões, com contador de resultados.
- O botão **Recarregar notícias** lê o JSON já publicado: **não força a execução do coletor no GitHub**. Para antecipar a coleta, utilize **Run workflow**.

A captura de imagem pode não ser possível para manchetes provenientes do Google Notícias ou páginas que bloqueiem a leitura de metadados. O projeto não copia conteúdo de matérias pagas.

## Testes executados

- 9 testes Python do coletor (`python -m unittest discover -s tests -v`).
- Teste de interface Chromium com notícias simuladas: setor, tipo de notícia, busca e renderização de cartões.

Os testes foram feitos com o código do pacote, não diretamente no seu repositório remoto.
