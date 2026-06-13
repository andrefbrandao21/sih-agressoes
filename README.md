# SIH — Internações por agressão (X85–Y09), até 17 anos

Extrai do SIH (DataSUS via basedosdados, tabela `br_ms_sih.aihs_reduzidas`) a
contagem de internações por agressão (causas externas CID-10 **X85 a Y09**),
agregada por **município de residência (`id_municipio_paciente`) × ano × mês**,
para pessoas de **até 17 anos**.

Detalhes e armadilhas em [docs/documentacao.md](docs/documentacao.md);
dicionário das colunas em [docs/dicionario.md](docs/dicionario.md).

Cada linha do resultado: `ano, mes, id_municipio_residencia, internacoes_agressao`.

## Estrutura

```
sih_agressoes/
├── .env                  # BILLING_PROJECT_ID (não versionado)
├── README.md
├── docs/
│   ├── documentacao.md   # metodologia, armadilhas, limitações
│   └── dicionario.md     # dicionário de colunas da aihs_reduzidas
├── scripts/
│   ├── main.py           # orquestrador (CLI)
│   └── sih/              # pacote
│       ├── config.py     # caminhos, .env, constantes de esquema
│       ├── consultas.py  # construtores de SQL
│       ├── bq.py         # acesso ao BigQuery
│       └── pipeline.py   # extrair / completude / diagnostico / inspect
└── data/
    ├── internacoes_agressao_munic_mes_ate17.csv   # saída principal
    └── completude_causa_externa_uf_ano.csv        # qualidade do registro
```

## Uso

```bash
pip install basedosdados pandas pandas-gbq pyarrow python-dotenv
gcloud auth application-default login
# coloque BILLING_PROJECT_ID no .env

python scripts/main.py                # default: all (extrair + completude)
python scripts/main.py inspect        # confere o esquema da tabela
python scripts/main.py extrair        # extração principal (2009–2022)
python scripts/main.py completude     # qualidade do registro
python scripts/main.py diagnostico    # investigação da quebra de 2015
python scripts/main.py all            # extrair + completude
```

Opções: `--start-year`, `--end-year`, `--idade-max`, `--billing-project`,
`--output`. O billing vem do `.env`; os caminhos são resolvidos sozinhos
(rode de onde quiser). Saída principal:
`data/internacoes_agressao_munic_mes_ate17.csv`.

## Decisões embutidas (e como ajustar)

- **Onde o X85–Y09 é procurado:** nos diagnósticos secundários em `subcategoria`
  (4 chars) — `cid_secundario_subcategoria` (até 2014) + os 9
  `cid_diagnostico_secundario_N_subcategoria` (2015+). As colunas `categoria` e
  `cid_causa_*` são furadas no basedosdados — ver `docs/documentacao.md` §4.
- **Idade ≤ 17 anos:** definida por `IDADE_MAX_ANOS`. A unidade
  (`unidade_medida_idade_paciente`) é resolvida pelo dicionário; bebês em
  meses/dias entram; só excluímos >17 quando a unidade é "Anos".
- **Município de residência:** `id_municipio_paciente` (não o do estabelecimento).
- **AIH de continuação** infla `COUNT(*)`. Para contar só AIH normal, defina
  `COL_TIPO_AIH = "tipo_aih"` e o código de AIH normal (confira no dicionário).

## Cuidado de identificação

Como agressão é a **variável de resultado** num painel município×tempo, rode
`--completude` antes: se a completude da causa externa tiver tendência ou variar
com o tratamento, o efeito estimado pode ser artefato de registro, não violência.
