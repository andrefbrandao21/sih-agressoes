# Internações por agressão em crianças e adolescentes (≤17 anos) — SIH/DataSUS

Documentação do pipeline em `sih_agressoes/`. Extrai do SIH a contagem de
internações por **agressão** (causas externas CID-10 **X85–Y09**) em pessoas
de **até 17 anos**, agregada por **município de residência × ano × mês**.

---

## 1. Objetivo e desenho

- **Desfecho:** violência **não-letal** que gera internação hospitalar no SUS.
- **Papel analítico:** **variável de resultado** num painel município×tempo
  (algum choque/política → agressões contra crianças).
- **Unidade do dado final:** `(ano, mes, id_municipio_residencia)`; valor =
  total de AIH com CID de agressão.

Por ser desfecho num painel, a qualidade do **registro** (não só o volume real)
importa para a identificação — ver §5.

## 2. Fonte

- Tabela: `basedosdados.br_ms_sih.aihs_reduzidas` (SIH-RD, AIH reduzidas).
- Acesso: BigQuery via `basedosdados`, com `BILLING_PROJECT_ID` no `.env`.
- Cobertura efetiva: **2009–2022** (2008 vem vazio no basedosdados).

## 3. Definição do desfecho

### CID de agressão
Bloco **X85–Y09** ("agressões") do capítulo XX (causas externas) da CID-10.
Filtro lexicográfico no prefixo de 3 caracteres: `BETWEEN 'X85' AND 'Y09'`
(X85..X99, Y00..Y09 são contíguos).

### Onde o código mora no SIH — atenção
No SIH a internação por agressão tem:
- `cid_principal` = a **lesão** (capítulo XIX, S/T) — *não* é o X85–Y09;
- a **causa externa** (X85–Y09) registrada num campo secundário.

A estrutura desse campo **mudou em 2015** (ver §4). O pipeline cobre as duas
épocas escaneando, em `subcategoria` (4 chars):

| Campo | Período em que carrega o sinal |
|---|---|
| `cid_secundario_subcategoria` (DIAG_SECUN, campo único) | até 2014 |
| `cid_diagnostico_secundario_1..9_subcategoria` (DIAGSEC1-9) | 2015+ |

Um AIH é contado **uma vez** se a agressão aparecer em qualquer um desses campos.

### Idade ≤ 17 anos
`idade_paciente` vem com unidade codificada (`unidade_medida_idade_paciente`),
resolvida pelo dicionário do basedosdados. Regra (limite em `IDADE_MAX_ANOS`):
- unidade = "Anos" → inclui se `idade_paciente ≤ 17`;
- unidade em meses/dias/horas → **sempre inclui** (é < 1 ano);
- unidade nula → inclui se `idade_paciente ≤ 17`.

Assim bebês não são excluídos nem confundidos com "12 anos".

### Município
`id_municipio_paciente` = **residência** do paciente (não o do estabelecimento),
para alinhar o desfecho ao local onde o tratamento/choque incide.

## 4. A armadilha resolvida (quebra estrutural de 2015)

A primeira extração tinha 2008 e 2015–2018 **zerados** e 2019+ quase vazio.
Investigação (`diagnostico.py`) revelou:

1. **Colunas `categoria` (3 chars) são furadas** no basedosdados
   (ex.: `cid_causa_categoria` tinha ~18 mil preenchidos vs ~91 mil em
   `cid_causa_subcategoria`). → **Usar sempre `subcategoria`.**
2. **`cid_causa_*` (causa externa) só é preenchido até 2014.** Inútil depois.
3. O sinal real está nos **diagnósticos secundários**, que migraram de campo
   único (`DIAG_SECUN`) para nove campos (`DIAGSEC1-9`) em 2015.

Com a correção, a série fica contínua e o denominador (crianças com lesão S/T)
permanece estável (~110–121 mil/ano), confirmando que houve só **mudança de
campo**, não quebra real.

Totais por ano (≤17 anos, Brasil):

```
2009 5263   2013 7165   2017 6642   2021 3906
2010 6264   2014 6822   2018 5493   2022 3281
2011 7693   2015 6587   2019 4936
2012 7298   2016 6568   2020 4101
```

## 5. Limitações e ameaças à identificação

- **Viés de seleção:** capta só a agressão grave o suficiente para internar no
  SUS. Não é incidência de violência; depende de acesso e oferta hospitalar.
