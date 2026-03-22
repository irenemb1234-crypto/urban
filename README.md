# Repositorio — Herramientas de Análisis y Diseño Urbano

Catálogo curado de software, plugins, frameworks y workflows geoespaciales para análisis y diseño urbano.

## Estructura

```
├── index.html          ← Código base (interfaz completa)
├── data/
│   ├── tools.json      ← Herramientas (tabla principal)
│   ├── academic.json   ← Contenido académico adicional
│   └── otros.json      ← Posts descartados
└── README.md
```

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

### Añadir posts descartados

Edita `data/otros.json`:

```json
{
  "autor": "Nombre",
  "razon": "Motivo del descarte",
  "url": "https://linkedin.com/..."
}
```

## Desarrollo local

Para probar en local necesitas un servidor HTTP (los `fetch()` no funcionan con `file://`):

```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .
```

Luego abre `http://localhost:8000`
