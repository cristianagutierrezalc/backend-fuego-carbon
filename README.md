# 🔥 Fuego & Carbón · API del Menú Digital

Backend en **FastAPI** para el menú digital del restaurante Fuego & Carbón. Este servicio es la **única fuente de verdad** del catálogo: los precios, las categorías y la disponibilidad viven aquí, y el frontend los consume vía REST.

## ✅ Estado

**Publicado** — en producción junto al menú digital.

## 🧱 Estructura

```
backend-fuego-carbon/
├── main.py            # API completa (app, rutas y catálogo)
└── requirements.txt   # Dependencias del proyecto
```

## 🚀 Ejecución local

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`

## 🧩 Relación con el frontend

El frontend del menú digital consume esta API con `fetch()`:

- **Frontend:** [cristianagutierrezalc/pagdemodev](https://github.com/cristianagutierrezalc/pagdemodev)
- **Prototipo inicial:** [cristianagutierrezalc/demopage](https://github.com/cristianagutierrezalc/demopage)

## 💡 Principio de diseño

Antes, el frontend mantenía su propia copia del catálogo y se desincronizaba con la realidad del restaurante. Ahora el backend es la única fuente de verdad: cualquier cambio de precio o de disponibilidad se refleja de inmediato en el menú, sin tocar el HTML.

## 🛠️ Stack

Python · FastAPI · Uvicorn
