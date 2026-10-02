import json
import pytest

from app.tools import (
    get_order_status,
    get_product_details,
    search_products,
)

def test_search_yamaha_products():
    """
    Verifica a busca de produtos Yamaha dentro do limite de preço.
    """

    response = search_products.invoke(
        {
            "query": "Yamaha",
            "max_price_brl": 1000,
            "only_in_stock": True
        }
    )

    result = json.loads(response)

    assert result["found"] is True
    assert result["count"] == 3

def test_get_product_details():
    """
    Verifica os detalhes retornados para um produto conhecido.
    """

    response = get_product_details.invoke(
        {
            "product_name": "Takamine GD20",
        }
    )

    result = json.loads(response)
    product = result["product"]

    assert result["found"] is True
    assert product["product_id"] == 95
    assert product["price"]["current_brl"] == 2199.0
    assert product["stock_quantity"] == 5

def test_active_promotion():
    """
    Verifica a aplicação de uma promoção ativa ao preço do produto.
    """

    response = get_product_details.invoke(
        {
            "product_name": "Taylor 110e",
        }
    )

    result = json.loads(response)
    product = result["product"]

    assert product["price"]["base_brl"] == 5999.0
    assert product["price"]["current_brl"] == 5519.08
    assert product["promotion"]["discount_percent"] == 8.0

def test_get_order_status():
    """
    Verifica a consulta de pedido com número e e-mail válidos.
    """

    response = get_order_status.invoke(
        {
            "order_id": 1,
            "customer_email": "pedro.oliveira@jmail.com",
        }
    )

    result = json.loads(response)

    assert result["found"] is True
    assert result["order"]["status"] == "delivered"
    assert result["order"]["total_brl"] == 11499.0

def test_rejects_wrong_email():
    """
    Verifica que um e-mail incorreto não permite consultar o pedido.
    """

    response = get_order_status.invoke(
        {
            "order_id": 1,
            "customer_email": "wrong@example.com",
        }
    )

    result = json.loads(response)

    assert result["found"] is False

def test_product_not_found():
    """
    Verifica a resposta para um produto inexistente no catálogo.
    """

    response = get_product_details.invoke(
        {
            "product_name": "Produto xyz",
        }
    )

    result = json.loads(response)

    assert result["found"] is False
    assert result["message"] == ("Produto não encontrado no catálogo.")