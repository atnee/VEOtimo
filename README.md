# VEOtimo

Framework reprodutível para planejamento integrado de eletropostos urbanos. A
cidade, as redes e todos os parâmetros técnicos são **entradas**: o núcleo não
contém hipóteses específicas de uma localidade.

> Estado atual: **Etapa 1 — arquitetura, contrato de dados e configuração**.
> Nenhum resultado de localização é chamado de ótimo nesta etapa. Os arquivos de
> exemplo são explicitamente sintéticos.

## Visão geral

O problema é tratado como a integração de mobilidade, rede viária, demanda de
recarga, rede de distribuição, transformadores, filas e otimização. A arquitetura
prevê um *outer loop* (MILP/GA/PSO/GWO/NSGA-II) e uma avaliação padronizada no
*inner loop*:

```text
caso -> importação -> mobilidade -> demanda VE -> candidatos
     -> candidato/barra/transformador -> solução candidata
     -> filas + fluxo de potência + custos + restrições -> objetivos
     -> validação AC -> indicadores, mapas e tabelas
```

A especificação científica completa, equações, dados requeridos, tabelas,
restrições e roteiro incremental estão em [`docs/metodologia.md`](docs/metodologia.md).
O dicionário de dados está em [`docs/dicionario_dados.md`](docs/dicionario_dados.md).

## Estrutura

```text
config/                 configurações versionadas de casos e algoritmos
data/{raw,processed}/   dados de entrada e dados padronizados
data/networks/          grafos e modelos elétricos
results/{figures,maps}/ artefatos por run_id (ignorados pelo Git)
src/veotimo/            código reutilizável
tests/                  testes automatizados
main.py                 entrada de linha de comando
```

Os futuros módulos `road`, `mobility`, `electrical`, `queueing`, `optimization`,
`powerflow`, `scenarios`, `visualization` e `export` se comunicam somente por
modelos tipados. Solvers e motores de fluxo implementarão interfaces estáveis
`solve(problem, config)` e `run_power_flow(network, scenario)`.

## Início rápido

Requer Python 3.11 ou posterior.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py validate --config config.yaml
python main.py powerflow --network data/networks/ieee33.json
python main.py optimize --algorithm exhaustive
python main.py optimize --algorithm ga --seed 42
pytest
```

`validate` verifica o contrato mínimo, imprime o nível de modelagem e cria um
`run_id`; não executa ainda otimização ou fluxo de potência. Copie `config.yaml`,
altere `study` e os caminhos em `inputs`, sem modificar código.

## Benchmark IEEE 33 barras

O repositório inclui o alimentador radial IEEE 33 barras (3,715 MW e 2,300
MVAr), com os 32 ramos normalmente fechados e as chaves de interligação abertas
omitidas de forma documentada. O comando `powerflow` executa uma varredura AC
*backward/forward* de carga PQ constante, sem dependências científicas externas.
O caso base é verificado automaticamente contra os valores de referência de
tensão mínima e perdas. Este motor leve serve ao teste reprodutível; o fluxo AC
pandapower continuará sendo a validação prevista para redes reais.

### Notebook científico

O notebook [`notebooks/ieee33_analise_cientifica.ipynb`](notebooks/ieee33_analise_cientifica.ipynb)
executa uma análise reproduzível do benchmark e exporta figuras em 300 dpi e
tabelas CSV. Ele inclui desenho esquemático da topologia, perfil e distribuição
de tensão, perdas por ramo, cenários locacionais de recarga, curva de estresse,
capacidade de hospedagem e painel multicritério elétrico.

```bash
jupyter lab notebooks/ieee33_analise_cientifica.ipynb
```

O notebook diferencia explicitamente diagnóstico elétrico de localização ótima
urbana e encerra com limitações e experimentos necessários para um artigo A1.

## Otimização elétrica inicial

O benchmark sintético implementa a interface comum `solve(problem, config)` com
dois métodos: enumeração exata (referência global para a instância pequena) e um
algoritmo genético inteiro reprodutível. Cada vetor define o número de carregadores
em cinco barras candidatas. A avaliação distribui a demanda agregada, executa
fluxo AC, monetiza CAPEX e perdas incrementais e penaliza demanda não atendida e
violações de tensão. O GA é comparado automaticamente ao ótimo exato nos testes.

Os candidatos, demanda, custos, simultaneidade e limites do arquivo
`data/processed/ieee33_optimization_case.json` são **sintéticos**. Portanto, o
resultado valida o pipeline computacional, mas não representa uma cidade nem
substitui a futura otimização integrada com rede viária, OD, filas e séries
temporais.

## Reprodutibilidade e proveniência

* toda execução recebe `run_id` UTC e registra configuração, semente e versões;
* cada campo importado deve carregar `source_kind`: `measured`, `estimated` ou
  `synthetic`;
* estimativas exigem método e fonte/referência; nunca são rotuladas como medidas;
* unidades internas seguem o dicionário de dados e distâncias operacionais usam
  caminho viário, salvo aproximação declarada;
* artefatos de cada cenário serão gravados em `results/<run_id>/`.

## Licença

Consulte [LICENSE](LICENSE).
