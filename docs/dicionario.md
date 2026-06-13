# Dicionário — `basedosdados.br_ms_sih.aihs_reduzidas`

Referência das colunas do SIH-RD (AIH reduzidas) no basedosdados, organizada por
tema. Baseado no esquema da tabela e na query de referência do basedosdados.
Marcações: ✅ usado neste projeto · ⚠️ armadilha confirmada (ver §Armadilhas).

## Como decodificar

Muitas colunas guardam **códigos**, não rótulos. Há três fontes de decode:

1. **Dicionário** `basedosdados.br_ms_sih.dicionario` (campos marcados "dic"):
   ```sql
   LEFT JOIN (
     SELECT chave, valor FROM `basedosdados.br_ms_sih.dicionario`
     WHERE id_tabela = 'aihs_reduzidas' AND nome_coluna = '<coluna>'
   ) d ON dados.<coluna> = d.chave
   ```
2. **Diretórios** `basedosdados.br_bd_diretorios_brasil.*` (municipio, cid_10,
   cbo_2002) — para nomes de município, descrições de CID e ocupações.
3. **Direto** — colunas numéricas/datas/strings já legíveis.

---

## Identificação e tempo

| Coluna | Tipo | Notas |
|---|---|---|
| `ano`, `mes` | INT | partição; competência da AIH ✅ |
| `id_aih` | STRING | identificador da AIH |
| `sequencial_aih` | — | sequencial |
| `tipo_aih` | dic | normal / continuação / longa permanência — útil p/ deduplicar |
| `motivo_autorizacao_aih` | dic | |
| `remessa` | — | lote de envio |

## Localização

| Coluna | Tipo | Notas |
|---|---|---|
| `sigla_uf` | INT64 | ⚠️ **vazio** no bd. Para UF, use `SUBSTR(id_municipio_*, 1, 2)` |
| `id_municipio_estabelecimento` | STRING | município do hospital (+ diretório `municipio`) |
| `id_municipio_gestor` | STRING | município gestor |
| `id_municipio_paciente` | STRING | **residência** do paciente (IBGE 7 díg.) ✅ |
| `cep_paciente` | — | CEP |

## Internação (clínico-administrativo)

| Coluna | Tipo | Notas |
|---|---|---|
| `data_internacao`, `data_saida` | DATE | datas do episódio |
| `carater_internacao` | dic | eletivo / urgência |
| `especialidade_leito` | dic | |
| `motivo_saida` | dic | inclui alta, óbito, transferência |
| `tipo_uti`, `tipo_uci` | dic | |
| `complexidade` | dic | |
| `indicador_infeccao_hospitalar` | dic | |
| `indicador_obito` | — | óbito na internação (0/1) |
| `quantidade_dias`, `quantidade_dias_permanencia` | INT | duração |
| `quantidade_dias_uti_mes`, `quantidade_dias_unidade_intermediaria`, `quantidade_dias_acompanhate` | INT | |
| `procedimento_solicitado`, `procedimento_realizado` | dic | SIGTAP |
| `sequencial_longa_permanencia` | — | |

## Estabelecimento

| Coluna | Tipo | Notas |
|---|---|---|
| `id_estabelecimento_cnes` | STRING | CNES |
| `natureza_juridica_estabelecimento` | dic | + variante `_ate_2012` (quebra metodológica) |
| `tipo_gestao_estabelecimento` | dic | |
| `cnpj_estabelecimento`, `cnpj_mantenedora` | — | |
| `tipo_gestor`, `cpf_gestor`, `data_autorizacao_gestor` | — | |

## Paciente (sociodemográfico)

| Coluna | Tipo | Notas |
|---|---|---|
| `data_nascimento_paciente` | DATE | |
| `idade_paciente` | INT | ✅ **só faz sentido com a unidade** abaixo |
| `unidade_medida_idade_paciente` | dic | ⚠️ anos/meses/dias/horas — ver §Armadilhas |
| `sexo_paciente` | dic | |
| `raca_cor_paciente`, `etnia_paciente` | dic | |
| `codigo_nacionalidade_paciente` | — | |
| `cbo_2002_paciente` | dir cbo | ocupação |
| `grau_instrucao_paciente` | dic | |
| `indicador_vinculo_previdencia` | dic | |
| `indicador_paciente_homonimo` | — | |
| `quantidade_filhos_paciente` | INT | |

