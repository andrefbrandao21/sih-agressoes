"""Orquestração de alto nível. Cada função recebe o billing e devolve um
DataFrame; as que produzem artefato também salvam em data/."""

import os

import pandas as pd

from . import bq, config, consultas


def _saida_extracao(idade_max):
    return os.path.join(
        config.DATA_DIR, f"internacoes_agressao_munic_mes_ate{idade_max}.csv")


def _balancear(df, start, end, billing):
    """Expande para painel balanceado: todos os municípios (IBGE) × todos os
    meses do período, com zero onde não houve internação."""
    municipios = (bq.read_sql(consultas.query_municipios(), billing)
                  ["id_municipio_6"].astype(str).tolist())
    df = df.copy()
    df["id_municipio_residencia"] = df["id_municipio_residencia"].astype(str)

    fora = int(df.loc[~df["id_municipio_residencia"].isin(municipios),
                      "internacoes_agressao"].sum())
    grid = pd.MultiIndex.from_product(
        [range(start, end + 1), range(1, 13), municipios],
        names=["ano", "mes", "id_municipio_residencia"]).to_frame(index=False)
    out = grid.merge(df, on=["ano", "mes", "id_municipio_residencia"], how="left")
    out["internacoes_agressao"] = out["internacoes_agressao"].fillna(0).astype(int)

    print(f"[balanceamento] {len(municipios):,} municípios × "
          f"{(end - start + 1) * 12} meses = {len(out):,} linhas")
    if fora:
        print(f"[balanceamento] AVISO: {fora} internações em municípios fora do "
              f"diretório IBGE foram descartadas.")
    return out


def inspecionar(billing):
    """Imprime o esquema da tabela (nomes e tipos das colunas)."""
    df = bq.read_sql(consultas.query_inspecao(), billing)
    pd.set_option("display.max_rows", None)
    print(f"Esquema de {config.TABELA}\n")
    print(df.to_string(index=False))
    return df


def extrair(billing, start, end, idade_max=None, output=None, balancear=True):
    """Extração principal: agressão por município de residência × ano × mês.

    balancear=True (default) devolve painel balanceado (todos os municípios ×
    meses, zeros preenchidos); False devolve só as células com ≥1 internação.
    """
    idade_max = config.IDADE_MAX_ANOS if idade_max is None else idade_max
    output = output or _saida_extracao(idade_max)
    df = bq.extrair_por_ano(
        lambda ano: consultas.query_extracao(ano, idade_max),
        range(start, end + 1), billing)
    if balancear:
        df = _balancear(df, start, end, billing)
    df = (df.sort_values(["ano", "mes", "id_municipio_residencia"])
            .reset_index(drop=True))
    os.makedirs(config.DATA_DIR, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"\nOK. {len(df):,} linhas salvas em {output}")
    print(df.head(10).to_string(index=False))
    return df


def completude(billing, start, end, output=None):
    """Diagnóstico de qualidade do registro da causa externa, por UF/ano."""
    output = output or os.path.join(
        config.DATA_DIR, "completude_causa_externa_uf_ano.csv")
    df = bq.extrair_por_ano(consultas.query_completude,
                            range(start, end + 1), billing, rotulo="completude")
    os.makedirs(config.DATA_DIR, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"\nSalvo: {output}")
    return df


def diagnosticar(billing, start, end, idade_max=None):
    """Reproduz a investigação da quebra estrutural de 2015 (não salva)."""
    df = bq.read_sql(consultas.query_diagnostico(start, end, idade_max), billing)
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print(df.to_string(index=False))
    return df
