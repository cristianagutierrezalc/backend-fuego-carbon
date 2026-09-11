"""
API Menú Digital Gastronómico — Fuego & Carbón
================================================
Backend construido con FastAPI. Expone el catálogo completo de productos
del restaurante y sirve como ÚNICA fuente de verdad para el frontend
(antes, el frontend tenía su propio catálogo duplicado y desincronizado).

Principios aplicados (Clean Code):
- Contratos de datos explícitos con Pydantic (validación automática).
- Separación de responsabilidades: modelos / datos / acceso a datos / rutas.
- Manejo de errores robusto y respuestas HTTP semánticamente correctas.
- Sin duplicación de datos: "Más Vendidas" es un flag (`featured`), no una
  categoría duplicada con copias de productos ya existentes.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging — visibilidad profesional de lo que hace la API en producción.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("fuego_y_carbon.api")


# ---------------------------------------------------------------------------
# Modelos de datos (Pydantic)
# Definir un contrato explícito evita bugs de "campo mal escrito" y permite
# que FastAPI genere documentación interactiva (/docs) automáticamente.
# ---------------------------------------------------------------------------
class Category(str, Enum):
    """Categorías reales del menú (sin duplicados ni emojis en el dato crudo;
    la presentación visual —emoji, orden, etc.— es responsabilidad del
    frontend, no del backend)."""

    COMBOS = "Combos"
    HAMBURGUESAS = "Hamburguesas"
    SALCHIPAPAS = "Salchipapas"
    PERROS_CALIENTES = "Perros Calientes"
    PICADAS = "Picadas"
    PATACONES_RELLENOS = "Patacones Rellenos"
    PIZZAS = "Pizzas"
    ACOMPANAMIENTOS = "Acompañamientos"
    BEBIDAS = "Bebidas"


class Product(BaseModel):
    """Representa un producto del menú."""

    id: str
    category: Category
    name: str
    desc: str
    price: int = Field(..., gt=0, description="Precio en pesos colombianos (COP)")
    image: str
    featured: bool = Field(
        default=False,
        description="True si el producto debe aparecer en 'Más Vendidas'.",
    )
    available: bool = Field(
        default=True,
        description="Permite ocultar/agotar un producto sin borrarlo del catálogo.",
    )


class CategorySummary(BaseModel):
    """Resumen de una categoría, útil para construir la barra de filtros
    en el frontend sin tener que descargar todo el catálogo primero."""

    name: str
    total_products: int


class HealthStatus(BaseModel):
    status: str
    total_products: int


# ---------------------------------------------------------------------------
# Datos del catálogo
# Fuente única de verdad: antes vivía duplicado (y desactualizado) también
# en el frontend. Ahora el frontend siempre lo consulta aquí.
# ---------------------------------------------------------------------------
PRODUCTS_DB: list[Product] = [
    # --- Combos ---------------------------------------------------------
    Product(id="combo-01", category=Category.COMBOS, name="Combo Dúo Fuego",
            desc="2 Hamburguesas Clásicas + Papas francesas grandes + 2 Coca Colas de 400ml.",
            price=49900, image="https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=500"),
    Product(id="combo-02", category=Category.COMBOS, name="Combo Familiar Parrillero",
            desc="1 Picada personal + 1 Salchipapa Salvaje + 1 Pizza Personal + 1 Gaseosa 1.5L.",
            price=89900, image="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=500"),
    Product(id="combo-03", category=Category.COMBOS, name="Combo Personal Todo Terreno",
            desc="1 Hamburguesa BBQ Crispy + Papas rústicas + Limonada natural de la casa.",
            price=31900, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"),

    # --- Hamburguesas -----------------------------------------------------
    Product(id="hamb-01", category=Category.HAMBURGUESAS, name="Hamburguesa Clásica Fuego",
            desc="Carne de res 150g, queso cheddar, lechuga, tomate y salsa especial.",
            price=24900, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500",
            featured=True),
    Product(id="hamb-02", category=Category.HAMBURGUESAS, name="Hamburguesa Doble Queso & Tocino",
            desc="Doble carne 300g, doble queso, tocino crujiente y cebolla caramelizada.",
            price=32900, image="https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=500"),
    Product(id="hamb-03", category=Category.HAMBURGUESAS, name="Hamburguesa BBQ Crispy",
            desc="Carne 150g, aros de cebolla crocantes, salsa BBQ ahumada y queso gouda.",
            price=28900, image="https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=500"),
    Product(id="hamb-04", category=Category.HAMBURGUESAS, name="Hamburguesa Mex-Jalapeño",
            desc="Carne de res, queso pepper jack, jalapeños, guacamole y totopos picados.",
            price=27900, image="https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500"),
    Product(id="hamb-05", category=Category.HAMBURGUESAS, name="Hamburguesa Mushroom Swiss",
            desc="Carne de res 150g, champiñones salteados en mantequilla y queso suizo.",
            price=29900, image="https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=500"),
    Product(id="hamb-06", category=Category.HAMBURGUESAS, name="Hamburguesa Chicken Crispy",
            desc="Pechuga de pollo apanada, ensalada coleslaw, pepinillos y mayonesa de ajo.",
            price=25900, image="https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500"),
    Product(id="hamb-07", category=Category.HAMBURGUESAS, name="Hamburguesa Veggie Black Bean",
            desc="Medallón de fríjoles negros y avena, aguacate, rúcula y tomate seco.",
            price=26900, image="https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"),
    Product(id="hamb-08", category=Category.HAMBURGUESAS, name="Hamburguesa Triple Beast",
            desc="Triple carne 450g, triple queso cheddar, tocino ahumado y salsa secreta.",
            price=39900, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"),
    Product(id="hamb-09", category=Category.HAMBURGUESAS, name="Hamburguesa Blue Cheese",
            desc="Carne de res, queso azul fundido y cebolla caramelizada al vino tinto.",
            price=31900, image="https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=500"),
    Product(id="hamb-10", category=Category.HAMBURGUESAS, name="Hamburguesa Pulled Pork BBQ",
            desc="Cerdo desmechado en cocción lenta, salsa BBQ casera y cebolla morada.",
            price=28900, image="https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=500"),

    # --- Salchipapas --------------------------------------------------
    Product(id="salc-01", category=Category.SALCHIPAPAS, name="Salchipapa Tradicional",
            desc="Cama de papas francesas, salchicha premium, queso costeño rallado y salsas.",
            price=18900, image="https://images.unsplash.com/photo-1585109649139-366815a0d713?w=500"),
    Product(id="salc-02", category=Category.SALCHIPAPAS, name="Salchipapa Salvaje (2 Pers)",
            desc="Papas francesas, salchicha manguera, carne desmechada, queso costeño y maicitos.",
            price=34900, image="https://images.unsplash.com/photo-1585109649139-366815a0d713?w=500",
            featured=True),
    Product(id="salc-03", category=Category.SALCHIPAPAS, name="Salchipapa Costeña Especial",
            desc="Papas rústicas, salchicha, pollo desmechado, tocineta, queso gratinado y suero.",
            price=29900, image="https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"),

    # --- Perros Calientes -----------------------------------------------
    Product(id="perr-01", category=Category.PERROS_CALIENTES, name="Perro Americano Clásico",
            desc="Salchicha americana, pepinillos, cebolla picada, mostaza dulce y ketchup.",
            price=16900, image="https://images.unsplash.com/photo-1619740455993-9e612b1af08a?w=500"),
    Product(id="perr-02", category=Category.PERROS_CALIENTES, name="Perro Mexicano Picante",
            desc="Salchicha premium, chili con carne, jalapeños, queso cheddar y guacamole.",
            price=19900, image="https://images.unsplash.com/photo-1627308595229-7830a5c91f9f?w=500"),
    Product(id="perr-03", category=Category.PERROS_CALIENTES, name="Perro Especial con Tocineta",
            desc="Salchicha envuelta en tocineta, queso mozzarella fundido, papa ripia y salsa verde.",
            price=21900, image="https://images.unsplash.com/photo-1619740455993-9e612b1af08a?w=500"),

    # --- Picadas ----------------------------------------------------------
    Product(id="pica-01", category=Category.PICADAS, name="Picada Personal Fuego & Carbón",
            desc="Lomo de res, pechuga de pollo, chorizo, chicharrón, papas criollas y arepitas.",
            price=32900, image="https://images.unsplash.com/photo-1544025162-d76694265947?w=500"),
    Product(id="pica-02", category=Category.PICADAS, name="Picada Familiar (3-4 Personas)",
            desc="Selección de carnes al carbón, costillitas BBQ, yuca frita, patacón y guasacaca.",
            price=79900, image="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=500"),

    # --- Patacones Rellenos ------------------------------------------
    Product(id="pata-01", category=Category.PATACONES_RELLENOS, name="Patacón Trifásico",
            desc="Patacón gigante con carne desmechada, pollo, chicharrón, queso costeño y suero.",
            price=28900, image="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            featured=True),
    Product(id="pata-02", category=Category.PATACONES_RELLENOS, name="Patacón Ranchero",
            desc="Patacón tostado con pollo desmechado, maíz tierno, tocineta crujiente y queso fundido.",
            price=26900, image="https://images.unsplash.com/photo-1544025162-d76694265947?w=500"),

    # --- Pizzas -------------------------------------------------------
    Product(id="pizz-01", category=Category.PIZZAS, name="Pizza Pepperoni Fuego (Personal)",
            desc="Salsa de tomate casera, queso mozzarella abundante y dobles rodajas de pepperoni.",
            price=22900, image="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500"),
    Product(id="pizz-02", category=Category.PIZZAS, name="Pizza Hawaiana Especial (Personal)",
            desc="Masa artesanal, jamón seleccionado, piña calada en almíbar y queso mozzarella.",
            price=21900, image="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500"),
    Product(id="pizz-03", category=Category.PIZZAS, name="Pizza Carnívora (Personal)",
            desc="Cargada con carne molida artesanal, tocineta, chorizo santarrosano y jamón.",
            price=25900, image="https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=500"),

    # --- Acompañamientos --------------------------------------------
    Product(id="acom-01", category=Category.ACOMPANAMIENTOS, name="Papas Rústicas Suprema",
            desc="Papas rústicas con queso cheddar fundido y trozos de tocino.",
            price=14900, image="https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"),
    Product(id="acom-02", category=Category.ACOMPANAMIENTOS, name="Papas Francesas Clásicas",
            desc="Papas fritas en corte tradicional, doradas y crujientes con sal marina.",
            price=9900, image="https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=500"),
    Product(id="acom-03", category=Category.ACOMPANAMIENTOS, name="Aros de Cebolla Crocantes",
            desc="Aros de cebolla apanados acompañados de salsa BBQ de la casa.",
            price=12900, image="https://images.unsplash.com/photo-1639024471283-03518883512d?w=500"),
    Product(id="acom-04", category=Category.ACOMPANAMIENTOS, name="Nuggets de Pollo X8",
            desc="Trozos de pechuga apanados acompañados de salsa miel mostaza.",
            price=13900, image="https://images.unsplash.com/photo-1562967914-608f82629710?w=500"),
    Product(id="acom-05", category=Category.ACOMPANAMIENTOS, name="Dedos de Queso Mozzarella",
            desc="6 bastones de mozzarella empanizados con salsa marinara casera.",
            price=15900, image="https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=500"),
    Product(id="acom-06", category=Category.ACOMPANAMIENTOS, name="Papas Trufadas con Parmesano",
            desc="Papas delgadas bañadas en aceite de trufa y queso parmesano rallado.",
            price=17900, image="https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"),
    Product(id="acom-07", category=Category.ACOMPANAMIENTOS, name="Nachos con Queso y Guacamole",
            desc="Totopos de maíz crujientes con queso cheddar fundido y guacamole fresco.",
            price=16900, image="https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=500"),
    Product(id="acom-08", category=Category.ACOMPANAMIENTOS, name="Alitas BBQ X6",
            desc="Alitas de pollo bañadas en salsa BBQ dulce ahumada.",
            price=19900, image="https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=500"),
    Product(id="acom-09", category=Category.ACOMPANAMIENTOS, name="Alitas Spicy Buffalo X6",
            desc="Alitas de pollo picantes estilo Buffalo con aderezo blue cheese.",
            price=19900, image="https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=500"),
    Product(id="acom-10", category=Category.ACOMPANAMIENTOS, name="Mazorca Dulce a la Parrilla",
            desc="Mazorca desgranada con mantequilla, queso costeño y papitas fosforito.",
            price=8900, image="https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=500"),

    # --- Bebidas ------------------------------------------------------
    Product(id="beb-01", category=Category.BEBIDAS, name="Coca Cola Personal 400ml",
            desc="Refresco helado en botella plástica.",
            price=5500, image="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=500"),
    Product(id="beb-02", category=Category.BEBIDAS, name="Coca Cola Zero 400ml",
            desc="Sabor original sin azúcar.",
            price=5500, image="https://images.unsplash.com/photo-1554866585-cd94860890b7?w=500"),
    Product(id="beb-03", category=Category.BEBIDAS, name="Limonada Natural",
            desc="Zumo de limón recién exprimido con un toque de menta.",
            price=7900, image="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"),
    Product(id="beb-04", category=Category.BEBIDAS, name="Limonada Cerezada",
            desc="Limonada natural frapeada con almíbar de cereza.",
            price=8900, image="https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=500"),
    Product(id="beb-05", category=Category.BEBIDAS, name="Limonada de Coco",
            desc="Mezcla cremosa de leche de coco y limón natural.",
            price=9900, image="https://images.unsplash.com/photo-1546171753-97d7676e4602?w=500"),
    Product(id="beb-06", category=Category.BEBIDAS, name="Malteada de Chocolate",
            desc="Helado artesanal de chocolate con crema batida y chispas.",
            price=12900, image="https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=500"),
    Product(id="beb-07", category=Category.BEBIDAS, name="Malteada de Vainilla & Oreo",
            desc="Helado de vainilla batido con trozos de galleta Oreo.",
            price=13900, image="https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=500"),
    Product(id="beb-08", category=Category.BEBIDAS, name="Cerveza Artesanal IPA",
            desc="Cerveza local amarga con notas cítricas, 330ml.",
            price=11900, image="https://images.unsplash.com/photo-1608270586620-248524c67de9?w=500"),
    Product(id="beb-09", category=Category.BEBIDAS, name="Cerveza Club Colombia Dorada",
            desc="Cerveza tipo Lager, 330ml.",
            price=7500, image="https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=500"),
    Product(id="beb-10", category=Category.BEBIDAS, name="Agua Mineral con Gas 500ml",
            desc="Agua de manantial refrescante y con gas.",
            price=4500, image="https://images.unsplash.com/photo-1560023907-5f339617ea30?w=500"),
]


# ---------------------------------------------------------------------------
# Capa de acceso a datos (Repository Pattern)
# Aísla "cómo se guardan los datos" de "cómo se exponen por HTTP". Si mañana
# esto pasa de una lista en memoria a una base de datos real, las rutas de
# abajo no cambian ni una línea.
# ---------------------------------------------------------------------------
class ProductRepository:
    """Encapsula el acceso al catálogo de productos."""

    def __init__(self, products: list[Product]) -> None:
        self._products: dict[str, Product] = {p.id: p for p in products}

    def list_all(self) -> list[Product]:
        return list(self._products.values())

    def get_by_id(self, product_id: str) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise KeyError(product_id)
        return product

    def filter(
        self,
        category: Optional[Category] = None,
        featured: Optional[bool] = None,
        query: Optional[str] = None,
        available_only: bool = False,
    ) -> list[Product]:
        results = self.list_all()

        if category is not None:
            results = [p for p in results if p.category == category]
        if featured is not None:
            results = [p for p in results if p.featured == featured]
        if available_only:
            results = [p for p in results if p.available]
        if query:
            normalized = query.strip().lower()
            results = [
                p for p in results
                if normalized in p.name.lower() or normalized in p.desc.lower()
            ]
        return results

    def category_summary(self) -> list[CategorySummary]:
        counts: dict[str, int] = {}
        for product in self._products.values():
            counts[product.category.value] = counts.get(product.category.value, 0) + 1
        return [CategorySummary(name=name, total_products=total) for name, total in counts.items()]


repository = ProductRepository(PRODUCTS_DB)


# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="API Menú Digital Gastronómico — Fuego & Carbón",
    description="Catálogo de productos, categorías y disponibilidad del restaurante.",
    version="2.0.0",
)

# CORS: en desarrollo se permite cualquier origen para facilitar pruebas del
# frontend estático servido con file:// o un servidor local.
# En Firebase Hosting, el rewrite de /api/** hace que el navegador vea el
# mismo origen (tu-proyecto.web.app) tanto para el HTML como para la API,
# así que CORS deja de ser un problema en producción. Aun así, se restringe
# explícitamente por si alguien llama a Cloud Run directamente.
ALLOWED_ORIGINS = [
    "http://localhost:5000",       # firebase emulators:start (hosting)
    "http://127.0.0.1:5000",
    "https://TU-PROYECTO.web.app",       # <-- reemplaza por tu dominio real de Firebase
    "https://TU-PROYECTO.firebaseapp.com",  # <-- idem
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Red de seguridad: cualquier error no previsto se registra y responde
    de forma controlada, sin filtrar detalles internos al cliente."""
    logger.exception("Error no controlado en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error inesperado. Intenta nuevamente en unos minutos."},
    )


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthStatus, tags=["Meta"])
def health_check() -> HealthStatus:
    """Endpoint de salud para monitoreo/uptime checks."""
    return HealthStatus(status="ok", total_products=len(repository.list_all()))


