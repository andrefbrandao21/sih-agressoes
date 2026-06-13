"""Orquestrador do pipeline SIH — internações por agressão (X85–Y09).

Uso:
    python scripts/main.py                         # default: all (extrair + completude)
    python scripts/main.py inspect                 # esquema da tabela
    python scripts/main.py extrair                 # extração principal
    python scripts/main.py completude              # qualidade do registro
    python scripts/main.py diagnostico             # investigação da quebra de 2015
    python scripts/main.py all                     # extrair + completude

Opções comuns: --billing-project, --start-year, --end-year, --idade-max.
O billing vem do .env (BILLING_PROJECT_ID) se não for passado.
"""

import argparse
import os
import sys

# garante que o pacote `sih` (ao lado deste arquivo) seja importável
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sih import config, pipeline  # noqa: E402


def build_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--billing-project", default=None,
                   help="Projeto GCP com faturamento (ou BILLING_PROJECT_ID no .env).")
    p.add_argument("--start-year", type=int, default=2009,  # 2008 vazio no bd
                   help="Ano inicial (default 2009).")
    p.add_argument("--end-year", type=int, default=2022,
                   help="Ano final (default 2022).")
    p.add_argument("--idade-max", type=int, default=config.IDADE_MAX_ANOS,
                   help=f"Idade máxima em anos (default {config.IDADE_MAX_ANOS}).")
    p.add_argument("--output", default=None,
                   help="Caminho de saída (default em data/).")
    p.add_argument("--balancear", action=argparse.BooleanOptionalAction, default=True,
                   help="Painel balanceado (todos municípios × meses, zeros "
                        "preenchidos). Use --no-balancear p/ só células com dado.")
    p.add_argument("comando", nargs="?", default="all",
                   choices=["inspect", "extrair", "completude",
                            "diagnostico", "all"],
                   help="O que executar (default: all).")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    bp = config.get_billing(args.billing_project)
    c = args.comando

    if c == "inspect":
        pipeline.inspecionar(bp)
    elif c == "extrair":
        pipeline.extrair(bp, args.start_year, args.end_year,
                         args.idade_max, args.output, args.balancear)
    elif c == "completude":
        pipeline.completude(bp, args.start_year, args.end_year, args.output)
    elif c == "diagnostico":
        pipeline.diagnosticar(bp, args.start_year, args.end_year, args.idade_max)
    elif c == "all":
        print("== EXTRAÇÃO ==")
        pipeline.extrair(bp, args.start_year, args.end_year,
                         args.idade_max, balancear=args.balancear)
        print("\n== COMPLETUDE ==")
        pipeline.completude(bp, args.start_year, args.end_year)


if __name__ == "__main__":
    main()
