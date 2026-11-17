# BLOCKTIDE TV (web app)

Web app para crianças com **só vídeos em português europeu**, de um catálogo de canais de produção
portuguesa verificados. Os vídeos tocam no leitor oficial do YouTube (incorporado, `youtube-nocookie.com`,
sem sugestões externas no fim). Interface própria BLOCKTIDE — não imita o YouTube.

- Início por temas, «Continuar a ver», páginas de canal, pesquisa só no catálogo
- Fim do vídeo: ecrã «A seguir» com outro vídeo parecido (contagem de 6 s)
- Área dos pais com PIN: resumo do tempo, limite diário, hora de dormir, canais, vídeos acrescentados
- Instalável no ecrã principal (iPhone: Partilhar → «Adicionar ao ecrã principal»; Android: «Instalar app»)
  e abre sem rede (sem vídeos)
- Tudo fica no aparelho (localStorage); não há contas nem servidor

Ficheiros estáticos: publicar este repositório em qualquer alojamento com HTTPS (GitHub Pages, Netlify…).
Teste (Python + Playwright): `python3 tests/tv_e2e.py`.

© 2026 Igor Serrano. Todos os direitos reservados — ver `LICENSE`. Tipos de letra Nunito e Lilita One sob a licença SIL OFL (`fonts/`).

**Limites desta versão:** catálogo fixo (`catalog.json`, 42 vídeos de 6 canais); a seguir, um pequeno
servidor com a API do YouTube para o manter atualizado. O leitor incorporado não permite escolher a
faixa de áudio: o catálogo só deve ter vídeos sem dobragens.
