sistema_de_qualidade_do_ar
Sistema web desenvolvido em Streamlit para análise da qualidade do ar em pontos de coleta georreferenciados, com foco em:
leitura e tratamento de dados ambientais;
classificação técnica de variáveis;
visualização analítica em tabela, gráficos e mapa;
exportação de relatório em PDF com gráficos e mapa.
O projeto foi estruturado para ficar mais estável em ambiente local e em deploy, evitando dependências desnecessárias e separando melhor as responsabilidades do sistema.
---
Objetivo do sistema
O sistema foi criado para apoiar a análise de medições ambientais realizadas em diferentes pontos de coleta, permitindo ao usuário:
selecionar um dia específico de análise;
filtrar os pontos de coleta desejados;
refinar a análise por horário;
escolher a variável principal para análise estatística;
comparar os valores observados com referências técnicas internas e externas;
visualizar os pontos em mapa;
gerar um relatório consolidado em PDF.
---
Funcionalidades principais
1. Filtros analíticos
O sistema permite filtrar os dados por:
data
ponto de coleta
horário
variável de análise estatística
2. Classificação técnica automática
As variáveis são classificadas automaticamente com base em regras definidas no sistema:
Temperatura
Umidade Relativa
CO₂
Essas classificações ajudam a transformar os dados brutos em leitura técnica mais clara.
3. Tabela de coletas filtradas
Após aplicação dos filtros, o sistema exibe uma tabela com:
ponto
data/hora
temperatura
classificação da temperatura
umidade relativa
classificação da umidade
CO₂
classificação de CO₂
ponto de orvalho
4. Gráficos comparativos
O painel gera gráficos analíticos para apoiar a interpretação dos dados:
indicadores estatísticos por ponto;
comparação de CO₂ por ponto;
temperatura média vs referências;
umidade média vs referências;
CO₂ médio vs referências.
5. Mapa dos pontos de coleta
Os pontos são exibidos em mapa com coordenadas fixas por latitude/longitude, com pin customizado e popup analítico.
6. Exportação de relatório PDF
O sistema gera um relatório com:
referências utilizadas;
gráficos comparativos;
mapa dos pontos de coleta;
caixas-resumo com os dados de cada ponto no mapa exportado.
---
Fluxo do sistema
O fluxo de funcionamento do sistema é o seguinte:
Etapa 1 — Carregamento
O sistema lê a base Excel localizada na pasta `data/`.
Etapa 2 — Validação
As colunas obrigatórias são verificadas para garantir que a estrutura da base esteja correta.
Etapa 3 — Tratamento
São realizados:
normalização dos nomes de colunas;
conversão de data e hora;
conversão de colunas numéricas;
criação das classificações automáticas.
Etapa 4 — Filtros
O usuário aplica os filtros desejados pela sidebar.
Etapa 5 — Visualização
O sistema renderiza:
tabela filtrada;
tabela de referências;
gráficos estatísticos;
mapa dos pontos.
Etapa 6 — Exportação
Ao solicitar o PDF, o sistema:
exporta os gráficos para imagem;
gera o mapa estático com base cartográfica;
compõe o relatório final em PDF.
---
Arquitetura do projeto
A aplicação foi organizada em módulos para facilitar manutenção, evolução e debug.
```text
sistema_de_qualidade_do_ar/
├── app.py
├── settings.py
├── data_loader.py
├── rules.py
├── charts.py
├── map_view.py
├── map_export.py
├── report.py
├── ui.py
├── requirements.txt
├── README.md
├── assets/
│   └── icone_ponto.png
└── data/
    └── Base de dados.xlsx
```
---
Papel de cada arquivo
`app.py`
Arquivo principal da aplicação.
Responsável por:
carregar os dados;
chamar os filtros;
renderizar tabela, gráficos e mapa;
acionar a exportação do PDF.
`settings.py`
Arquivo central de configuração.
Contém:
caminhos de arquivos;
título da aplicação;
coordenadas dos pontos de coleta;
referências internas.
`data_loader.py`
Responsável por:
ler o Excel;
validar colunas obrigatórias;
tratar datas e horas;
converter campos numéricos;
aplicar as classificações;
filtrar os dados.
`rules.py`
Contém as regras de negócio para:
classificar temperatura;
classificar umidade;
classificar CO₂;
aplicar cores às classificações.
`charts.py`
Responsável por montar:
tabela de referências;
gráficos estatísticos;
gráficos comparativos.
`map_view.py`
Renderiza o mapa no painel web com os pontos de coleta selecionados.
`map_export.py`
Gera a versão estática do mapa para o PDF, incluindo:
tiles de mapa base;
pontos de coleta;
pin customizado;
caixas com resumo dos dados.
`report.py`
Gera o relatório em PDF a partir de:
gráficos exportados como imagem;
tabela de referências;
mapa exportado.
`ui.py`
Controla os componentes da sidebar:
filtros;
referências;
parâmetros comparativos.
---
Requisitos do sistema
Principais bibliotecas utilizadas:
`streamlit`
`pandas`
`folium`
`plotly`
`numpy`
`openpyxl`
`kaleido`
`reportlab`
`requests`
`pillow`
---
Instalação
1. Clonar o projeto
```bash
git clone <url-do-repositorio>
cd sistema_de_qualidade_do_ar
```
2. Criar ambiente virtual
```bash
python -m venv .venv
```
3. Ativar ambiente virtual
Windows PowerShell
```bash
.venv\Scripts\Activate.ps1
```
Windows CMD
```bash
.venv\Scripts\activate.bat
```
4. Instalar dependências
```bash
pip install -r requirements.txt
```
---
Execução
Para rodar o sistema localmente:
```bash
streamlit run app.py
```
Depois disso, o Streamlit abrirá no navegador com a URL local padrão.
---
Estrutura esperada dos dados
O arquivo Excel deve conter, no mínimo, as seguintes colunas:
`Data-Hora`
`(Horário Padrão do Brasil)`
`pontos`
`Temperatura (°C)`
`RH (%)`
`CO2 (ppm)`
`Ponto de Orvalho (°C)`
Essas colunas são validadas no carregamento. Se alguma estiver ausente, o sistema interrompe a execução e informa o erro.
---
Configuração dos pontos de coleta
As coordenadas dos pontos são definidas manualmente no arquivo `settings.py`, no dicionário `POINTS_COORDS`.
Exemplo:
```python
POINTS_COORDS = {
    "Ponto 1": {"lat": -15.77512, "lon": -47.98996},
    "Ponto 2": {"lat": -15.77394, "lon": -47.98632},
    "Ponto 3": {"lat": -15.78031, "lon": -47.98043},
    "Ponto 4": {"lat": -15.77639, "lon": -47.99554},
}
```
---
Como o PDF é gerado
Quando o usuário clica em Gerar PDF com Tabela, Gráficos e Mapa, o sistema executa este fluxo:
exporta os gráficos Plotly para PNG;
gera uma imagem estática do mapa com base cartográfica;
desenha os pontos e suas caixas-resumo;
monta o PDF final;
libera o arquivo para download.
---
Vantagens da arquitetura atual
A versão atual do projeto traz algumas melhorias importantes:
separação clara de responsabilidades;
menos acoplamento no `app.py`;
retirada de dependências mais frágeis do fluxo principal;
uso de coordenadas fixas no lugar de shapefile;
geração de PDF mais previsível;
melhor compatibilidade com deploy.
---
Possíveis melhorias futuras
Alguns próximos passos possíveis para evolução do sistema:
melhorar o layout visual do painel;
acrescentar indicadores-resumo em cards;
permitir upload de arquivo diretamente pela interface;
adicionar exportação em outros formatos;
melhorar ainda mais o layout do PDF;
adicionar logo institucional no relatório;
permitir seleção dinâmica de mais pontos de coleta;
incluir cache mais refinado para otimizar desempenho.
---
Observações finais
Este projeto foi estruturado para oferecer uma análise ambiental clara, visual e técnica, com foco em estabilidade, manutenção e facilidade de uso.
Ele pode ser adaptado para outros contextos semelhantes, desde que:
a base de dados siga a estrutura esperada;
os pontos de coleta sejam configurados no `settings.py`;
as regras de classificação sejam ajustadas conforme a necessidade do estudo.
---