# Instrucciones para Claude

Web estática (GitHub Pages desde `main`): `index.html` lee `data/*.json`. Estructura, campos y valores válidos en `README.md`.

## Rutina: clasificar posts de LinkedIn

Claude no tiene acceso a LinkedIn. Los posts llegan a `inbox/linkedin_inbox.json` mediante el userscript `scripts/linkedin-to-urban.user.js`, que la usuaria ejecuta en su navegador. La rutina solo procesa ese inbox.

1. Si ya hay un pull request abierto de una ejecución anterior de esta rutina (ramas `claude/…` que tocan `data/` o `inbox/descartados.json`), no hagas nada y termina: la siguiente ejecución continuará cuando se haya mergeado.
2. Trabaja sobre la última versión de `main` (`git fetch origin main`).
3. Ejecuta `python3 scripts/pending_inbox.py`. Si devuelve 0 pendientes, termina sin commits, ramas ni PRs.
4. Para cada post pendiente (usa `texto`, `enlaces` y, si hace falta, busca en la web la herramienta o el paper enlazado):
   - Herramienta, plugin, software o workflow → `data/tools.json`
   - Paper, libro, curso o contenido académico → `data/academic.json`
   - Relacionado con el sector pero no catalogable → `data/otros.json` (`autor`, `razon`, `url`, `fecha`)
   - Irrelevante para la web → `inbox/descartados.json` como `{"id": "<id>", "razon": "<motivo breve>"}`
5. Usa siempre la `url` del post del inbox para el campo de LinkedIn (`url` en tools/otros, `liUrl` en academic): así `pending_inbox.py` lo reconoce como procesado. Antes de añadir, comprueba que la herramienta o el paper no estén ya en `data/` con otro post; si lo están, envía el post a `descartados.json` con la razón «duplicado de …».
6. Usa solo los valores válidos de `README.md` (`categoria`, `acceso`, `tipo`, `ia`, `linkType`). `fecha` = fecha de hoy (AAAA-MM-DD).
7. Valida que los JSON cargan (`python3 -c "import json; json.load(open(...))"`), vuelve a ejecutar `pending_inbox.py` (debe dar 0 pendientes), haz commit y abre un único pull request contra `main` con la lista de lo añadido y lo descartado.

No modifiques `inbox/linkedin_inbox.json`: lo escribe el userscript.
