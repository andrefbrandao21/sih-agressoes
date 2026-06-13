"""Configuração central: caminhos, .env/billing e constantes de esquema.

As armadilhas de coluna estão documentadas em docs/dicionario.md. Os nomes aqui
foram confirmados via `main.py inspect` contra br_ms_sih.aihs_reduzidas.
"""

import os

# sih_agressoes/  (scripts/sih/config.py -> sobe 3 níveis)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass  # sem python-dotenv: use env var do sistema ou --billing-project


def get_billing(cli_value=None):
    """Resolve o billing_project_id (CLI > .env/env var)."""
    bp = cli_value or os.environ.get("BILLING_PROJECT_ID")
    if not bp:
        raise SystemExit(
            "ERRO: defina BILLING_PROJECT_ID no .env ou use --billing-project.")
    return bp


# ---------------------------------------------------------------------------
# Esquema da tabela
# ---------------------------------------------------------------------------
TABELA = "basedosdados.br_ms_sih.aihs_reduzidas"
DATASET = "basedosdados.br_ms_sih"
NOME_TABELA = "aihs_reduzidas"

# Município de residência do paciente (IBGE 7 díg.). sigla_uf vem vazia -> UF
# deve ser derivada de SUBSTR(COL_MUNICIPIO_RES, 1, 2).
COL_MUNICIPIO_RES = "id_municipio_paciente"

# Idade só faz sentido com a unidade (anos/meses/dias), resolvida pelo dicionário.
COL_IDADE = "idade_paciente"
COL_UNIDADE_IDADE = "unidade_medida_idade_paciente"
IDADE_MAX_ANOS = 17  # default; parametrizável na CLI

# Bloco CID-10 de agressão (categoria de 3 chars; X85..Y09 são contíguos).
CID_INI = "X85"
CID_FIM = "Y09"

# Onde mora o X85–Y09 (ver docs): usar SUBCATEGORIA (categoria é furada);
# cid_causa_* só até 2014; secundário migra de campo único p/ DIAGSEC1-9 em 2015.
COLS_CID_CATEGORIA = []  # não usar categoria
COLS_CID_SUBCATEGORIA = [
    "cid_secundario_subcategoria",                      # DIAG_SECUN (≤2014)
] + [
    f"cid_diagnostico_secundario_{i}_subcategoria" for i in range(1, 10)  # DIAGSEC (2015+)
]

# Para contar só AIH normal (excluir continuação/longa permanência), defina
# COL_TIPO_AIH = "tipo_aih" e o código normal. None = conta todas as AIH.
COL_TIPO_AIH = None
VALOR_TIPO_AIH_NORMAL = "1"
