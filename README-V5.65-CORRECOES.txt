V5.65 — Consolidação segura

Base utilizada: commit 0468e8d (versão para a qual o Render foi revertido).

Correções aplicadas:
- Home mobile: seção Empreendimentos em uma única coluna, sem título espremido.
- Modal Agendar Visita: foto com foco superior, data identificada, campos padronizados e checkbox 18x18.
- Script do modal centralizado no script.js para evitar duplicidade de comportamento.
- Universo Parque Alphaville: removidos menu/modal/agendamento duplicados; CTAs usam o script compartilhado.
- WhatsApp contextual e flutuante passam pelo mesmo número/configuração do script.js.
- Universo mobile: localização, benefícios e imagem de investimento protegidos contra cortes/overflow.
- Removido texto de instruções que havia sido colado acidentalmente dentro do style.css.
- Cache-busting atualizado para v=565-clean.

Antes de publicar: testar Home e Universo em desktop/mobile e então Commit/Push no GitHub Desktop.
