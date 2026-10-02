import csv
from functools import lru_cache 
from app.config import config 

@lru_cache(maxsize=None)
def load_csv_data(file_path: str):
    """"
    Carrega um CSV uma vez e armazena em cache. 
    """

    path = config.data_dir / file_path 
    if not path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")

    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return tuple(dict(row) for row in reader)

def get_categories(): 
    return load_csv_data("categories.csv") 

def get_products(): 
    return load_csv_data("products.csv") 

def get_promotions(): 
    return load_csv_data("promotions.csv") 

def get_costumers(): 
    return load_csv_data("costumers.csv") 

def get_orders(): 
    return load_csv_data("orders.csv") 

def get_order_items(): 
    return load_csv_data("order_items.csv") 

