from pathlib import Path
from urllib.parse import quote

root = Path('/mnt/data/v535')
html_path = root/'universo-parque-alphaville.html'
css_path = root/'style.css'
html = html_path.read_text(encoding='utf-8')

# Metadata: more precise but still clearly pre-launch information.
html = html.replace(
    'content="Conheça o Universo Riva no Parque Alphaville, em Campinas: pré-lançamento com apartamentos de 2 e 3 dormitórios, suíte e varanda gourmet."',
    'content="Universo Parque Alphaville, pré-lançamento Riva em Campinas: apartamentos de 55 m² e 84 m², 2 e 3 dormitórios, varanda, suíte e lazer completo. Consulte disponibilidade e condições."',
    1
)
html = html.replace(
    'content="Pré-lançamento no Parque Alphaville, em Campinas, com proposta de apartamentos de 2 e 3 dormitórios, suíte e varanda gourmet."',
    'content="Pré-lançamento no Parque Alphaville, em Campinas: unidades divulgadas de 55 m² e 84 m², com 2 e 3 dormitórios, varanda, suíte e lazer completo."',
    1
)

old_intro = '''<section class="universo-intro" id="detalhes"><div><p class="eyebrow">UNIVERSO RIVA</p><h2>Parque Alphaville ganha um novo jeito de morar.</h2></div><div><p>O material de lançamento apresenta o Universo Riva como o primeiro projeto de apartamentos no Parque Alphaville, reunindo localização estratégica, mobilidade, lazer e uma proposta contemporânea de condomínio.</p><div class="universo-facts"><span><b>2 e 3</b>dormitórios</span><span><b>Suíte</b>nas opções divulgadas</span><span><b>Varanda</b>gourmet</span><span><b>Em breve</b>pré-lançamento</span></div></div></section>'''
new_intro = '''<section class="universo-intro" id="detalhes"><div><p class="eyebrow">UNIVERSO RIVA</p><h2>Parque Alphaville ganha um novo jeito de morar.</h2></div><div><p>O Universo Parque Alphaville chega como o primeiro projeto de apartamentos do bairro, reunindo proposta contemporânea, mobilidade, lazer e duas tipologias divulgadas para diferentes momentos de vida.</p><div class="universo-facts"><span><b>55 m²</b>2 dormitórios</span><span><b>84 m²</b>3 dormitórios</span><span><b>Suíte</b>em tipologia divulgada</span><span><b>Varanda</b>nas opções apresentadas</span></div></div></section>
<section class="universo-specs" aria-label="Tipologias e ficha preliminar"><div class="universo-specs-head"><p class="eyebrow">INFORMAÇÕES PRELIMINARES</p><h2>Duas plantas pensadas para rotinas diferentes.</h2><p>Dados divulgados para o pré-lançamento. Disponibilidade, vagas, memorial e condições comerciais devem ser confirmados no atendimento.</p></div><div class="universo-spec-grid"><article><span class="spec-size">55 m²</span><h3>2 dormitórios</h3><p>Varanda, 1 vaga e planta compacta com distribuição funcional.</p></article><article><span class="spec-size">84 m²</span><h3>3 dormitórios com suíte</h3><p>Varanda, até 2 vagas e configuração voltada a quem busca mais espaço.</p></article><article><span class="spec-size">Lazer</span><h3>Condomínio completo</h3><p>Piscina, espaço gourmet e ambientes de convivência aparecem entre os itens divulgados.</p></article><article><span class="spec-size">Em breve</span><h3>Pré-lançamento</h3><p>O material público consultado indica previsão de lançamento para outubro, sujeita a confirmação.</p></article></div></section>'''
if old_intro not in html:
    raise SystemExit('intro block not found')
html = html.replace(old_intro, new_intro)

old_location = '''<section class="universo-location"><div class="universo-location-copy"><p class="eyebrow">LOCALIZAÇÃO</p><h2>No centro de conexões importantes.</h2><p>O material destaca a proximidade com Parque Taquaral, acesso à Rodovia Dom Pedro I e Parque Dom Pedro Shopping, reforçando a conveniência da região.</p><a class="btn universo-gold" href="#contato">Receber informações</a></div><figure><img src="assets/universo/localizacao.webp" width="1052" height="1495" loading="lazy" alt="Material de localização do Universo Riva Parque Alphaville"></figure></section>'''
new_location = '''<section class="universo-location"><div class="universo-location-copy"><p class="eyebrow">LOCALIZAÇÃO</p><h2>Conveniência e mobilidade no entorno.</h2><p>O Parque Alphaville está conectado a importantes eixos de Campinas. O material público do lançamento destaca a proximidade com centros de compras, universidades e acessos rodoviários.</p><div class="universo-location-points"><span><b>≈ 5 min</b>Parque Dom Pedro Shopping</span><span><b>Poucos minutos</b>Galleria Shopping</span><span><b>Acesso rápido</b>PUC Campinas</span><span><b>Região próxima</b>Barão Geraldo e Unicamp</span><span><b>Conexão viária</b>Rodovias Dom Pedro I e Anhanguera</span></div><a class="btn universo-gold" href="#contato">Receber informações</a></div><figure><img src="assets/universo/localizacao.webp" width="1052" height="1495" loading="lazy" alt="Material de localização do Universo Riva Parque Alphaville"></figure></section>'''
if old_location not in html:
    raise SystemExit('location block not found')
