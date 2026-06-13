# SIH — Internações por agressão (X85–Y09), até 17 anos

Extrai do SIH (DataSUS via basedosdados, tabela `br_ms_sih.aihs_reduzidas`) a
contagem de internações por agressão (causas externas CID-10 **X85 a Y09**),
agregada por **município de residência (`id_municipio_paciente`) × ano × mês**,
para pessoas de **até 17 anos**.

Detalhes e armadilhas em [docs/documentacao.md](docs/documentacao.md);
dicionário das colunas em [docs/dicionario.md](docs/dicionario.md).

Cada linha do resultado: `ano, mes, id_municipio_residencia, internacoes_agressao`.

## Os dados (para colaboradores)

Os CSVs já estão versionados em [`data/`](data/) — **não precisa rodar nada nem
saber programar**. Baixe direto pelo GitHub: botão verde **Code → Download ZIP**,
ou abra o arquivo e clique em **Download raw file**.

- [`data/internacoes_agressao_munic_mes_ate17.csv`](data/internacoes_agressao_munic_mes_ate17.csv)
  — painel balanceado, 1 linha por município × mês:

  | Coluna | Descrição |
  |---|---|
  | `ano`, `mes` | competência da internação |
  | `id_municipio_residencia` | código IBGE de **6 dígitos** (residência do paciente) |
  | `internacoes_agressao` | nº de internações por agressão (X85–Y09), ≤17 anos; **0** onde não houve |

- [`data/completude_causa_externa_uf_ano.csv`](data/completude_causa_externa_uf_ano.csv)
  — % das internações por lesão com causa externa registrada, por UF/ano
  (diagnóstico de qualidade do dado).

> O painel balanceado tem ~935 mil linhas (muito zero). Abre no Excel, mas pesa.

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

## Uso (para regenerar os dados)

Só é necessário se você for **regenerar** os CSVs. Exige projeto GCP com
faturamento (quem só quer os dados, veja a seção acima).

```bash
pip install basedosdados pandas pandas-gbq pyarrow python-dotenv
gcloud auth application-default login
# crie um .env na raiz com:  BILLING_PROJECT_ID=seu-projeto-gcp
```

### Comandos

| Comando | O que faz |
|---|---|
| `python scripts/main.py` | **default:** `all` (extrair + completude) |
| `python scripts/main.py extrair` | extração principal → `data/...ate17.csv` |
| `python scripts/main.py completude` | qualidade do registro → `data/completude_...csv` |
| `python scripts/main.py diagnostico` | investigação da quebra de 2015 (só imprime) |
| `python scripts/main.py inspect` | esquema da tabela (só imprime) |
| `python scripts/main.py all` | extrair + completude |

### Opções

| Opção | Default | Descrição |
|---|---|---|
| `--start-year` | `2009` | ano inicial (2008 vem vazio no bd) |
| `--end-year` | `2022` | ano final |
| `--idade-max` | `17` | idade máxima (anos); define o filtro **e** o nome do arquivo (`...ate17.csv`) |
| `--balancear` / `--no-balancear` | balancear | painel completo (municípios × meses, zeros) vs só células com ≥1 internação |
| `--output` | `data/...ate{idade}.csv` | caminho de saída |
| `--billing-project` | do `.env` | projeto GCP com faturamento |

Os caminhos são resolvidos sozinhos — rode de onde quiser.

### Exemplos

```bash
# outro recorte etário (gera ...ate12.csv)
python scripts/main.py extrair --idade-max 12

# versão enxuta: só células com internação (~40k linhas, abre fácil no Excel)
python scripts/main.py extrair --no-balancear

# um ano só, para teste rápido
python scripts/main.py extrair --start-year 2022 --end-year 2022
```

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
