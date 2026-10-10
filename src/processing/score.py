import pandas as pd


def calculate_score(volume: float, cpc: float, difficulty: float) -> float:
    if difficulty == 0:
        return 0.0
    return (volume * cpc) / difficulty


def rank_keywords(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["score"] = df.apply(
        lambda r: calculate_score(r["volume"], r["cpc"], r["difficulty"]), axis=1
    )
    return df.sort_values("score", ascending=False).head(top_n)