@app.get("/api/categories", response_model=list[CategorySummary], tags=["Categorías"])
def get_categories() -> list[CategorySummary]:
    """Devuelve las categorías disponibles y cuántos productos tiene cada una.
    Permite al frontend construir su barra de filtros dinámicamente en vez
    de tenerla hardcodeada (y potencialmente desincronizada del backend)."""
    return repository.category_summary()


@app.get("/api/products", response_model=list[Product], tags=["Productos"])
def get_products(
    category: Optional[Category] = Query(default=None, description="Filtrar por categoría exacta."),
    featured: Optional[bool] = Query(default=None, description="Filtrar solo destacados ('Más Vendidas')."),
    q: Optional[str] = Query(default=None, min_length=1, max_length=80, description="Búsqueda libre por nombre/descripción."),
    available_only: bool = Query(default=True, description="Excluir productos agotados."),
) -> list[Product]:
    """Lista productos, con filtros opcionales combinables por categoría,
    destacado, texto de búsqueda y disponibilidad."""
    return repository.filter(
        category=category,
        featured=featured,
        query=q,
        available_only=available_only,
    )


@app.get("/api/products/{product_id}", response_model=Product, tags=["Productos"])
def get_product(product_id: str) -> Product:
    """Obtiene el detalle de un producto puntual por su id."""
    try:
        return repository.get_by_id(product_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un producto con id '{product_id}'.",
        ) from exc
