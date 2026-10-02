import csv
from functools import lru_cache 
from app.config import config 

@lru_cache(maxsize=None)
def load_csv_data(file_path: str):
    """
    Carrega um arquivo CSV da pasta de dados e mantém o resultado em cache.
    Cada arquivo é lido apenas na primeira chamada. As linhas são convertidas em
    dicionários e retornadas como uma tupla para reutilização pelas tools.

    Args:
        file_path: Nome do arquivo CSV relativo a ``config.data_dir``.

    Returns:
        Tupla de dicionários, em que cada dicionário representa uma linha do CSV.

    Raises:
        FileNotFoundError: Se o arquivo solicitado não existir na pasta de dados.
    """

    path = config.data_dir / file_path 
    if not path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")

    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return tuple(dict(row) for row in reader)

def get_categories(): 
    """
    Retorna as categorias cadastradas em ``categories.csv``.
    """
    return load_csv_data("categories.csv") 

def get_products(): 
    """
    Retorna os produtos cadastrados em ``products.csv``.
    """
    return load_csv_data("products.csv") 

def get_promotions(): 
    """
    Retorna as promoções cadastradas em ``promotions.csv``.
    """
    return load_csv_data("promotions.csv") 

def get_customers(): 
    """
    Retorna os clientes cadastrados em ``customers.csv``.
    """
    return load_csv_data("customers.csv") 

def get_orders(): 
    """
    Retorna os pedidos cadastrados em ``orders.csv``.
    """
    return load_csv_data("orders.csv") 

def get_order_items(): 
    """
    Retorna os itens de pedidos cadastrados em ``order_items.csv``.
    """
    return load_csv_data("order_items.csv") 
