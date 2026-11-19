import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import collect_news as c

SAMPLE_RSS=b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Agencia</title>
<item><title>ANTT publica resolucao para concessoes ferroviarias</title><link>https://www.gov.br/antt/pt-br/noticias/ato-x</link><pubDate>Tue, 17 Nov 2026 13:00:00 GMT</pubDate></item>
<item><title>Reuniao interna sem relevancia regulatoria</title><link>https://www.gov.br/antt/pt-br/noticias/evento</link><pubDate>Mon, 16 Nov 2026 13:00:00 GMT</pubDate></item>
</channel></rss>'''
ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title>ANP aprova nova regra sobre gas natural</title>
<link rel="alternate" href="https://www.gov.br/anp/pt-br/noticias/ato-x"/>
<published>2026-11-17T10:00:00Z</published>
</entry></feed>'''

class NewsCollectorTest(unittest.TestCase):
    def test_rss_article_parsing(self):
        articles=c.parse_feed(SAMPLE_RSS)
        self.assertEqual(len(articles),2)
        self.assertEqual(articles[0]['date'],'2026-11-17T13:00:00+00:00')

    def test_atom(self):
        results=c.parse_feed(ATOM)
        self.assertEqual(len(results),1)
        self.assertTrue(results[0]['url'].startswith('https://www.gov.br/anp'))

    def test_reject_untrusted_links(self):
        self.assertEqual(c.safe_url('javascript:alert(1)'),'')
        self.assertEqual(c.safe_url('http://example.com'),'')
        self.assertEqual(c.safe_url('https://foo.local'),'https://foo.local')

    def test_feed_filter_and_sector(self):
        src=json.loads(c.CONFIG.read_text())[1]
        result,status=c.collect_source(src, getter=lambda _: SAMPLE_RSS,
                                       now=datetime(2026,11,18,tzinfo=timezone.utc))
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['setores'],[2])
        self.assertEqual(status['situacao'],'ok')

    def test_fallback(self):
        src=json.loads(c.CONFIG.read_text())[1]
        def mock(url):
            if url.endswith('/RSS'): raise OSError('feed indisponível')
            return SAMPLE_RSS
        result,status=c.collect_source(src,getter=mock,now=datetime(2026,11,18,tzinfo=timezone.utc))
        self.assertEqual(len(result),1)
        self.assertIn('Google',status['via'])

    def test_rss_image_preview(self):
        rss=b'''<rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item>
        <title>ANTT publica resolucao ferroviaria</title>
        <link>https://www.gov.br/antt/pt-br/noticias/123</link>
        <media:thumbnail url="https://www.gov.br/antt/pt-br/imagens/capa.jpg"/>
        <description>Publicacao sobre regras novas.</description>
        </item></channel></rss>'''
        one=c.parse_feed(rss)[0]
        self.assertEqual(one['image'], 'https://www.gov.br/antt/pt-br/imagens/capa.jpg')
        self.assertEqual(one['description'], 'Publicacao sobre regras novas.')

    def test_og_preview_metadata(self):
        src=json.loads(c.CONFIG.read_text())[1]
        html=b'''<html><head><meta property="og:image" content="/imagens/noticia.jpg">
        <meta property="og:description" content="Resumo da publicacao"></head></html>'''
        pic,desc=c.og_preview(src,'https://www.gov.br/antt/pt-br/noticias/ato',getter=lambda _: html)
        self.assertEqual(pic,'https://www.gov.br/imagens/noticia.jpg')
        self.assertEqual(desc,'Resumo da publicacao')

    def test_sector_disambiguation(self):
        sources=json.loads(c.CONFIG.read_text())
        antt,anp,infra=sources[1],sources[4],sources[5]
        self.assertEqual(c.classify_sectors(antt,'ANTT autoriza ferrovia no interior'),[2])
        self.assertEqual(c.classify_sectors(antt,'ANTT regulamenta pedagio em rodovias'),[3])
        self.assertEqual(c.classify_sectors(antt,'ANTT inicia consulta publica de regras gerais'),[])
        self.assertEqual(c.classify_sectors(anp,'ANP aprova regulamento de gasodutos'),[8])
        self.assertEqual(c.classify_sectors(infra,'Agencias analisam novo marco legal'),[])

    def test_manchetes_alheias_ficam_de_fora(self):
        fontes={f['id']:f for f in json.loads(c.CONFIG.read_text())}
        negatives=[
          ('antt','ANTT orienta motoristas durante feriado nas rodovias'),
          ('antt','ANTT divulga campanha educativa em ferrovias'),
          ('anatel','Anatel promove evento sobre telefonia movel'),
          ('aneel','ANEEL divulga dados de consumo de energia eletrica'),
          ('anp','ANP amplia fiscalizacao em postos de combustiveis'),
          ('infra','Agencias discutem os desafios do setor de infraestrutura'),
          ('anac','ANAC anuncia novas vagas para servidores'),
          ('anp','ANP publica nova regra de gas natural sem identificar atividade'),
        ]
        for src,titulo in negatives:
            with self.subTest(titulo=titulo):
                self.assertFalse(c.relevant(titulo, fontes[src]))

    def test_atuacoes_normativas_por_setor(self):
        fontes={f['id']:f for f in json.loads(c.CONFIG.read_text())}
        positives=[
          ('anatel','Anatel aprova resolucao sobre outorga de telecomunicacoes',[1]),
          ('antt','ANTT publica resolucao sobre concessoes ferroviarias',[2]),
          ('antt','ANTT abre consulta publica sobre revisao tarifaria de rodovias',[3]),
          ('anac','ANAC aprova regulamento de concessoes aeroportuarias',[4]),
          ('anac','ANAC abre audiencia publica sobre autorizacao de servicos aereos',[5]),
          ('aneel','ANEEL publica resolucao normativa para distribuicao de energia eletrica',[6]),
          ('anp','ANP publica resolucao sobre concessao e exploracao de petroleo',[7]),
          ('anp','ANP aprova nova resolucao de tarifas de transporte de gas natural',[8]),
          ('anp','ANP abre consulta publica sobre acesso a terminais de GNL',[9]),
          ('infra','ANTT publica novo regulamento de concessoes ferroviarias',[2]),
        ]
        for src,titulo,setores in positives:
            with self.subTest(titulo=titulo):
                self.assertTrue(c.relevant(titulo, fontes[src]))
                self.assertEqual(c.classify_sectors(fontes[src], titulo),setores)

    def test_future_dates_not_publications(self):
        src=json.loads(c.CONFIG.read_text())[1]
        result,_=c.collect_source(src,getter=lambda _:SAMPLE_RSS,
                                  now=datetime(2025,11,18,tzinfo=timezone.utc))
        self.assertEqual(result,[])

if __name__=='__main__':unittest.main()
