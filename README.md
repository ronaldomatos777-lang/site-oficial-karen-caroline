# Karen Caroline Imóveis — site e CRM

Este é o documento operacional atual do projeto. Os arquivos `README-*.txt` permanecem no repositório apenas como histórico de versões e não devem ser usados como instrução de publicação.

## Tecnologias e estrutura

- `app.py`: aplicação Flask, API de leads/eventos, CRM administrativo, exportação CSV e entrega controlada das páginas/assets.
- `*.html`: página inicial, empreendimentos e política de privacidade.
- `script.js`: formulários, UTMs, idempotência, fila offline, eventos, WhatsApp, agendamento, galerias e lightboxes.
- `style.css`: estilos compartilhados; o Casa Prado também possui ajustes visuais inline próprios.
- `social-links.js`: ativa redes sociais somente quando URLs oficiais forem configuradas.
- `assets/`: imagens públicas dos empreendimentos.
- `data/leads.db`: banco SQLite local (criado automaticamente e ignorado pelo Git).
- `Procfile` e `railway.json`: execução com Gunicorn no Railway.
- `backup-crm.bat` e `iniciar-site.bat`: utilitários Windows.

## Execução local

Requer Python 3.11 ou superior. No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:ADMIN_PASSWORD = "defina-uma-senha-forte"
$env:SECRET_KEY = "defina-uma-chave-aleatoria-longa"
$env:COOKIE_SECURE = "0"
python app.py
```

Acesse `http://127.0.0.1:5000/` e o CRM em `http://127.0.0.1:5000/admin`. No Windows, `iniciar-site.bat` também inicia a aplicação, desde que Python e as dependências estejam instalados. Não existe senha administrativa padrão: `ADMIN_PASSWORD` deve ser definida.

## Banco de dados

### SQLite

Sem `DATABASE_URL`, o sistema usa SQLite. O caminho padrão é `data/leads.db`; `DATA_DIR` ou `DB_PATH` podem alterar o local. O esquema e as colunas incrementais são criados na inicialização sem apagar leads existentes. Arquivos `.db`, WAL e SHM não devem ser versionados.

### PostgreSQL e Railway

Com `DATABASE_URL` definida, o sistema usa PostgreSQL por meio do `psycopg`. No Railway:

1. configure `DATABASE_URL` com o PostgreSQL do projeto;
2. configure todas as variáveis sensíveis abaixo;
3. mantenha o comando Gunicorn de `railway.json`/`Procfile`;
4. valide `/health` após o deploy.

Se optar por SQLite no Railway, monte volume persistente e use `DATA_DIR=/data`. Sem volume, o banco local pode ser perdido em novos deploys.

## Variáveis de ambiente

- `ADMIN_PASSWORD` (obrigatória para acessar o CRM): senha forte e exclusiva.
- `SECRET_KEY` (obrigatória em produção): chave aleatória longa para sessões e CSRF.
- `WHATSAPP_NUMBER`: número oficial em formato internacional, somente dígitos; o padrão atual preserva o atendimento existente.
- `DATABASE_URL`: ativa PostgreSQL quando preenchida.
- `DATA_DIR`: diretório dos dados SQLite; padrão local `data/`.
- `DB_PATH`: caminho completo alternativo do banco SQLite.
- `COOKIE_SECURE`: use `1` com HTTPS em produção e `0` apenas no desenvolvimento HTTP local.
- `ALLOWED_ORIGINS`: origens aceitas pela API, separadas por vírgula.
- `PORT`: porta fornecida pela hospedagem; localmente o Flask usa 5000.

Copie `.env.example` apenas como referência. O aplicativo não carrega `.env` sozinho; defina as variáveis no sistema ou na plataforma. Nunca versione `.env`, bancos, backups ou exportações de leads.

## CRM e APIs

- `/admin`: login do CRM.
- `/admin/leads`: busca, filtros e funil de leads.
- `/admin/lead`: detalhes e observações.
- `/admin/exportar.csv`: exportação protegida contra CSV Injection.
- `/api/leads`: cadastro de leads com validação, rate limit e idempotência.
- `/api/events`: eventos de navegação/conversão, incluindo `lead_id` e `interesse` quando aplicáveis.
- `/api/config`: configuração pública necessária ao frontend.
- `/whatsapp`: redirecionamento para o número oficial configurado.
- `/health`: verificação de saúde da aplicação.

