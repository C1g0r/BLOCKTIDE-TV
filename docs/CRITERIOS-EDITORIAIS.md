# Critérios editoriais — BLOCKTIDE TV

## Regra principal
Não incluir vídeos produzidos no Brasil nem conteúdos falados em português do Brasil.
Um canal internacional pode ser aceite, desde que não seja de origem brasileira e o conteúdo seja infantil.

## Estados de curadoria
- `verificado`: canal aprovado editorialmente; os seus vídeos aparecem por defeito. **O estado do canal não garante que cada vídeo tenha o áudio auditado**.
- `pendente`: canal identificado, mas sem validação editorial suficiente; desligado por defeito. Os pais podem ativá-lo conscientemente.
- `internacional`: canal infantil não brasileiro, atualmente usado apenas nos Shorts; idiomas estrangeiros podem ser ocultados no painel parental.

## Antes de adicionar um vídeo
1. Confirmar o URL e o ID real do vídeo no YouTube, e se permite incorporação.
2. Confirmar que a origem da produção não é brasileira; não basta a localização ou o nome do canal.
3. Ouvir o vídeo completo ou amostra representativa e registar o idioma real.
4. Confirmar que é adequado a crianças e que não tem publicidade integrada imprópria.
5. Verificar duplicados em `videos` **e** `shorts`.
6. Guardar fonte, data de verificação e estado da auditoria no registo de curadoria.
7. Só promover o canal a `verificado` após revisão suficiente.

## Campos de segurança
- `country`, `originCountry`, `market`: valores `BR`, `BRA`, `Brasil`, `Brazil` são rejeitados.
- `lang`: `pt-BR` é rejeitado.
- `blocked: true`: rejeitado.
- Os metadados não constituem prova de origem ou idioma. Um vídeo sem esses campos **não fica automaticamente aprovado**.
- Vídeos adicionados manualmente pelos pais não podem ser auditados pela aplicação.

## Automatização
O GitHub Actions executa `python3 tests/catalog_policy.py`, `node --check app.js` e verifica a sintaxe JSON.
Estes testes detetam problemas estruturais e metadados proibidos; **não verificam o áudio, a proveniência real, a disponibilidade no YouTube ou a adequação editorial**.