html = html.replace(old_location, new_location)

old_benefits = '''<section class="universo-benefits"><div class="section-head"><div><p class="eyebrow">POR QUE CONHECER</p><h2>Diferenciais apresentados para o lançamento.</h2></div><p>Uma leitura organizada do material recebido, sem substituir a confirmação das condições comerciais no atendimento.</p></div><div class="universo-benefit-grid"><article><b>01</b><h3>Localização estratégica</h3><p>Parque Alphaville Campinas, com acesso facilitado a importantes pontos da região.</p></article><article><b>02</b><h3>Plantas inteligentes</h3><p>Opções divulgadas de 2 e 3 dormitórios, com suíte e varanda gourmet.</p></article><article><b>03</b><h3>Condomínio moderno</h3><p>Proposta contemporânea, lazer completo e espaços pensados para a rotina.</p></article><article><b>04</b><h3>Morar ou investir</h3><p>O material promocional destaca o potencial imobiliário da região e a versatilidade do projeto.</p></article></div></section>'''
new_benefits = '''<section class="universo-benefits"><div class="section-head"><div><p class="eyebrow">POR QUE CONHECER</p><h2>Um projeto que combina localização, plantas e lazer.</h2></div><p>Os diferenciais abaixo reúnem informações divulgadas para o pré-lançamento e ajudam a comparar o projeto com o seu momento de vida.</p></div><div class="universo-benefit-grid"><article><b>01</b><h3>Parque Alphaville</h3><p>Primeiro projeto de apartamentos apresentado para o bairro, em uma área conectada a importantes serviços de Campinas.</p></article><article><b>02</b><h3>55 m² e 84 m²</h3><p>Duas tipologias divulgadas, com 2 e 3 dormitórios, varanda e opção com suíte.</p></article><article><b>03</b><h3>Lazer e convivência</h3><p>Piscina, espaço gourmet e áreas de convivência aparecem entre os itens apresentados para o condomínio.</p></article><article><b>04</b><h3>Mobilidade</h3><p>Acesso facilitado à Rodovia Dom Pedro I, Anhanguera e importantes pontos comerciais e educacionais da região.</p></article></div></section>'''
if old_benefits not in html:
    raise SystemExit('benefits block not found')
html = html.replace(old_benefits, new_benefits)

old_invest = '''<section class="universo-invest"><img src="assets/universo/investimento.webp" width="1779" height="884" loading="lazy" alt="Diferenciais do Universo Parque Alphaville"><div><p class="eyebrow">VISÃO GERAL</p><h2>Um lançamento apresentado para morar e também considerar como investimento.</h2><p>Entre os pontos destacados no material estão localização, acesso às principais rodovias, lazer, apartamentos com varanda, plantas inteligentes e condomínio moderno.</p><a class="btn universo-gold" href="https://wa.me/5519974078273?text=Ol%C3%A1%21%20Vim%20pelo%20site%20e%20quero%20receber%20as%20condi%C3%A7%C3%B5es%20de%20pr%C3%A9-lan%C3%A7amento%20do%20Universo%20Riva%20Parque%20Alphaville." target="_blank" rel="noopener">Quero condições de pré-lançamento</a></div></section>'''
new_invest = '''<section class="universo-invest"><div class="universo-invest-media"><img src="assets/universo/investimento.webp" width="1779" height="884" loading="lazy" alt="Diferenciais do Universo Parque Alphaville"></div><div class="universo-invest-copy"><p class="eyebrow">VISÃO GERAL</p><h2>Um endereço para morar — e para avaliar com visão patrimonial.</h2><p>A localização, a oferta de serviços no entorno, a mobilidade e as duas tipologias divulgadas tornam o empreendimento relevante tanto para quem procura moradia quanto para quem está estudando uma aquisição imobiliária de longo prazo.</p><p class="universo-disclaimer">Potencial de valorização não representa garantia de retorno. Valores, disponibilidade e condições devem ser confirmados no atendimento.</p><a class="btn universo-gold" href="https://wa.me/5519974078273?text=Ol%C3%A1%21%20Vim%20pelo%20site%20e%20quero%20receber%20as%20condi%C3%A7%C3%B5es%20de%20pr%C3%A9-lan%C3%A7amento%20do%20Universo%20Riva%20Parque%20Alphaville." target="_blank" rel="noopener">Quero condições de pré-lançamento</a></div></section>'''
if old_invest not in html:
    raise SystemExit('invest block not found')
