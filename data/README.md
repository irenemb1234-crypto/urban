# Data

Five JSON datasets that power `index.html`. All files are arrays of objects. Dates are `YYYY-MM-DD`.

## `tools.json` — tools & platforms (90)

| Field | Type | Notes |
|---|---|---|
| `nombre` | string | tool name |
| `categoria` | string | `Análisis` \| `Generación` \| `Ambas` |
| `subcategorias` | string[] | |
| `acceso` | string | `Libre acceso` \| `Empresa de pago` \| `Mixto` \| `En desarrollo` |
| `tipo` | string | e.g. `Empresa establecida`, `Framework académico` |
| `ia` | string | `Sí` \| `No` |
| `descripcion` | string | |
| `autor` | string | person or org |
| `url` | string | primary URL (often a LinkedIn post) |
| `link` | string | canonical site (distinct from `url`) |
| `linkType` | string | `website` \| `github` \| `demo` |
| `programas` | string[] | host programs (Rhino3D, QGIS…) |
| `enlaces` | {label,url}[] | extra links |
| `imagen` | string | |
| `fecha` | string | date added |
| `empresa` | string? | optional — company `nombre` in `companies.json` when the tool is also a listed organisation |

## `companies.json` — organisations (294)

| Field | Type | Notes |
|---|---|---|
| `nombre` | string | |
| `tipo` | string | e.g. `Empresa privada`, `Universidad`, `Laboratorio` |
| `sector` | string | |
| `descripcion` | string | |
| `url` | string | LinkedIn company page |
| `fecha` | string | |
| `herramientas` | string[]? | optional — tool `nombre`s in `tools.json` owned by this org |

## `academic.json` — articles & curated lists (12)

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `desc` | string | |
| `autor` | string | |
| `cat` | string? | |
| `badges` | string? | inline HTML badges |
| `body` | string? | expandable HTML body |
| `paperUrl` | string? | |
| `linkUrl` | string? | |
| `liUrl` | string? | LinkedIn post |
| `fecha` | string | |

Note: academic items with `tipo: "Framework académico"` from `tools.json` are merged in at runtime by `index.html`.

## `recursos.json` — curated collections (3)

Each collection:

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `titulo` | string | |
| `descripcion` | string | |
| `sourceUrl` / `sourceLabel` | string | origin of the list |
| `autor` | string | curator |
| `fecha` | string | |
| `items` | object[] | see below |

Each item: `nombre`, `descripcion`, `link`, `linkType`, `enlaces?`, `imagen?`.

## `otros.json` — LinkedIn post references (45)

| Field | Type | Notes |
|---|---|---|
| `autor` | string | |
| `razon` | string | why it was kept |
| `url` | string | LinkedIn post |
| `fecha` | string | |

## Cross-dataset relationships

- **Tool ↔ company.** `companies[].herramientas` and `tools[].empresa` form a two-way link between the 11 companies that ship tools and the 20 tools they own.
- **Shared authors.** `autor` is the main join key across `tools`, `academic`, `otros`, and `recursos` (collection-level). Ten authors appear in multiple datasets; Milan Janosov and Abhinav Bhardwaj are the most cross-cutting.
