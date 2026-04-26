# test_ranking.py

from src.db_utils import load_price_data
from src.ranking import create_volume_ranking

df = load_price_data()
ranking = create_volume_ranking(df)

print(ranking.head(10))