html = html.replace(old_invest, new_invest)

old_concept = '''<section class="universo-concept"><img src="assets/universo/conceito.webp" width="1054" height="1492" loading="lazy" alt="Identidade Universo Riva Parque Alphaville"><div><p class="eyebrow">UM NOVO CAPÍTULO</p><h2>Universo Riva.</h2><p>Uma nova proposta chegando ao Parque Alphaville.</p></div></section>'''
new_concept = '''<section class="universo-concept"><div class="universo-concept-copy"><p class="eyebrow">UM NOVO CAPÍTULO</p><h2>Universo Riva.</h2><p>Uma identidade criada para apresentar o primeiro projeto de apartamentos do Parque Alphaville.</p><div class="universo-concept-tags"><span>2 e 3 dormitórios</span><span>55 e 84 m²</span><span>Varanda</span><span>Lazer completo</span></div><a class="btn universo-gold" href="#contato">Quero receber plantas e condições</a></div><figure class="universo-concept-media"><img src="assets/universo/conceito.webp" width="1054" height="1492" loading="lazy" alt="Identidade Universo Riva Parque Alphaville"></figure></section>'''
if old_concept not in html:
    raise SystemExit('concept block not found')
html = html.replace(old_concept, new_concept)

# Add FAQ before contact form.
marker = '<section class="cta universo-cta" id="contato">'
faq = '''<section class="universo-faq"><div class="universo-faq-head"><p class="eyebrow">PERGUNTAS FREQUENTES</p><h2>O essencial antes de pedir as condições.</h2></div><div class="universo-faq-list"><details><summary>Quais metragens foram divulgadas?</summary><p>As informações públicas consultadas apresentam apartamentos de 55 m² e 84 m².</p></details><details><summary>Quantos dormitórios?</summary><p>Foram divulgadas opções de 2 e 3 dormitórios, com varanda e tipologia com suíte.</p></details><details><summary>Quantas vagas?</summary><p>A divulgação consultada indica 1 vaga para a planta de 55 m² e até 2 vagas para a configuração de 84 m². A unidade específica deve ser confirmada no atendimento.</p></details><details><summary>O condomínio terá lazer?</summary><p>Entre os itens apresentados estão piscina, espaço gourmet e ambientes de convivência.</p></details><details><summary>Quando será o lançamento?</summary><p>O anúncio público consultado indica previsão para outubro. Como se trata de pré-lançamento, a data pode ser alterada e deve ser confirmada com a corretora.</p></details></div></section>'''
if marker not in html:
    raise SystemExit('contact marker not found')
html = html.replace(marker, faq + marker, 1)

html_path.write_text(html, encoding='utf-8')

