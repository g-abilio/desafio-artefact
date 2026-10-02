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
    Normaliza texto para buscas sem diferença entre acentos e maiúsculas.

    Args:
        text: Texto original a ser normalizado.

    Returns:
        Texto em minúsculas e sem caracteres de acentuação.
    """

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf-8")
    return text.lower()

def json_response(data) -> str: 
    """
    Serializa o resultado de uma tool em JSON para que o agente possa ler.

    Args:
        data: Estrutura serializável em JSON.

    Returns:
        String JSON indentada, preservando caracteres Unicode.
    """

    return json.dumps(data, ensure_ascii = False, indent = 2)

def get_categories_by_id() -> dict[str, str]: 
    """
    Cria um dicionário com índice que associa cada ID ao nome de sua categoria.

    Returns:
        Dicionário no formato ``{category_id: category_name}``.
    """

    category_dict = {}

    categories = get_categories()
    for category in categories:
        category_dict[category["category_id"]] = category["name"]

    return category_dict

def find_active_promotion(product_id: str) -> dict[str, str] | None: 
    """
    Procura a promoção ativa associada a um produto.

    Args:
        product_id: Identificador do produto no catálogo.

    Returns:
        Dados da primeira promoção ativa encontrada ou ``None`` quando o produto
        não possuir promoção ativa.
    """

    for promotion in get_promotions(): 
        if (product_id == promotion["product_id"] and promotion["is_active"] == "1"): 
            return promotion

    return None

def calculate_product_prices(product: dict[str, str]) -> tuple[float, float, dict[str, str] | None]: 
    """
    Calcula o preço atual de um produto considerando uma possível promoção ativa.

    Args:
        product: Linha do produto carregada de ``products.csv``.

    Returns:
        Tupla contendo preço base, preço atual e dados da promoção. Quando não há
        promoção ativa, os dois preços são iguais e o terceiro item é ``None``.
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
    Converte o conteúdo JSON da coluna ``specs`` em um dicionário.

    Args:
        raw_specs: Texto JSON armazenado no CSV de produtos.

    Returns:
        Especificações convertidas, um dicionário vazio para entrada vazia ou um
        dicionário com ``raw_value`` quando o texto não for um JSON válido.
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
    Converte uma linha de produto em uma resposta estruturada para o agente.
    A resposta reúne categoria, disponibilidade, estoque, preços, promoção e
    especificações, convertendo os campos numéricos recebidos como texto no CSV.

    Args:
        product: Linha do produto carregada de ``products.csv``.
        categories_by_id: Dicionário com índice que associa IDs aos nomes das categorias.

    Returns:
        Dicionário com os dados consolidados do produto.
    """

    price_tuple = (calculate_product_prices(product))

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
    Busca opções de produtos no catálogo usando filtros estruturados.
    Use esta tool quando o cliente solicitar recomendações, produtos de uma marca
    ou categoria, opções dentro de um orçamento ou itens disponíveis em estoque.
    Todos os termos de ``query`` devem aparecer no nome, descrição, categoria ou
    especificações. Produtos não ativos são sempre ignorados.

    Args:
        query: Nome, marca, categoria ou característica procurada.
        max_price_brl: Preço atual máximo em reais.
        only_in_stock: Se verdadeiro, exclui produtos com estoque igual a zero.

    Returns:
        String JSON com a quantidade e a lista ordenada dos produtos encontrados,
        ou uma mensagem indicando que nenhum item corresponde aos filtros.
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
    Consulta os dados detalhados de um produto específico.
    Use esta tool quando o cliente mencionar um modelo e perguntar por preço,
    estoque, disponibilidade, promoção, descrição ou especificações. A busca
    aceita o nome completo ou parte dele e informa possíveis opções quando o
    termo corresponder a mais de um produto.

    Args:
        product_name: Nome completo ou trecho do nome do produto.

    Returns:
        String JSON com o produto encontrado, sugestões em caso de ambiguidade ou
        uma mensagem indicando que o produto não existe no catálogo.
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
    Consulta um pedido após validar seu número e o e-mail do cliente.
    Use esta tool somente quando o cliente fornecer as duas informações. A mesma
    resposta de erro é usada para pedido inexistente e e-mail incorreto, evitando
    confirmar a existência de dados para uma pessoa não validada.

    Args:
        order_id: Número identificador do pedido.
        customer_email: E-mail associado ao cliente que realizou a compra.

    Returns:
        String JSON com status, valor histórico, pagamento, rastreamento, previsão
        de entrega, observações e itens; ou uma mensagem genérica de não encontrado.
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
    Consulta informações gerais e políticas oficiais da loja por RAG.
    Use esta tool para perguntas sobre endereço, horários, pagamentos, promoções,
    trocas, devoluções, garantias, frete, entregas e procedimentos de atendimento.

    Args:
        question: Pergunta do cliente a ser pesquisada no manual de políticas.

    Returns:
        Trechos do manual semanticamente relacionados à pergunta, acompanhados do
        número da página de origem.
    """

    return retrieve_store_policies(question)
