import json
import unicodedata
from typing import Any
from langchain.tools import tool 
from app.rag import retrieve_store_policies
from app.data_store import (
    get_categories,
    get_customers,
    get_order_items,
    get_orders,
    get_products,
    get_promotions,
)

def normalize_text(text: str) -> str:
    """
    Normaliza o texto removendo acentos e convertendo para minúsculas.
    Facilita as buscas e comparações de strings. 
    """

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf-8")
    return text.lower()

def json_response(data) -> str: 
    """"
    Converte os resultados das tools em um JSON formatado.
    """

    return json.dumps(data, ensure_ascii = False, indent = 2)

def get_categories_by_id() -> dict[str, str]: 
    """
    Associa o nome da categoria ao seu id.
    """

    category_dict = {}

    categories = get_categories()
    for category in categories:
        category_dict[category["category_id"]] = category["name"]

    return category_dict

def find_active_promotion(product_id: str) -> dict[str, str] | None: 
    """"
    Procura uma promoção ativa para o produto em foco.
    """

    for promotion in get_promotions(): 
        if (product_id == promotion["product_id"] and promotion["is_active"] == "1"): 
            return promotion

    return None

def calculate_product_prices(product: dict[str, str]) -> tuple[float, float, dict[str, str] | None]: 
    """
    Calcula o preço atual de um produto considerando uma possível promoção ativa
    """

    base_price = float(product["price_brl"])
    promotion = find_active_promotion(product["product_id"])

    if promotion is None: 
        return base_price, base_price, None

    discount_percent = float(promotion["discount_percent"])
    current_price = base_price * (1 - discount_percent/100)

    return base_price, current_price, promotion

def parse_specs(raw_specs: str) -> dict[str, Any]: 
    """
    Converte a coluna specs, que tem um JSON.
    """

    if not raw_specs: 
        return {} 

    try: 
        return json.loads(raw_specs)
    except json.JSONDecodeError: 
        return {
            "raw_value": raw_specs
        }

def product_to_response(product: dict[str, str], categories_by_id: dict[str, str]) -> dict[str, Any]:
    """
    Transforma uma linha de produto em um formato adequado para ser entregue ao agente.
    """

    price_tuple = (calculate_product_prices(product))

    # base_price, current_price, promotion

    stock_quantity = int(product["stock_quantity"])
    status = product["status"]

    if status == "discontinued":
        availability = "Produto descontinuado"
    elif status == "coming_soon":
        availability = "Produto ainda não disponível para venda"
    elif stock_quantity <= 0:
        availability = "Sem estoque"
    else:
        availability = "Disponível"

    promotion_data = None
    promotion = price_tuple[2]
    if promotion is not None:
        promotion_data = {
            "description": promotion["description"],
            "discount_percent": float(promotion["discount_percent"]),
        }

    base_price, current_price = price_tuple[0], price_tuple[1]
    return {
        "product_id": int(product["product_id"]),
        "name": product["name"],
        "category": categories_by_id.get(
            product["category_id"],
            "Categoria desconhecida"
        ),
        "description": product["description"],
        "status": status,
        "availability": availability,
        "stock_quantity": stock_quantity,
        "price": {
            "base_brl": base_price,
            "current_brl": current_price,
        },
        "promotion": promotion_data,
        "specs": parse_specs(product["specs"]),
    }

