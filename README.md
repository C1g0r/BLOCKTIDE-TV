# BLOCKTIDE TV (web app)

Web app para crianças com **só vídeos em português europeu**, de um catálogo de canais de produção
portuguesa verificados. Os vídeos tocam no leitor oficial do YouTube (incorporado, `youtube-nocookie.com`,
sem sugestões externas no fim). Interface própria BLOCKTIDE — não imita o YouTube.

- Início por temas, «Continuar a ver», páginas de canal, pesquisa só no catálogo
- **Shorts:** vídeos curtos para deslizar na vertical (um só leitor que muda de vídeo, começa sem som, passa sozinho ao seguinte; tocar pausa). Só conteúdo infantil e **nunca português do Brasil**; os pais podem desligar os Shorts ou limitar a PT-PT e sem diálogo
- Fim do vídeo: ecrã «A seguir» com outro vídeo parecido (contagem de 6 s)
- Área dos pais com PIN: resumo do tempo, limite diário, hora de dormir, canais, vídeos acrescentados
- Instalável no ecrã principal (iPhone: Partilhar → «Adicionar ao ecrã principal»; Android: «Instalar app»)
  e abre sem rede (sem vídeos)
- Tudo fica no aparelho (localStorage); não há contas nem servidor

Ficheiros estáticos: publicar este repositório em qualquer alojamento com HTTPS (GitHub Pages, Netlify…).
Teste (Python + Playwright): `python3 tests/tv_e2e.py`.

© 2026 Igor Serrano. Todos os direitos reservados — ver `LICENSE`. Tipos de letra Nunito e Lilita One sob a licença SIL OFL (`fonts/`).

## Catálogo — atualização de 21 de novembro de 2026

- **65 vídeos normais:** 49 de canais portugueses ativos e 16 de canais pendentes que os pais podem ativar.
- **156 Shorts:** 78 assinalados PT-PT (30 visíveis por defeito, 48 pendentes) e 78 internacionais, em idiomas diferentes ou sem diálogo.
- **Novos nesta atualização:** 19 vídeos sem duplicados: 7 do canal oficial Panda e os Caricas (ativos), 7 do Aprender com a MEGA e 5 do Cartoonito Portugal (estes últimos dois continuam desligados por defeito). Mais 11 referências encontradas que já existiam como Shorts e não foram repetidas.
- **Proveniência:** `docs/curadoria-2026-11-21.csv` contém os IDs, ligações diretas, grau de evidência e estado da auditoria de áudio dos vídeos novos. Fontes: o YouTube oficial de Panda e os Caricas e o diretório Português Portugal para Aprender com a MEGA e Cartoonito Portugal.
- **Política de exclusão:** não adicionar conteúdos de origem brasileira nem vídeos em português do Brasil. O código rejeita qualquer entrada assinalada com `originCountry`/`market`/`country` = `BR` ou `lang` = `pt-BR`, mesmo que o canal esteja ativado.
- **Limite importante:** o filtro lê metadados; não analisa áudio nem identifica automaticamente sotaques ou o país de produção. Canais pendentes não aparecem por defeito. Os pais devem confirmar o áudio e a origem antes de os ativar. Vídeos acrescentados manualmente pelos pais são da sua responsabilidade.

A lista anterior de canais candidatos (sem ID confirmado) continua separada em `docs/pesquisa-2026-11-17/`, sem entradas fictícias. Durações que não foram confirmadas ficam vazias, em vez de serem inventadas.

**Validação rápida do catálogo:** `python3 tests/catalog_policy.py`. Teste funcional: `python3 tests/tv_e2e.py`.

## Qualidade e auditoria

As verificações automáticas do catálogo correm no GitHub Actions a cada alteração relevante. Consultar [critérios editoriais](docs/CRITERIOS-EDITORIAIS.md). A validação estrutural não substitui a audição e revisão humanas dos vídeos.

### Curadoria adicional (21/11/2026)

Foi incluído um vídeo oficial de Panda e os Caricas, **Os Caricas (Ao Vivo no Campo Pequeno, Lisboa, 2018)**. A página oficial do YouTube identifica a editora Universal Music Portugal, a apresentação em Lisboa e apresenta a letra em português. A reprodução integral e a incorporação continuam por verificar. O catálogo contém agora 66 vídeos normais e 156 Shorts.

## Diagnóstico de atualizações (v0.5.3)

A área dos pais mostra a versão do código, a versão do catálogo, o total de vídeos e quantos estão disponíveis com os filtros atuais. Os canais pendentes ficam desligados por defeito; por isso, o total do catálogo não corresponde necessariamente ao número de vídeos visíveis.

A aplicação verifica a atualização do service worker a cada abertura e recarrega quando uma nova versão toma posse. Para consultar os dados técnicos no navegador: `window.BTV.diagnostics`. O carregamento de `catalog.json` utiliza `cache: 'no-store'` quando existe ligação. Em instalações antigas pode ser necessária uma atualização manual inicial para obter o novo código.
