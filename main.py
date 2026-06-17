from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Product
from schemas import ProductCreate, StockUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚠️  Wiping existing database tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🚀 Creating fresh database tables...")
    Base.metadata.create_all(bind=engine)
    
    yield  # The application runs while paused here
    
    print("🛑 Shutting down application...")

# Pass the lifespan handler into FastAPI
app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    db = SessionLocal()
    products = db.query(Product).all()
    product_status = {}

    for product in products:
        if product.stock == 0:
            product_status[product.id] = "Out of Stock"
        elif product.stock <= 3:
            product_status[product.id] = "Low Stock"
        else:
            product_status[product.id] = "In Stock"

    total_products = len(products)
    total_stock = sum(product.stock for product in products)
    low_stock = len([p for p in products if 0 < p.stock <= 3])
    out_stock = len([p for p in products if p.stock == 0])

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "product_status": product_status,
            "total_products": total_products,
            "total_stock": total_stock,
            "low_stock": low_stock,
            "out_stock": out_stock
        }
    )


@app.post("/add-product")
def add_product_form(
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...)
):
    db = SessionLocal()
    product = Product(
        name=name,
        category=category,
        price=price,
        stock=stock
    )
    db.add(product)
    db.commit()
    db.close()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@app.post("/update-stock/{product_id}/{change}")
def update_stock_from_ui(
    product_id: int,
    change: int
):
    db = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product:
        new_stock = product.stock + change
        if new_stock >= 0:
            product.stock = new_stock
            db.commit()

    db.close()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@app.post("/products")
def add_product(product: ProductCreate):
    db: Session = SessionLocal()
    new_product = Product(
        name=product.name,
        category=product.category,
        price=product.price,
        stock=product.stock
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    db.close()

    return {
        "id": new_product.id,
        "name": new_product.name,
        "category": new_product.category,
        "price": new_product.price,
        "stock": new_product.stock
    }


@app.get("/products")
def get_products():
    db: Session = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return products


@app.put("/products/{product_id}/stock")
def update_stock(
    product_id: int,
    stock_update: StockUpdate
):
    db: Session = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        db.close()
        return {"error": "Product not found"}

    new_stock = product.stock + stock_update.change

    if new_stock < 0:
        db.close()
        return {"error": "Stock cannot be negative"}

    product.stock = new_stock
    db.commit()
    db.refresh(product)
    db.close()

    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "stock": product.stock
    }


@app.get("/products/low-stock")
def get_low_stock_products():
    db: Session = SessionLocal()
    products = (
        db.query(Product)
        .filter(
            Product.stock > 0,
            Product.stock <= 3
        )
        .all()
    )
    db.close()
    return products