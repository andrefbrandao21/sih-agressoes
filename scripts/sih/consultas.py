"""Construtores de SQL para o BigQuery. Todas as queries usam o alias `d` para a
tabela e, quando precisam de idade, a CTE `dic_idade`."""

from . import config


def _cte_idade():
    return f"""WITH dic_idade AS (
      SELECT chave, valor
      FROM `{config.DATASET}.dicionario`
      WHERE nome_coluna = '{config.COL_UNIDADE_IDADE}'
        AND id_tabela = '{config.NOME_TABELA}'
    )"""


def filtro_idade(idade_max=None):
    """'Até N anos' inclui bebês (meses/dias) e exclui >N anos."""
    idade_max = config.IDADE_MAX_ANOS if idade_max is None else idade_max
    return f"""CASE
        WHEN UPPER(dic_idade.valor) LIKE '%ANO%' THEN SAFE_CAST(d.{config.COL_IDADE} AS INT64) <= {idade_max}
        WHEN dic_idade.valor IS NULL          THEN SAFE_CAST(d.{config.COL_IDADE} AS INT64) <= {idade_max}
        ELSE TRUE
      END"""


def _hit(col):
    return f"SUBSTR(d.{col}, 1, 3) BETWEEN '{config.CID_INI}' AND '{config.CID_FIM}'"


def filtro_cid():
    partes = [f"d.{c} BETWEEN '{config.CID_INI}' AND '{config.CID_FIM}'"
              for c in config.COLS_CID_CATEGORIA]
    partes += [_hit(c) for c in config.COLS_CID_SUBCATEGORIA]
    if not partes:
        raise ValueError("Nenhuma coluna de CID configurada em config.")
    return "(\n        " + "\n        OR ".join(partes) + "\n      )"


def query_extracao(ano, idade_max=None):
    filtro_tipo = (f"\n      AND d.{config.COL_TIPO_AIH} = '{config.VALOR_TIPO_AIH_NORMAL}'"
                   if config.COL_TIPO_AIH else "")
    return f"""
    {_cte_idade()}
    SELECT
      d.ano AS ano,
      d.mes AS mes,
      d.{config.COL_MUNICIPIO_RES} AS id_municipio_residencia,
      COUNT(*) AS internacoes_agressao
    FROM `{config.TABELA}` AS d
    LEFT JOIN dic_idade ON d.{config.COL_UNIDADE_IDADE} = dic_idade.chave
    WHERE d.ano = {ano}
      AND d.{config.COL_MUNICIPIO_RES} IS NOT NULL
      AND ({filtro_idade(idade_max)})
      AND {filtro_cid()}{filtro_tipo}
    GROUP BY ano, mes, id_municipio_residencia
    ORDER BY mes, id_municipio_residencia
    """


def query_municipios():
    """Universo de municípios para balancear o painel. Usa o código de 6 dígitos
    (id_municipio_6), que é o que o SIH (id_municipio_paciente) usa."""
    return """
    SELECT DISTINCT id_municipio_6
    FROM `basedosdados.br_bd_diretorios_brasil.municipio`
    WHERE id_municipio_6 IS NOT NULL
    ORDER BY id_municipio_6
    """


def query_inspecao():
    return f"""
    SELECT column_name, data_type
    FROM `{config.DATASET}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{config.NOME_TABELA}'
    ORDER BY ordinal_position
    """


def query_completude(ano):
    """% de internações por lesão (S/T) com causa externa (V–Y) registrada nos
    campos secundários, por UF (derivada do código do município).

    Sem filtro de idade de propósito: é um termômetro geral de qualidade de
    codificação (all-ages), priorizando poder estatístico/estabilidade em
    células UF×ano pequenas. Não confundir com o desfecho, que é ≤17 anos.
    """
    lesao = "SUBSTR(cid_principal_subcategoria, 1, 1) IN ('S','T')"
    tem_causa = " OR ".join(
        f"SUBSTR({c}, 1, 1) IN ('V','W','X','Y')" for c in config.COLS_CID_SUBCATEGORIA)
    com_causa = f"{lesao} AND ({tem_causa})"
    uf = f"SUBSTR({config.COL_MUNICIPIO_RES}, 1, 2)"
    return f"""
    SELECT
      ano,
      {uf} AS uf_codigo,
      COUNTIF({lesao}) AS internacoes_por_lesao,
      COUNTIF({com_causa}) AS com_causa_externa,
      SAFE_DIVIDE(COUNTIF({com_causa}), COUNTIF({lesao})) AS pct_preenchido
    FROM `{config.TABELA}`
    WHERE ano = {ano}
      AND {config.COL_MUNICIPIO_RES} IS NOT NULL
    GROUP BY ano, uf_codigo
    ORDER BY uf_codigo
    """


def query_diagnostico(ano_ini, ano_fim, idade_max=None):
    """Reproduz a investigação da quebra de 2015: por ano, conta crianças com
    agressão em cada campo secundário (campo único vs DIAGSEC1-9)."""
    diagsec = [f"cid_diagnostico_secundario_{i}_subcategoria" for i in range(1, 10)]
    any_diagsec = " OR ".join(_hit(c) for c in diagsec)
    child = filtro_idade(idade_max)
    return f"""
    {_cte_idade()}
    SELECT
      d.ano,
      COUNTIF(({child}) AND SUBSTR(d.cid_principal_subcategoria,1,1) IN ('S','T')) AS criancas_lesao,
      COUNTIF(({child}) AND {_hit('cid_secundario_subcategoria')}) AS ag_secun,
      COUNTIF(({child}) AND ({any_diagsec})) AS ag_diagsec_1a9,
      COUNTIF(({child}) AND ({_hit('cid_secundario_subcategoria')} OR {any_diagsec})) AS ag_qualquer
    FROM `{config.TABELA}` AS d
    LEFT JOIN dic_idade ON d.{config.COL_UNIDADE_IDADE} = dic_idade.chave
    WHERE d.ano BETWEEN {ano_ini} AND {ano_fim}
    GROUP BY d.ano
    ORDER BY d.ano
    """