@tool 
def search_products(query: str, max_price_brl: float, only_in_stock: bool) -> str:
    """
    Busca produtos pelo nome, descrição ou categoria, filtrando por preço máximo e disponibilidade em estoque.
    """

    normalized_query = normalize_text(query)
    query_words = normalized_query.split() 

    categories_by_id = get_categories_by_id()
    results = [] 

    for product in get_products():
        # Verifica se o produto está ativo
        if product["status"] != "active":
            continue 

        stock_quantity = int(product["stock_quantity"])
        # Verifica se o produto está em estoque
        if only_in_stock and stock_quantity <= 0:
            continue

        category_name = categories_by_id.get(product["category_id"], "",)
        searchable_text = normalize_text(" ".join(
                [
                    product["name"],
                    product["description"],
                    category_name,
                    product["specs"],
                ]
            )
        )

        # Todos os termos precisam aparecer em algum lugar dos dados do produto.
        if not all(term in searchable_text for term in query_words):
            continue

        price_tuple = calculate_product_prices(product)
        current_price = price_tuple[1] 

        if (max_price_brl is not None and current_price > max_price_brl):
            continue

        results.append(product_to_response(product, categories_by_id))

    results.sort( key=lambda item: (
            item["price"]["current_brl"],
            item["name"]
        )
    )

    total_results = len(results)

    if not results:
        return json_response(
            {
                "found": False,
                "count": 0,
                "message": (
                    "Nenhum produto foi encontrado com os filtros informados."
                ),
                "products": [],
            }
        )

    return json_response(
        {
            "found": True,
            "count": total_results,
            "products": results,
        }
    )

@tool 
def get_product_details(product_name: str) -> str:
    """
    Consulta preço, estoque, situação e promoção de um produto.
    """

    normalized_query = normalize_text(product_name)

    if not normalized_query: 
        return json_response(
            {
                "found": False,
                "message": "Informe o nome do produto.",
            }
        )

    products = list(get_products()) 

    exact_matches = [] 
    for product in products: 
        if normalize_text(product["name"]) == normalized_query: 
            exact_matches.append(product)

    partial_matches = [] 
    for product in products:
        if normalized_query in normalize_text(product["name"]): 
            partial_matches.append(product)

    if exact_matches:
        selected_product = exact_matches[0]
    elif len(partial_matches) == 1:
        selected_product = partial_matches[0]
    elif len(partial_matches) > 1:
        suggestions = [] 
        for product in partial_matches: 
            suggestions.append(product["name"])

        return json_response(
            {
                "found": False,
                "ambiguous": True,
                "message": (
                    "Mais de um produto corresponde ao nome informado. Peça ao cliente para escolher um modelo mais específico."
                ),
                "suggestions": suggestions,
            }
        )
    else:

        return json_response(
            {
                "found": False,
                "message": (
                    "Produto não encontrado no catálogo."
                ),
            }
        )

    categories_by_id = get_categories_by_id()
    return json_response(
        {
            "found": True,
            "product": product_to_response(
                selected_product,
                categories_by_id
            ),
        }
    )

@tool 
def get_order_status(order_id: int, customer_email: str) -> str:
    """
    Consulta o status de um pedido pelo ID e e-mail do cliente.
    """

    order = next(
        (order for order in get_orders() if order["order_id"] == str(order_id)),
        None
    )

    error_response = {
        "found": False,
        "message": "Pedido não encontrado para o número e e-mail informados.",
    }

    if order is None:
        return json_response(error_response)

    customer = next(
        (customer for customer in get_customers() if customer["customer_id"] == order["customer_id"]),
        None
    )
    if customer is None:
        return json_response(error_response)

    if customer["email"].strip().lower() != customer_email.strip().lower():
        return json_response(error_response)

    products_by_id = {
        product["product_id"]: product["name"] for product in get_products()
    }

    items = []
    for item in get_order_items():
        if item["order_id"] == str(order_id):
            items.append(
                {
                    "product_id": int(item["product_id"]),
                    "product_name": products_by_id.get(
                        item["product_id"],
                        "Produto não encontrado"
                    ),
                    "quantity": int(item["quantity"]),
                }
            )

    return json_response(
        {
            "found": True,
            "order": {
                "order_id": int(order["order_id"]),
                "order_date": order["order_date"],
                "status": order["status"],
                "total_brl": float(order["total_brl"]),
                "payment_method": order["payment_method"],
                "tracking_code": order["tracking_code"] or None,
                "estimated_delivery": order["estimated_delivery"] or None,
                "notes": order["notes"] or None,
                "items": items,
            },
        }
    )

@tool
def consult_store_policies(question: str) -> str:
    """
    Consulta as políticas oficiais da loja.
    """

    return retrieve_store_policies(question)