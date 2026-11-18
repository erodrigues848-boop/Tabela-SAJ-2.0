# Tabela SAJ — Setores regulados | monitoramento automático

Site estático da Tabela SAJ 2026 com **nove setores**, busca, referências legais clicáveis e monitoramento **diário** de manchetes por fontes oficiais e Agência iNFRA. Projeto preparado para **GitHub Pages**, sem servidor contratado e sem chave de API.

> **Importante:** este repositório ficará público se hospedado no GitHub Pages gratuito. Confira se a tabela e seus comentários são adequados à divulgação antes de publicar. Notícias não alteram automaticamente o conteúdo jurídico da tabela.

## Como publicar (forma mais simples: GitHub Desktop)

1. Extraia o ZIP para uma pasta chamada `tabela-saj` no seu computador. Não mova apenas o HTML: mantenha também as pastas `site`, `scripts`, `config`, `tests` e **`.github`**.
2. Instale o [GitHub Desktop](https://desktop.github.com/), entre na sua conta e clique em **File → Add local repository → Choose** (escolha a pasta extraída). Se aparecer **Create a repository here**, clique, crie o repositório e faça o primeiro commit.
3. Clique em **Publish repository**. Recomenda-se o nome `tabela-saj`. Para usar Pages no plano gratuito, publique como **Public**. Confirme que `.github/workflows/publicar.yml` está presente no GitHub.
4. No site GitHub, abra seu repositório e vá a **Settings → Pages → Build and deployment → Source → GitHub Actions**.
5. Acesse **Actions → Atualizar notícias e publicar Tabela SAJ → Run workflow → Run workflow**. O processo baixa notícias e publica a página. A primeira execução automática também ocorre após enviar os arquivos para o branch `main`.
6. O endereço aparece ao terminar o workflow, ou em **Settings → Pages**. Normalmente será `https://SEU-USUARIO.github.io/tabela-saj/`.
7. A coleta ocorrerá **todos os dias às 07h17 (Brasília, UTC-3)**. O agendamento do GitHub Actions pode atrasar; você pode iniciar manualmente no menu **Actions**.

### Alternativa com linha de comando

Crie no GitHub um repositório público vazio chamado `tabela-saj`, depois na pasta do projeto execute (substitua `SEU-USUARIO`):

```bash
git init -b main
git add .
git commit -m "Publicar Tabela SAJ com monitoramento regulatório"
git remote add origin https://github.com/SEU-USUARIO/tabela-saj.git
git push -u origin main
```

Depois faça os passos 4 a 6 acima. Não é necessário criar banco de dados, servidor, domínio pago ou credencial de notícias.

## Como a atualização funciona

- Workflow: `.github/workflows/publicar.yml` — dispara no **push**, diariamente e com comando manual.
- Coletor: `scripts/collect_news.py` — consulta os RSS oficiais configurados em `config/fontes.json`; se um feed falhar, tenta busca RSS no Google Notícias, identificada na página como **agregador**.
- Fonte jornalística: Agência iNFRA (`https://agenciainfra.com/blog/feed/`). Exibimos apenas títulos, datas e links; não reproduzimos o conteúdo de matérias.
- Saída: `site/data/news.json` — gerado automaticamente **na execução do workflow** e incluído na publicação do Pages. **Não há commit automático** do feed no branch `main`.
- Site: `site/index.html` + `site/assets/news.js` — ao abrir a página, lê o JSON publicado, filtra os registros e apresenta a última data da coleta.
- O botão **Recarregar notícias** recarrega a base já publicada; não executa o coletor no GitHub. Para forçar nova coleta, use **Actions → Run workflow**.
- Se todas as fontes falharem, o painel mostra aviso e não apresenta notícias como verificadas. O JSON da última execução está disponível em `.../data/news.json`.

**Avisos jurídicos:** classificação por setor e temas é automatizada por palavras-chave, e pode errar ou omitir assuntos. “Ato normativo: conferir vigência” **não significa** “em vigor”. Verifique o ato em sua publicação oficial antes de alterar a tabela. O texto do balão dos artigos depende de disponibilidade técnica do site público; a referência sempre tem link para abrir a fonte.

## Personalização

- **Acrescentar ou trocar fontes**: edite `config/fontes.json`. Use fontes abertas e preferencialmente RSS público (a URL de cada coleção gov.br pode mudar). A busca Google Notícias é fallback, não a publicação oficial.
- **Horário da atualização**: altere a linha `cron:` de `.github/workflows/publicar.yml` (horário UTC).
- **Palavras-chave e setores**: edite `KEYWORDS`, `SECTOR_KEYWORDS` e `TERM_AREAS` em `scripts/collect_news.py`.
- **Layout**: edite `site/assets/live.css` e `site/assets/news.js`. O HTML consolidado da tabela está em `site/index.html`.
- **Arquivo PDF**: não se atualiza sozinho no GitHub Pages. É recomendável incluir no PDF um link/QR code para a versão online.

## Testar localmente

O projeto não exige pacotes Python externos. Com Python 3.10+:

```bash
python -m unittest discover -s tests -v
python scripts/collect_news.py --allow-empty
python -m http.server 8000 --directory site
```

Abra `http://localhost:8000`. *A abertura direta de `index.html` por `file://` pode bloquear a leitura do JSON por restrições de segurança do navegador.*

## Limitações e cuidados

1. RSS e páginas externas podem mudar, exigir autenticação ou ficar indisponíveis; nenhuma coleta garante cobertura exaustiva. Monitorar o resultado em **Actions** e os avisos na página.
2. O site é estático: sem notificações push, sem envio de e-mail e sem atualização em tempo real; seu conteúdo é atualizado na próxima execução do workflow.
3. A triagem das manchetes **não verifica o texto integral da norma, sua vigência nem consolida alterações legislativas**. As referências da tabela precisam de revisão jurídica humana.
4. GitHub Pages gratuito exige repositório público em contas pessoais com Free. Consulte limites e disponibilidade atuais do GitHub.
5. O workflow pode ser desativado automaticamente após inatividade prolongada do repositório; verifique se o agendamento continua ativo.

## Fontes úteis

- GitHub Pages: https://docs.github.com/pt/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Agendamento do Actions: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- RSS em gov.br: https://www.gov.br/gestaodeconteudo/pt-br/manuais-e-tutoriais/configuracoes-do-ambiente/habilitando-rss
- Agência iNFRA: https://agenciainfra.com/blog/ultimas-noticias/
