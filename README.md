# Crawler IA — Escolas e Creches

Sistema em Docker para pesquisar sites de escolas e creches, rastrear páginas de contactos com Scrapy, guardar emails institucionais em PostgreSQL e exportar CSV para importação manual na Keila.

## Instalação

```bash
git clone https://github.com/smartlearningci/crawler-ia.git
cd crawler-ia
cp .env.example .env
# editar .env e alterar as passwords
docker compose up -d --build
```

Interface: http://localhost:8080

## Arrancar Keila (opcional)

Configura antes `KEILA_DB_PASSWORD`, `KEILA_USER`, `KEILA_PASSWORD` e `KEILA_SECRET_KEY_BASE` no `.env` (gerar chave: `openssl rand -hex 64`). Depois:

```bash
docker compose --profile keila up -d --build
```

Keila: http://localhost:4000. A imagem oficial é `pentacent/keila:0.40.2`.

## Pesquisa

Escreve termos como `escolas Lisboa` ou `creches Lisboa` na interface. O motor predefinido é Bing HTML (experimental). Em alternativa, podes configurar uma API Google Programmable Search com `SEARCH_ENGINE=google_api`, `SEARCH_API_KEY` e `SEARCH_CX`. O crawler respeita `robots.txt`, trabalha com atrasos entre pedidos e percorre links internos até à profundidade escolhida.

## Exportação

O CSV completo inclui email, escola, responsável (por preencher quando não conhecido), saudação, website, fonte, pesquisa e data. O CSV para Keila inclui email, first_name, last_name, school e greeting. Confirma o mapeamento e revê os contactos antes de importar.

## Gestão

```bash
docker compose ps
docker compose logs -f web
git pull
docker compose up -d --build
```

Não uses `docker compose down -v` se quiseres manter os dados.

## Limitações

Versão inicial: a pesquisa Bing depende de HTML e pode falhar, sites carregados apenas por JavaScript podem não ser processados, a identificação de escolas é aproximada e não existe identificação automática fiável dos responsáveis. Não existe envio automático de emails. A publicação do endereço num website não significa consentimento para marketing. Verifica sempre a base legal e os requisitos de oposição antes de contactar destinatários.
