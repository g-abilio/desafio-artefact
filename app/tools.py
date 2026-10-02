from langchain.tools import tool 

@tool 
def search_products(query: str, max_price_brl: float, only_in_stock: bool) -> str:
    """
    Busca produtos pelo nome, descrição ou categoria, filtrando por preço máximo e disponibilidade em estoque.
    """

@tool 
def get_product_details(product_name: str) -> str:
    """
    Consulta preço, estoque, situação e promoção de um produto.
    """

@tool 
def get_order_status(order_id: int, customer_email: str) -> str:
    """
    Consulta o status de um pedido pelo ID e e-mail do cliente.
    """