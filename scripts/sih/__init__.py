"""Pacote do pipeline SIH — internações por agressão (X85–Y09).

Módulos:
    config     — caminhos, .env, billing e constantes de esquema/colunas
    consultas  — construtores de SQL (filtros e queries)
    bq         — wrapper de leitura no BigQuery e loop ano-a-ano
    pipeline   — orquestração de alto nível (extrair, completude, etc.)
"""