css = css_path.read_text(encoding='utf-8')
css += r'''

/* V5.35 — Universo Parque Alphaville: correção de cortes + conteúdo técnico */
.universo-specs{background:#0a1b2d;color:#fff;padding:105px 7vw;border-top:1px solid #d7a74c22;border-bottom:1px solid #d7a74c22}
.universo-specs-head{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:7vw;align-items:end;margin-bottom:42px}
.universo-specs-head h2{margin:8px 0 0;font-size:clamp(40px,4.6vw,68px);line-height:1.02;max-width:760px}
.universo-specs-head>p:last-child{color:#bec9d4;line-height:1.75;max-width:620px}
.universo-specs .eyebrow,.universo-faq .eyebrow{color:#d7a74c}
.universo-spec-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.universo-spec-grid article{padding:28px;border:1px solid #d7a74c45;background:#061524;min-height:210px}
.spec-size{display:inline-block;color:#d7a74c;font:500 29px 'Playfair Display',Georgia,serif;margin-bottom:18px}
.universo-spec-grid h3{font-size:22px;margin:0 0 11px}.universo-spec-grid p{color:#bec9d4;line-height:1.65;font-size:14px;margin:0}
.universo-location-points{display:grid;gap:9px;margin:28px 0 32px}.universo-location-points span{display:grid;grid-template-columns:145px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #d6d0c6;font-size:13px;line-height:1.45}.universo-location-points b{color:#8a5e23}

/* A imagem de investimento contém texto próprio: nunca recortar. */
.universo-invest{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(410px,.88fr);background:#04111e;color:#fff;align-items:stretch;overflow:visible}
.universo-invest-media{display:flex;align-items:center;justify-content:center;background:#061524;padding:0;min-width:0}
.universo-invest-media img{display:block;width:100%;height:auto;max-height:none;object-fit:contain!important;object-position:center!important}
.universo-invest-copy{padding:72px clamp(38px,5vw,86px);align-self:center;min-width:0}
.universo-invest-copy h2{font-size:clamp(38px,4.1vw,64px);line-height:1.02;margin:8px 0 24px;max-width:650px;overflow-wrap:anywhere}
.universo-invest-copy>p:not(.eyebrow){font-size:16px;line-height:1.72;color:#c8d1da;margin-bottom:20px}
.universo-invest-copy .universo-disclaimer{font-size:12px!important;color:#8996a3!important;border-left:2px solid #d7a74c;padding-left:14px;margin:24px 0 30px!important}

/* Conceito em duas colunas: preserva a arte vertical inteira, sem zoom ou corte. */
.universo-concept{display:grid;grid-template-columns:minmax(390px,.72fr) minmax(0,1.28fr);min-height:760px;background:#020b15;color:#fff;overflow:hidden}
.universo-concept-copy{padding:90px 7vw;align-self:center;position:relative;z-index:2;max-width:none!important;left:auto!important;bottom:auto!important}
.universo-concept-copy h2{font-size:clamp(52px,6vw,90px);line-height:.96;margin:10px 0 22px}.universo-concept-copy>p:not(.eyebrow){font-size:18px;line-height:1.7;color:#c8d1da;max-width:520px}
.universo-concept-tags{display:flex;flex-wrap:wrap;gap:8px;margin:28px 0 32px}.universo-concept-tags span{border:1px solid #d7a74c55;padding:9px 12px;font-size:12px;color:#e7d4ae}
.universo-concept-media{margin:0;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 45%,#0d3156 0,#041321 52%,#020b15 100%);min-width:0;padding:36px}
.universo-concept-media img{display:block;width:auto!important;height:auto!important;max-width:100%;max-height:900px;object-fit:contain!important;object-position:center!important}

.universo-faq{padding:105px 7vw;background:#f4efe7;color:#201f1c;display:grid;grid-template-columns:minmax(300px,.7fr) minmax(0,1.3fr);gap:8vw}
.universo-faq-head h2{font-size:clamp(40px,4.7vw,68px);line-height:1.02;max-width:580px}.universo-faq-list details{border-top:1px solid #cfc5b6;padding:20px 0}.universo-faq-list details:last-child{border-bottom:1px solid #cfc5b6}.universo-faq-list summary{cursor:pointer;font-weight:700;font-size:17px;list-style:none;position:relative;padding-right:34px}.universo-faq-list summary::-webkit-details-marker{display:none}.universo-faq-list summary:after{content:'+';position:absolute;right:4px;top:-3px;font-size:25px;color:#a26e25}.universo-faq-list details[open] summary:after{content:'–'}.universo-faq-list p{font-size:14px;line-height:1.7;color:#645f58;max-width:760px;margin:12px 0 0}

@media(max-width:1100px){.universo-invest{grid-template-columns:1fr}.universo-invest-media img{width:100%;height:auto}.universo-concept{grid-template-columns:.85fr 1.15fr}.universo-spec-grid{grid-template-columns:1fr 1fr}}
@media(max-width:900px){.universo-specs-head,.universo-faq,.universo-concept{grid-template-columns:1fr}.universo-concept-copy{padding:75px 6vw}.universo-concept-media{padding:28px;min-height:620px}.universo-concept-media img{max-height:760px}.universo-invest-copy{padding:65px 6vw}.universo-location-points span{grid-template-columns:125px 1fr}}
@media(max-width:560px){.universo-specs{padding:70px 22px}.universo-spec-grid{grid-template-columns:1fr}.universo-specs-head{gap:20px}.universo-invest-copy{padding:58px 22px}.universo-invest-copy h2{font-size:39px}.universo-concept-copy{padding:62px 22px}.universo-concept-media{min-height:500px;padding:18px}.universo-faq{padding:70px 22px;gap:35px}.universo-location-points span{grid-template-columns:1fr;gap:2px}.universo-location-points b{display:block}.universo-faq-list summary{font-size:16px}}
'''
css_path.write_text(css, encoding='utf-8')

# Update README with version note.
readme = root/'README-V5.30.txt'
if readme.exists():
    txt = readme.read_text(encoding='utf-8')
    txt += '\n\nV5.35 — Universo Parque Alphaville: correção de recortes nas seções Visão Geral e Conceito, inclusão de metragens/tipologias divulgadas, localização detalhada, ficha preliminar e FAQ. Conteúdo externo foi apenas factual e reescrito; nenhuma imagem externa foi incorporada.\n'
    readme.write_text(txt, encoding='utf-8')

print('updated')