Alterações administrativas usam sessão e token CSRF. A aplicação aceita SQLite e PostgreSQL, mas ainda não utiliza Alembic.

## Leads, idempotência e fila offline

Cada envio do frontend recebe uma `idempotency_key`. Se a resposta se perder e a mesma solicitação for reenviada, a restrição única no banco devolve o lead já criado em vez de duplicá-lo. Um novo envio legítimo gera outra chave e continua permitido.

Quando a API está indisponível, o navegador guarda temporariamente até 20 leads no `localStorage`. A fila expira em 24 horas, elimina entradas antigas/corrompidas e reutiliza a mesma chave no reenvio. Por conter dados pessoais, esse armazenamento deve continuar limitado e temporário.

## WhatsApp

`WHATSAPP_NUMBER` no backend é a fonte única do número. O frontend obtém a configuração por `/api/config`, e links diretos usam `/whatsapp`. Mensagens contextuais preservam empreendimento, página e UTMs. Não replique o número em HTML ou JavaScript.

## Backup

Para SQLite local, feche gravações concorrentes e execute `backup-crm.bat`; o script copia `data/leads.db` para `backups/leads-AAAAmmdd-HHMMSS.db`. A pasta de backup é ignorada pelo Git. Para PostgreSQL, use o mecanismo de backup/exportação oferecido pelo provedor e teste periodicamente a restauração. A exportação CSV do CRM auxilia operações, mas não substitui backup consistente do banco.

## Segurança básica

- O Flask publica apenas as páginas e assets permitidos; arquivos Python, `.env`, Git, bancos, scripts, READMEs e arquivos de implantação não são servidos.
- Use HTTPS, `COOKIE_SECURE=1`, segredos exclusivos e acesso restrito ao painel.
- Não armazene credenciais no repositório nem envie bancos/exportações para o Git.
- O rate limit atual é em memória e por processo do Gunicorn; é uma proteção básica, não um limitador distribuído.
- Revise a Política de Privacidade e os procedimentos de retenção conforme a LGPD antes de campanhas em produção.

## Casa Prado e material completo

Não existe PDF de material completo no projeto nem interface pública ativa para baixá-lo. O formulário normal de contato, as plantas, a galeria e o agendamento do Casa Prado permanecem ativos. Não adicione CTA de download sem primeiro disponibilizar um material real e definir um fluxo aprovado.

## Inventário técnico e histórico

Classificação revisada na ETAPA 4:

- Necessário em produção: `app.py`, HTMLs nomeados, `script.js`, `style.css`, `social-links.js`, `assets/`, `robots.txt`, `sitemap.xml`, `requirements.txt`, `Procfile` e `railway.json`.
- Necessário para operação local: `.env.example`, `.gitignore`, `iniciar-site.bat` e `backup-crm.bat`.
- Necessário apenas como histórico: `README-V5*.txt`, `README-CRM.txt`, `README-LEADS.txt`, `README-PUBLICACAO-V5.txt` e `README-WHATSAPP.txt`.
- Obsoleto: `update_v535.py` (script pontual com caminho `/mnt/data/v535`) e `.html` (cópia antiga da página Universo). Ambos ficam fora da lista pública do Flask.
- Backup preservado e não rastreado: `app_backup_sqlite.py`; não é importado nem publicado.
- Duplicados binariamente idênticos confirmados por SHA-256: `assets/universo/conceito-alt.webp` / `conceito.webp`; `assets/seleto/hero.webp` / `galeria/seleto-17.webp`; `assets/casa/hero-fachada.webp` / `hero.webp`; `assets/seleto/localizacao.webp` / `galeria/seleto-01.webp`. Permanecem porque nomes referenciados fazem parte da organização atual.
- Aparentemente não utilizados, mas preservados: `assets/visit-consultora-v521.png`, `assets/alta/aerea.webp`, `assets/cores/aerea.webp`, `apto2.webp`, `implantacao.webp`, `lazer.webp`, `piscina.webp`, `portaria.webp` e `assets/universo/conceito-alt.webp`.

Nenhum arquivo histórico ou asset deve ser removido sem nova revisão de referências e autorização.
