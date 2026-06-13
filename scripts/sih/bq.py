"""Acesso ao BigQuery via basedosdados."""

import basedosdados as bd
import pandas as pd


def read_sql(query, billing):
    return bd.read_sql(query, billing_project_id=billing)


def extrair_por_ano(query_fn, anos, billing, rotulo="extracao"):
    """Roda `query_fn(ano)` para cada ano (uma partição por query) e concatena."""
    frames = []
    for ano in anos:
        print(f"[{rotulo}] {ano} ...", flush=True)
        df = read_sql(query_fn(ano), billing)
        print(f"           {len(df):,} linhas", flush=True)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
