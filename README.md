# Repositorio — Herramientas de Análisis y Diseño Urbano

Catálogo curado de software, plugins, frameworks y workflows geoespaciales para análisis y diseño urbano.

## Estructura

```
├── index.html              ← Código base (interfaz completa, SPA)
├── data/
│   ├── tools.json          ← Herramientas (tabla principal)
│   ├── academic.json       ← Contenido académico adicional
│   ├── companies.json      ← Empresas del sector
│   ├── recursos.json       ← Listas de recursos (plug-ins, datasets, etc.)
│   └── otros.json          ← Posts descartados
├── csv/                    ← Fuentes originales sin procesar
│   ├── Company Follows.csv
│   ├── linkedin_saved_posts.csv
│   └── linkedin-saved-posts-2026-03-22 (2).csv
├── recursos/               ← Imágenes locales para listas de recursos
├── inbox/
│   ├── linkedin_inbox.json ← Posts enviados desde LinkedIn (pendientes de clasificar)
│   └── descartados.json    ← Posts del inbox revisados y no incluidos en la web
├── scripts/
│   ├── linkedin-to-urban.user.js ← Userscript de Tampermonkey
│   └── pending_inbox.py    ← Lista los posts del inbox aún no catalogados
├── CLAUDE.md               ← Instrucciones para la rutina que clasifica el inbox
└── README.md
```

## Enviar posts de LinkedIn al repositorio

Claude no puede entrar en LinkedIn (requiere tu sesión y su API no da acceso a los posts guardados), así que el flujo tiene dos pasos:

1. **Captura (tú, un clic):** un userscript recoge los posts desde tu propio navegador y los guarda en `inbox/linkedin_inbox.json` (rama `main`).
2. **Clasificación (rutina de Claude):** la rutina diaria lee los posts pendientes, los clasifica en herramientas, académico u otros y abre un único pull request para que lo revises. Las instrucciones que sigue están en `CLAUDE.md`.

**Instalación (una sola vez):**

1. Instala la extensión [Tampermonkey](https://www.tampermonkey.net/) en tu navegador.
2. Abre `scripts/linkedin-to-urban.user.js` en GitHub, pulsa **Raw** y Tampermonkey ofrecerá instalarlo.
3. Crea un token en GitHub → Settings → Developer settings → **Fine-grained tokens**: acceso solo al repositorio `urban`, permiso **Contents: Read and write**.
4. La primera vez que pulses el botón, el script te pedirá el token (se guarda en Tampermonkey; para cambiarlo usa el menú de Tampermonkey → *Cambiar token de GitHub*).

**Uso:** abre https://www.linkedin.com/my-items/saved-posts/ (o el feed) y pulsa el botón azul **Enviar a urban** abajo a la derecha. El script carga toda la lista, extrae autor, URL, enlaces y los primeros 500 caracteres del texto de cada post (el repositorio es público) y añade solo los nuevos al inbox. Si el botón indica «0 posts vistos», LinkedIn ha cambiado su HTML y hay que actualizar los selectores del script.

**Procesado:** `python3 scripts/pending_inbox.py` imprime los posts del inbox cuyo ID aún no aparece en `data/*.json` ni en `inbox/descartados.json`. Cada post revisado se añade a `tools.json`, `academic.json` u `otros.json` (con su URL de LinkedIn) o, si no es relevante, a `inbox/descartados.json` como `{"id": "...", "razon": "..."}`, así que deja de aparecer como pendiente.

## Configuración en GitHub Pages

1. Crea un repositorio en GitHub (público)
2. Sube todos los archivos manteniendo la estructura de carpetas
3. Ve a **Settings → Pages**
4. En "Source" selecciona **Deploy from a branch**
5. Selecciona la rama `main` y carpeta `/ (root)`
6. Guarda. En unos minutos tendrás la web en `https://tu-usuario.github.io/nombre-repo/`

## Cómo añadir herramientas

Edita `data/tools.json` directamente en GitHub (botón de lápiz) y añade un nuevo objeto al array:

```json
{
  "nombre": "Nombre de la herramienta",
  "categoria": "Análisis",
  "subcategorias": ["Subcategoría 1", "Subcategoría 2"],
  "acceso": "Libre acceso",
  "tipo": "Herramienta nueva",
  "ia": "No",
  "descripcion": "Descripción breve.",
  "autor": "Nombre del autor",
  "url": "https://linkedin.com/...",
  "programas": ["Python", "QGIS"],
  "link": "https://ejemplo.com",
  "linkType": "website",
  "imagen": "https://url-de-imagen.jpg",
  "enlaces": [{"label": "GitHub", "url": "https://github.com/..."}],
  "fecha": "2026-03-20"
}
```

### Valores válidos

| Campo | Opciones |
|-------|----------|
| `categoria` | `Análisis`, `Generación`, `Ambas` |
| `acceso` | `Libre acceso`, `Empresa de pago`, `Mixto`, `En desarrollo` |
| `tipo` | `Herramienta nueva`, `Empresa establecida`, `Complemento`, `Workflow`, `Framework académico`, `Educativo`, `Conceptual`, `Educativo/Workflow` |
| `ia` | `Sí`, `No` |
| `linkType` | `website`, `github`, `demo`, `paper`, `docs` |

### Añadir contenido académico

Edita `data/academic.json` con la misma lógica.

### Añadir empresas

Edita `data/companies.json`. Si una empresa también aparece como herramienta en `tools.json`, se enlazan automáticamente entre las dos pestañas.

### Añadir listas de recursos

Edita `data/recursos.json`. Cada lista tiene `titulo`, `descripcion`, opcional `sourceUrl`/`sourceLabel`, y un array `items` con objetos `{nombre, descripcion, imagen?, link?, enlaces?}`.

### Añadir posts descartados

Edita `data/otros.json`:

```json
{
  "autor": "Nombre",
  "razon": "Motivo del descarte",
  "url": "https://linkedin.com/..."
}
```

## Pestañas de la interfaz

- **Herramientas** → Tabla, Gráficos y Mapa de relaciones sobre `tools.json`.
- **Académico** → Frameworks académicos (de `tools.json`) + papers extra (`academic.json`).
- **Empresas** → Directorio clasificado a partir de `companies.json`.
- **Recursos** → Listas temáticas desde `recursos.json` (plug-ins, datasets, librerías…).
- **Otros** → Posts no catalogados (`otros.json`).

La barra superior incluye un buscador global que indexa las cinco secciones.

## Fuentes originales (CSV)

La carpeta `csv/` guarda los exports en crudo desde LinkedIn que sirvieron de origen para poblar `data/*.json`. No los consume la web directamente; se conservan como trazabilidad de las fuentes.

## Desarrollo local

Para probar en local necesitas un servidor HTTP (los `fetch()` no funcionan con `file://`):

```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .
```

Luego abre `http://localhost:8000`
