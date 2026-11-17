# BLOCKTIDE TV (web app)

Web app para crianças com **só vídeos em português europeu**, de um catálogo de canais de produção
portuguesa verificados. Os vídeos tocam no leitor oficial do YouTube (incorporado, `youtube-nocookie.com`,
sem sugestões externas no fim). Interface própria BLOCKTIDE — não imita o YouTube.

- Início por temas, «Continuar a ver», páginas de canal, pesquisa só no catálogo
- **Shorts:** vídeos curtos para deslizar na vertical (um leitor de cada vez, começa sem som, passa sozinho ao seguinte). Só conteúdo infantil e **nunca português do Brasil**; os pais podem desligar os Shorts ou limitar a PT-PT e sem diálogo
- Fim do vídeo: ecrã «A seguir» com outro vídeo parecido (contagem de 6 s)
- Área dos pais com PIN: resumo do tempo, limite diário, hora de dormir, canais, vídeos acrescentados
- Instalável no ecrã principal (iPhone: Partilhar → «Adicionar ao ecrã principal»; Android: «Instalar app»)
  e abre sem rede (sem vídeos)
- Tudo fica no aparelho (localStorage); não há contas nem servidor

Ficheiros estáticos: publicar este repositório em qualquer alojamento com HTTPS (GitHub Pages, Netlify…).
Teste (Python + Playwright): `python3 tests/tv_e2e.py`.

© 2026 Igor Serrano. Todos os direitos reservados — ver `LICENSE`. Tipos de letra Nunito e Lilita One sob a licença SIL OFL (`fonts/`).

## Catálogo

- **Shorts** (`catalog.json` → `shorts`): 78 Shorts verdadeiros (verticais, até 3 min, incorporação confirmada): 30 dos canais verificados (RTP zigzag, Canal Panda, Panda e os Caricas) e 48 dos canais por confirmar, que só aparecem quando os pais os ligam. `pt-BR` nunca entra.

- **Verificados** (ligados): RTP zigzag, Panda e os Caricas, Xana Toc Toc, Avô Cantigas, Sónia e as Profissões, Canal Panda — 42 vídeos.
- **Por confirmar** (desligados até os pais os ligarem): Cartoonito Portugal, Disney Junior PT, Moonbug Portugal,
  Aprender com a MEGA, Histórias do Guilherme — identidade confirmada, áudio por auditar; 4 vídeos até agora.
- `docs/pesquisa-2026-11-17/`: a pesquisa original, incluindo 18 canais candidatos ainda sem ID confirmado
  (vários são brasileiros e não devem entrar). Ficou de fora «Portuguese at Ease» (aulas para adultos).

**Limites desta versão:** catálogo fixo (`catalog.json`, 42 vídeos de 6 canais); a seguir, um pequeno
servidor com a API do YouTube para o manter atualizado. O leitor incorporado não permite escolher a
faixa de áudio: o catálogo só deve ter vídeos sem dobragens.
