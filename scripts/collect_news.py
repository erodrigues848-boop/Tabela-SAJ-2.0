#!/usr/bin/env python3
"""Coletor de metadados públicos de notícias para GitHub Pages.

- RSS oficial primeiro, Google Notícias RSS como contingência sinalizada.
- O resultado NÃO atesta a vigência de nenhum ato.
- Não reproduz matérias, apenas manchete, data e endereço da fonte.
- Somente urllib/XML e biblioteca padrão, sem tokens nem banco de dados.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'fontes.json'
OUTPUT = ROOT / 'site' / 'data' / 'news.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; SAJ-PainelRegulatorio/1.0; consulta-publica; +https://github.com)',
    'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.6',
}
MAX_AGE_DAYS = 150
MAX_PER_SOURCE = 15
MAX_TOTAL = 70
# HTML de manchetes publicado por fontes oficiais; nunca é obrigatório para a coleta.
MAX_OG_PER_SOURCE = 5
KEYWORDS = (
    'resoluc', 'normativ', 'regulament', 'legisl', 'decreto', 'portaria',
    'consulta publica', 'audiencia publica', 'concess', 'autoriz', 'outorga',
    'revisao tarifaria', 'tarifa', 'agencia', 'marco legal', 'seguranca operacional',
    'contrato', 'lei ', 'fiscaliz', 'licitac', 'leilao', 'renov', 'prorrog',
    'ferrovi', 'rodovi', 'aeroport', 'energia', 'gas natural', 'petroleo',
    'telecomunic', 'publica', 'homologa', 'diretriz', 'transporte'
)
SECTOR_KEYWORDS = {
    1: ('anatel', 'telecom', 'telefonia', 'banda larga', 'espectro', '5g', 'radiofrequencia'),
    2: ('ferrovi', 'trem', 'trilho', 'malha ferrovi', 'atf', 'ferrovia'),
    3: ('rodovi', 'pedagio', 'onibus', 'fretamento', 'frete rodoviario', 'caminhao', 'br-'),
    4: ('aeroporto', 'aerodromo', 'infraestrutura aeroportuaria'),
    5: ('aviacao', 'aereo', 'aerea', 'aeronave', 'companhia aerea', 'voo', 'passageiros aereos'),
    6: ('aneel', 'eletric', 'energia', 'geracao', 'transmissao', 'distribuicao', 'comercializacao'),
    7: ('petroleo', 'combustiv', 'refin', 'oleo', 'pre sal', 'exploracao e producao'),
    8: ('gasoduto', 'transporte de gas', 'transportador de gas', 'capacidade de transporte', 'malha de transporte de gas'),
    9: ('gnl', 'estocagem', 'regaseific', 'liquefac', 'processamento de gas', 'acondicionamento de gas'),
}
TERM_AREAS = {
    'Licitação e outorga': ('licitacao', 'leilao', 'outorga', 'concessao', 'autorizacao', 'permissao', 'edital'),
    'Prazo e prorrogação': ('prazo', 'prorrogacao', 'vigencia', 'renovacao', 'extensao'),
    'Tarifas e remuneração': ('tarifa', 'reajuste', 'remuneracao', 'preco', 'pedagio', 'revisao tarifaria'),
    'Qualidade e segurança': ('qualidade', 'desempenho', 'fiscalizacao', 'seguranca', 'indicador'),
    'Infraestrutura e investimentos': ('investimento', 'obras', 'infraestrutura', 'expansao', 'capacidade'),
    'Normas gerais': ('resolucao', 'lei ', 'decreto', 'regulamento', 'norma', 'portaria'),
}


def norm(text: str) -> str:
    text = unicodedata.normalize('NFD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()


def safe_text(text: str) -> str:
    text = re.sub(r'<[^>]*>', ' ', html.unescape(text or ''))
    return re.sub(r'\s+', ' ', text).strip()


def safe_url(url: str) -> str:
    url = html.unescape(url.strip())
    try:
        p = urlsplit(url)
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            return ''
        if p.hostname in {'localhost', '127.0.0.1', '::1'}:
            return ''
        return url
    except ValueError:
        return ''


def fetch(url: str, timeout: int = 17) -> bytes:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as res:
        if res.status >= 400:
            raise RuntimeError(f'HTTP {res.status}')
        payload = res.read(2_500_001)
        if len(payload) > 2_500_000:
            raise RuntimeError('Feed acima do tamanho máximo permitido')
        return payload


def tag(element):
    return element.tag.rsplit('}', 1)[-1].lower()


def child_text(element, name: str):
    for item in element:
        if tag(item) == name:
            return (item.text or '').strip()
    return ''


def date_iso(raw: str):
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (ValueError, TypeError, IndexError):
        try:
            dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds')


class ArticleMetaParser(HTMLParser):
    """Lê somente metadados de prévia publicados pela fonte, sem copiar o artigo."""
    def __init__(self):
        super().__init__()
        self.image = ''
        self.description = ''

    def handle_starttag(self, t, attrs):
        if t.lower() != 'meta':
            return
        d = dict(attrs)
        key = (d.get('property') or d.get('name') or '').lower()
        value = d.get('content', '')
        if key in ('og:image', 'twitter:image', 'twitter:image:src') and not self.image:
            self.image = value
        elif key in ('og:description', 'description') and not self.description:
            self.description = safe_text(value)[:140]


def og_preview(source: dict, article_url: str, getter=fetch):
    """Prévia opcional para links diretos em domínios públicos configurados."""
    target = urlsplit(article_url)
    host = (target.hostname or '').lower()
    allowed = source.get('dominios', [])
    if not host or not any(host == d or host.endswith('.' + d) for d in allowed):
        return '', ''
    if host in ('news.google.com',):
        return '', ''
    try:
        payload = getter(article_url)
        if len(payload) > 650_000:
            payload = payload[:650_000]
        meta = ArticleMetaParser()
        meta.feed(payload.decode('utf-8', errors='replace'))
        return safe_url(urljoin(article_url, meta.image)) if meta.image else '', meta.description
    except (ValueError, UnicodeError, OSError, RuntimeError, TimeoutError):
        return '', ''


def feed_image(node):
    for el in node.iter():
        name = tag(el)
        typ = el.attrib.get('type', '').lower()
        candidate = el.attrib.get('url', '') or el.attrib.get('href', '')
        if name in ('thumbnail', 'image') and candidate:
            if safe_url(candidate):
                return safe_url(candidate)
        if name in ('enclosure', 'content') and candidate and (typ.startswith('image/') or re.search(r'\.(?:png|jpe?g|webp)(?:[?#]|$)', candidate, re.I)):
            if safe_url(candidate):
                return safe_url(candidate)
    return ''


def parse_feed(payload: bytes):
    root = ET.fromstring(payload)
    if tag(root) not in ('rss', 'rdf', 'feed'):
        raise ValueError('XML não reconhecido como RSS/Atom')
    result = []
    for node in root.iter():
        if tag(node) not in ('item', 'entry'):
            continue
        title = safe_text(child_text(node, 'title'))
        link = child_text(node, 'link')
        if not link:
            links = [x for x in node if tag(x) == 'link']
            if links:
                link = next((x.attrib.get('href') for x in links if x.attrib.get('rel') in (None, 'alternate')), '') or ''
        date = (child_text(node, 'pubdate') or child_text(node, 'published')
                or child_text(node, 'updated') or child_text(node, 'date'))
        if title and safe_url(link):
            result.append({'title': title, 'url': safe_url(link), 'date': date_iso(date),
                           'image': feed_image(node),
                           'description': safe_text(child_text(node, 'description') or child_text(node, 'summary'))[:140]})
    return result


def classify_status(title: str) -> str:
    text = norm(title)
    if any(x in text for x in ('consulta publica', 'audiencia publica', 'abre consulta', 'submete a consulta')):
        return 'Consulta / participação'
    if any(x in text for x in ('proposta', 'propoe', 'estuda', 'discute', 'minuta', 'pretende')):
        return 'Proposta / discussão'
    if any(x in text for x in ('resolucao', 'decreto', 'portaria', 'lei ', 'norma', 'regulamento')):
        return 'Ato normativo: conferir vigência'
    if any(x in text for x in ('leilao', 'concessao', 'edital', 'contrato')):
        return 'Outorga / contrato'
    return 'Notícia setorial'


def classify_sectors(source: dict, title: str) -> list[int]:
    """Nunca atribui a todos os setores uma manchete sem tema reconhecível."""
    text = norm(title)
    match = [n for n in source['setores'] if any(term in text for term in SECTOR_KEYWORDS[n])]
    if source['id'] == 'antt':
        ferro = 2 in match
        rodo = 3 in match
        return ([2] if ferro else []) + ([3] if rodo else [])
    if source['id'] == 'anp':
        # "gás natural" isolado não basta para decidir entre transporte e estocagem.
        gas = 'gas natural' in text
        specific = [n for n in match if n in (8, 9)]
        if specific:
            return specific
        if gas and not any(t in text for t in ('petroleo', 'combustiv', 'refin', 'pre sal')):
            return []
        return [7] if 7 in match else []
    if len(source['setores']) == 1:
        return source['setores']
    # Publicações amplas de agência/veículo ficam em "Todos" até identificarmos setor.
    return match


def areas(title: str) -> list[str]:
    text = norm(title)
    return [area for area, keys in TERM_AREAS.items() if any(k in text for k in keys)][:3] or ['Acompanhamento setorial']


def relevant(title: str) -> bool:
    text = norm(title)
    return any(term in text for term in KEYWORDS)


def search_feed(query: str):
    return 'https://news.google.com/rss/search?' + urlencode({
        'q': query + ' when:90d', 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'
    })


def collect_source(source: dict, *, getter=fetch, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    logs = []
    data = []
    channel = 'RSS oficial'
    if source.get('rss'):
        try:
            data = parse_feed(getter(source['rss']))
            logs.append(f'RSS: {len(data)} entradas')
        except Exception as exc:
            logs.append(f'RSS indisponível ({type(exc).__name__})')
    if not data or not any(relevant(entry['title']) for entry in data):
        channel = 'Busca de notícias (Google Notícias)'
        try:
            data = parse_feed(getter(search_feed(source['busca'])))
            logs.append(f'Busca: {len(data)} entradas')
        except Exception as exc:
            logs.append(f'Busca indisponível ({type(exc).__name__})')
    result = []
    seen = set()
    og_tries = 0
    for item in data:
        if not relevant(item['title']) or item['url'] in seen:
            continue
        date = item['date']
        if date:
            dt = datetime.fromisoformat(date)
            if dt < now - timedelta(days=MAX_AGE_DAYS) or dt > now + timedelta(days=2):
                continue
        seen.add(item['url'])
        key = hashlib.sha256(item['url'].encode('utf-8')).hexdigest()[:14]
        img = item.get('image') or ''
        excerpt = item.get('description') or ''
        if not img and og_tries < MAX_OG_PER_SOURCE:
            # Evita buscas adicionais a páginas intermediárias do Google Notícias.
            host = (urlsplit(item['url']).hostname or '').lower()
            if any(host == d or host.endswith('.' + d) for d in source.get('dominios', [])):
                og_tries += 1
                img, og_excerpt = og_preview(source, item['url'], getter=getter)
                excerpt = excerpt or og_excerpt
        result.append({
            'id': key,
            'titulo': item['title'][:210],
            'imagem': safe_url(img) if img else '',
            'descricao': excerpt[:140],
            'url': item['url'],
            'publicado_em': date,
            'fonte': source['nome'],
            'canal': channel,
            'setores': classify_sectors(source, item['title']),
            'categoria': classify_status(item['title']),
            'temas': areas(item['title']),
            'atencao': 'Triagem automática: verificar publicação, vigência e alcance antes de alterar a tabela.'
        })
        if len(result) >= MAX_PER_SOURCE:
            break
    status = 'ok' if data else 'indisponível'
    return result, {
        'nome': source['nome'], 'situacao': status, 'via': channel,
        'quantidade': len(result), 'observacao': '; '.join(logs)[:170]
    }


def execute(getter=fetch, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    sources = json.loads(CONFIG.read_text(encoding='utf-8'))
    stories, report = [], []
    with ThreadPoolExecutor(max_workers=min(7, len(sources))) as pool:
        jobs = {pool.submit(collect_source, s, getter=getter, now=now): s for s in sources}
        for future in as_completed(jobs):
            source = jobs[future]
            try:
                batch, status = future.result()
                stories.extend(batch)
                report.append(status)
            except Exception as exc:
                report.append({'nome': source['nome'], 'situacao': 'erro', 'via': '-', 'quantidade': 0,
                               'observacao': type(exc).__name__})
    uniq = {}
    for item in sorted(stories, key=lambda s: s['publicado_em'] or '', reverse=True):
        uniq.setdefault(item['url'], item)
    ordered = list(uniq.values())[:MAX_TOTAL]
    return {
        'atualizado_em': now.isoformat(timespec='seconds'),
        'coleta': 'automática',
        'total': len(ordered),
        'noticias': ordered,
        'fontes': sorted(report, key=lambda r: r['nome']),
        'aviso': 'Manchetes para triagem jurídica. Notícia não confirma, por si, publicação nem vigência de norma.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(OUTPUT), help='Destino JSON gerado')
    parser.add_argument('--allow-empty', action='store_true', help='Publica mesmo sem notícias, com aviso explícito')
    args = parser.parse_args()
    dest = Path(args.output)
    response = execute()
    if response['total'] == 0 and not args.allow_empty:
        print('ERRO: nenhuma notícia recuperada; publicação interrompida para evitar feed vazio.', file=sys.stderr)
        for entry in response['fontes']:
            print(f"  {entry['nome']}: {entry['observacao']}", file=sys.stderr)
        return 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Atualização {response['atualizado_em']}: {response['total']} notícias")
    for s in response['fontes']:
        print(f" - {s['nome']}: {s['quantidade']} ({s['via']}; {s['situacao']})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