- **Completude da causa externa (medida, ver §5.1)** é alta e estável no
  agregado, mas muda de forma **heterogênea entre UFs** → ameaça se o tratamento
  se correlaciona com essas mudanças. Use `completude_causa_externa_uf_ano.csv`
  como controle ou cheque robustez.
- **Quebra de campo em 2015:** ainda que a contagem fique contínua, a *fonte*
  muda. Considere dummy pós-2015 ou checagem de robustez.
- **Tendência de queda 2015→2022** (2163 → 1203) com denominador estável:
  investigar se é real ou de codificação antes de interpretar.
- **AIH ≠ pessoa:** reinternações e AIH de continuação podem inflar `COUNT(*)`.
  Para contar só AIH normal, configure `COL_TIPO_AIH` no script.
- **Subnotificação/intenção indeterminada (Y10–Y34):** parte das agressões
  reais é codificada como intenção indeterminada → subestimação. Considere
  análise de sensibilidade incluindo Y10–Y34.

### 5.1. Completude da causa externa — resultado da medição

Medida via `--completude`: dentre as internações por lesão (CID principal S/T),
% com causa externa (V–Y) registrada nos campos secundários. UF derivada de
`SUBSTR(id_municipio_paciente, 1, 2)` (pois `sigla_uf` vem vazio — ver dicionário).

**Boa notícia:**
- Completude **nacional alta e estável**: 89–97% (a perda por subnotificação do
  campo é pequena).
- **Convergência entre UFs:** o desvio-padrão entre estados cai de ~7,5 p.p.
  (2009) para ~3–5 p.p. (2016+).

**Ressalva (a ameaça à identificação):** a variação **não é homogênea entre UFs**.
Comparando a média 2009–2014 vs 2017–2022:

| Pioraram | Δ p.p. | | Melhoraram | Δ p.p. |
|---|---|---|---|---|
| AL | −7,7 | | AM | +14,0 |
| PA | −7,0 | | RO | +8,4 |
| AP | −6,0 | | TO | +7,6 |
| MS | −4,6 | | ES | +4,2 |
| RJ | −4,2 | | RS | +2,3 |

> **Implicação:** num painel município×tempo, se o tratamento incide sobre
> estados onde o registro melhorou muito (AM, RO, TO), parte de um suposto
> "aumento de agressões" pode ser **melhora de codificação**, não violência real.
> Mitigação: efeito fixo de UF × tendência, ou incluir a completude como controle.

## 6. Arquivos

| Arquivo | Função |
|---|---|
| `scripts/main.py` | orquestrador (CLI): `inspect`/`extrair`/`completude`/`diagnostico`/`all` |
| `scripts/sih/` | pacote: `config`, `consultas`, `bq`, `pipeline` |
| `data/internacoes_agressao_munic_mes_ate17.csv` | saída final |
| `data/completude_causa_externa_uf_ano.csv` | diagnóstico de qualidade do registro |
| `docs/dicionario.md` | dicionário de colunas da `aihs_reduzidas` |
| `.env` | `BILLING_PROJECT_ID` (não versionado, na raiz) |

### Esquema da saída

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | int | ano da internação |
| `mes` | int | mês (1–12) |
| `id_municipio_residencia` | int | **código IBGE de 6 dígitos** (`id_municipio_paciente`), como no SIH |
| `internacoes_agressao` | int | nº de AIH com CID X85–Y09, ≤17 anos (0 onde não houve) |

**Painel balanceado por default.** A saída traz todos os municípios do diretório
IBGE × todos os meses do período (zeros preenchidos): 5.571 municípios × 168
meses = 935.928 linhas (2009–2022). Use `--no-balancear` para a versão esparsa
(só células com ≥1 internação).

> ⚠️ **Código de 6 dígitos:** o SIH usa o código de município de 6 dígitos
> (DataSUS), não o de 7 da IBGE. O balanceamento usa `id_municipio_6` do
> diretório. Para cruzar com bases de 7 dígitos (ex.: população), mapeie via
> `id_municipio_6` ↔ `id_municipio`.
>
> ⚠️ **~1,3% descartado:** ~1.071 internações (de 82.019) vêm com código de
> residência fora do diretório IBGE (ignorado/inválido) e são descartadas no
> balanceamento → total final 80.948.
