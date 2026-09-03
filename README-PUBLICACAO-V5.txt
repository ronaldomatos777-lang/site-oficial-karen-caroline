DOCUMENTO HISTÓRICO — KAREN CAROLINE IMÓVEIS / V5 PRODUÇÃO
As instruções atuais de execução, configuração e publicação estão em README.md.
Este arquivo registra o processo usado na versão V5 e não deve ser tratado como manual atual.

O QUE MUDOU NA V5
- Servidor Flask pronto para produção.
- Gunicorn para hospedagem pública.
- CRM protegido por sessão segura.
- A senha admin não fica fixa no código.
- Banco SQLite pode ser salvo em volume persistente usando DATA_DIR=/data.
- Endpoint /health para o Railway verificar o servidor.
- Headers básicos de segurança.
- Limite simples de tentativas no login e envio de leads.
