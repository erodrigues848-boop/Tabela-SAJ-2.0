# Tabela SAJ 2.0 — correção das marcas e do escopo de notícias

Este pacote substitui **somente a apresentação e o coletor das notícias**; preserva os 9 setores e o texto jurídico já publicado.

## Como atualizar sem GitHub Desktop

1. Faça uma cópia dos arquivos atuais do repositório (opcional, recomendada).
2. **Extraia** o ZIP. Você verá as pastas `site`, `scripts`, `tests` e o arquivo `LEIA-ME.md`. **Não envie o ZIP fechado.**
3. Abra seu repositório: https://github.com/erodrigues848-boop/Tabela-SAJ-2.0
4. Em **Code → Add file → Upload files**, arraste o conteúdo extraído para a área de upload, **mantendo os caminhos das pastas**. Confirme a substituição dos arquivos com os mesmos nomes e clique em **Commit changes**. Se a interface não aceitar a substituição de arquivos existentes, utilize o editor web `github.dev` ou edite os arquivos individualmente no GitHub.
5. Em **Actions**, execute manualmente a automação correta **Atualizar notícias e publicar Tabela SAJ**. Verifique se as etapas `Executar testes locais`, `Atualizar manchetes` e `Publicar site` ficaram verdes. A execução deve gerar um novo `site/data/news.json` no artefato publicado, mesmo sem gravar JSON de volta ao repositório.
6. Abra https://erodrigues848-boop.github.io/Tabela-SAJ-2.0/ e faça **Ctrl + F5**.

> **Não crie outra automação.** O projeto já possuía automações duplicadas. Este pacote não altera os arquivos `.github/workflows`. Use o workflow que já publica a pasta `site` e roda `python scripts/collect_news.py --allow-empty`.

## O que foi alterado

- **9 cabeçalhos**: as nove marcas vetoriais aproximadas foram removidas e substituídas por imagens públicas da identidade visual institucional de Anatel, ANTT, ANAC, Aneel e ANP. O mesmo logotipo é compartilhado pelos setores fiscalizados pela mesma agência. Se o host da imagem estiver indisponível, aparece **apenas a sigla**; o sistema não desenha uma versão inventada.
- **Notícias**: exigem simultaneamente **sinal de mudança normativa** (resolução, regulamentação, consulta pública, minuta, lei, mudança regulatória, revisão tarifária etc.), **tema da tabela** (outorga, tarifa, prazo, investimentos, qualidade etc.) e **setor identificável**. Palavras isoladas como “agência”, “energia” ou “transporte” não bastam.
- **ANP**: notícias de gasodutos de transporte ficam em **Transporte dutoviário de gás**; estocagem, GNL, processamento e gasodutos de escoamento ficam em **Outras atividades relacionadas ao gás**.
- **Notícias antigas**: o JSON de exemplo foi zerado deliberadamente para não continuar mostrando conteúdos que passaram no filtro antigo. A primeira execução do workflow repovoa o painel.
- **Defesa adicional na página**: o navegador só exibe notícias novas sinalizadas `escopo = normativo` e classificadas em um setor; isso impede a reaparição de cartões genéricos que estavam na base anterior.

## Verificação das marcas

- **Anatel**: coleção de imagens institucional https://www.gov.br/anatel/pt-br/centrais-de-conteudo/anatel-002-png — visual original, com reserva de fallback quando o link de imagem não funcionar.
- **ANTT**: manual de identidade https://www.gov.br/antt/pt-br/centrais-de-conteudo/manual-de-identidade-visual — reprodução pública da marca em imagem externa.
- **ANAC**: imagem publicada em domínio oficial `aeronaves.anac.gov.br`; manual de identidade https://www2.anac.gov.br/arquivos/manual%20ANAC/MANUAL%20DE%20IDENTIDADE%20VISUAL%20MARCA%20%20ANAC.pdf
- **Aneel**: marca institucional reproduzida em imagem pública hospedada externamente; portal para conferência https://www.gov.br/aneel/pt-br
- **ANP**: marca institucional reproduzida em imagem pública hospedada externamente; portal para conferência https://www.gov.br/anp/pt-br

**Importante**: algumas imagens são reproduções públicas hospedadas em terceiros, não arquivos baixados diretamente das agências. As marcas servem à **identificação das fontes**, sem alegar parceria ou endosso das agências. O uso de certas marcas pode estar sujeito às regras de identidade institucional (especialmente a Anatel). Para uso institucional formal, obtenha os arquivos e autorização diretamente da agência.

## Limites de automatização

- **Filtro rigoroso = menos notícias**. A ausência de notícias não significa que nenhuma norma tenha mudado.
- A triagem é feita pelo **título** do RSS (não certifica que a norma exista, esteja vigente, ou altere a Tabela SAJ).
- Para cada atualização, verificar a norma oficial, sua data de publicação e seus efeitos antes de modificar a tabela jurídica.
- As fotos das matérias, quando fornecidas pelo RSS/OG, continuam opcionais. A falta de foto não gera uma captura fictícia.
- Fontes RSS e sites de imagens externos podem alterar endereços ou bloquear requisições no futuro.

## Testes

```bash
python -m unittest discover -s tests -v
```

Testes locais passaram: classificação de 9 setores, notícias irrelevantes, filtros, pesquisa e integridade do HTML/JS.
