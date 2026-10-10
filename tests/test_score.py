import pytest, asyncio
from src.processing.score import rank_keywords
import pandas as pd

def test_rank_keywords():
    df = pd.DataFrame({"volume": [1000,2000,500], "cpc": [0.5,0.3,1.0], "difficulty": [10,5,20]})
    top = rank_keywords(df, top_n=2)
    assert len(top) == 2
    # highest score should be first
    assert top.iloc[0]["score"] >= top.iloc[1]["score"]