## Gestação / saúde reprodutiva / trabalho

| Coluna | Tipo | Notas |
|---|---|---|
| `id_gestante_pre_natal` | — | |
| `indicador_gestante_risco` | dic | |
| `tipo_contraceptivo_principal`, `tipo_contraceptivo_secundario` | dic | |
| `indicador_exame_vdrl` | — | |
| `id_acidente_trabalho` | — | |

## CID / Diagnósticos — núcleo do projeto

Cada CID vem **dividido** em `categoria` (3 chars, ex.: `X85`) e `subcategoria`
(4 chars, ex.: `X850`), decodificável pelo diretório `cid_10`.
⚠️ **Use `subcategoria`** — as colunas `categoria` são mal preenchidas.

| Coluna(s) | Papel | Notas |
|---|---|---|
| `cid_principal_categoria/subcategoria` | diagnóstico principal | em internação por agressão = a **lesão** (S/T), não o X85–Y09 |
| `cid_causa_categoria/subcategoria` | **causa externa** | ⚠️ só preenchido **até 2014**; inútil depois |
| `cid_secundario_subcategoria` | diag. secundário (campo único `DIAG_SECUN`) | ✅ carrega a agressão **até 2014** |
| `cid_diagnostico_secundario_1..9_categoria/subcategoria` | diags. secundários (`DIAGSEC1-9`) | ✅ carregam a agressão **2015+** (usar subcategoria) |
| `tipo_diagnostico_secundario_1..9` | — | tipo de cada diag. secundário |
| `cid_notificacao_categoria/subcategoria` | CID de notificação | |
| `cid_morte_categoria/subcategoria` | CID de óbito | só se houve óbito |

> **Captura da agressão (X85–Y09) neste projeto:** união de
> `cid_secundario_subcategoria` + os 9 `cid_diagnostico_secundario_N_subcategoria`,
> testando `SUBSTR(col,1,3) BETWEEN 'X85' AND 'Y09'`.

## Financeiro

| Coluna | Notas |
|---|---|
| `valor_aih` | valor total da AIH |
| `valor_serivico_hospitalar` | ⚠️ **typo na coluna** ("serivico"); serviços hospitalares |
| `valor_servico_profissional`, `valor_uti`, `valor_uci` | componentes |
| `valor_complemento_federal_servicos_{hospitalares,profissionais}` | complementos federais |
| `valor_complemento_gestor_servicos_{hospitalares,profissionais}` | complementos do gestor |
| `valor_dolar` | valor em dólar |
| `tipo_financiamento`, `subtipo_financiamento`, `regra_contratual` | |

## Auditoria

| Coluna | Notas |
|---|---|
| `justificativa_auditor`, `justificativa_estabelecimento` | texto livre |

---

## Armadilhas confirmadas

1. **`sigla_uf` é INT64 e está vazio.** Derive a UF de
   `SUBSTR(id_municipio_paciente, 1, 2)` (código IBGE da UF).
2. **Colunas `categoria` (3 chars) são mal preenchidas.** Ex.: `cid_causa_categoria`
   tinha ~18 mil preenchidos vs ~91 mil em `cid_causa_subcategoria`. **Use `subcategoria`.**
3. **`cid_causa_*` (causa externa) só é preenchido até 2014.** A partir de 2015,
   a causa externa migra para os diagnósticos secundários `DIAGSEC1-9`.
4. **Diagnóstico secundário mudou de estrutura em 2015:** campo único
   (`cid_secundario_subcategoria`) → nove campos (`cid_diagnostico_secundario_1..9`).
   Quem ignora isso perde 2015+ inteiro (foi o bug original — ver `documentacao.md` §4).
5. **`idade_paciente` exige a unidade.** Sem ela, "11" pode ser 11 anos, meses ou
   dias. Resolva pelo dicionário de `unidade_medida_idade_paciente`.
6. **2008 vem vazio** no basedosdados; cobertura efetiva 2009+.
