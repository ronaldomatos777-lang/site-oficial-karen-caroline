KAREN CAROLINE IMÓVEIS — V5 PRODUÇÃO
Domínio planejado: www.karencarolineimoveis.com.br

O QUE MUDOU NA V5
- Servidor Flask pronto para produção.
- Gunicorn para hospedagem pública.
- CRM protegido por sessão segura.
- A senha admin não fica fixa no código.
- Banco SQLite pode ser salvo em volume persistente usando DATA_DIR=/data.
- Endpoint /health para o Railway verificar o servidor.
- Headers básicos de segurança.
- Limite simples de tentativas no login e envio de leads.
- WhatsApp configurado: 5519974078273.

PUBLICAÇÃO NO RAILWAY
1. Crie um repositório PRIVADO no GitHub e envie o conteúdo desta pasta.
2. No Railway, crie New Project > Deploy from GitHub Repo e selecione o repositório.
3. No serviço, adicione um Volume e monte em /data.
4. Em Variables, crie:
   ADMIN_PASSWORD = uma senha forte e exclusiva
   SECRET_KEY = uma sequência aleatória longa (mínimo 32 caracteres)
   DATA_DIR = /data
   COOKIE_SECURE = 1
   WHATSAPP_NUMBER = 5519974078273
5. O Railway usará railway.json/Procfile e publicará o site.
6. Gere primeiro o domínio temporário .up.railway.app e teste:
   /              site
   /admin         CRM
   /health        deve mostrar ok=true
7. Em Settings > Public Networking > Custom Domain, adicione:
   www.karencarolineimoveis.com.br
8. O Railway exibirá os registros DNS necessários (CNAME + TXT). COPIE EXATAMENTE os valores exibidos.
9. No Wix: Domínios > karencarolineimoveis.com.br > Gerenciar registros DNS.
10. Altere/crie o CNAME do host www com o destino fornecido pelo Railway.
11. Adicione também o TXT de verificação fornecido pelo Railway.
12. Aguarde a verificação e emissão do SSL.

IMPORTANTE SOBRE O DOMÍNIO SEM WWW
Railway não fornece IP estático para registro A. Como o DNS está no Wix, use www.karencarolineimoveis.com.br como endereço principal. Antes de alterar o domínio raiz, confirme no Wix quais opções de encaminhamento/redirect estão disponíveis para mandar karencarolineimoveis.com.br para https://www.karencarolineimoveis.com.br. Não apague registros de e-mail (MX/TXT) caso existam.

BACKUP DO CRM
O banco fica em /data/leads.db quando publicado. Faça exportações CSV periódicas pelo próprio CRM. O volume persistente é essencial; sem ele, o banco pode ser perdido em novos deploys.

TESTE LOCAL
No Windows, crie um ambiente Python e execute:
  pip install -r requirements.txt
  set ADMIN_PASSWORD=sua-senha
  set SECRET_KEY=uma-chave-longa
  set COOKIE_SECURE=0
  python app.py
Depois abra http://127.0.0.1:5000

OBSERVAÇÃO
A Política de Privacidade atual é um modelo inicial. Antes de tráfego pago em produção, revise dados da corretora/controlador, finalidade, retenção, canal para direitos do titular e demais pontos de LGPD com orientação adequada.
