import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import random


def generateColors(array):
    hex_colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
    '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
    '#5254a3', '#6b6ecf', '#9c9ede', '#637939', '#8c6d31',
    '#bd9e39', '#8c6d31', '#e7ba52', '#843c39', '#ad494a',
    '#d6616b', '#ff7f0e', '#fdbf6f', '#cab2d6', '#6a3d9a',
    '#b5cf6b', '#8c6d31', '#c49c94', '#d6616b', '#9c9ede',
    '#9467bd', '#7b4173', '#5254a3', '#393b79', '#637939'
]

    colors = {}

    for element in array:
        index = random.randint(0, len(hex_colors))
        selectedColor = hex_colors[index]
        colors[element] = selectedColor
        hex_colors.pop(index)

    return colors


def writeColumns(object, *args):
    columns = st.columns(len(args))
    if object == 'dataframe':
        for i in range(len(columns)):
            with columns[i]:
                st.write(args[i][0])
                st.dataframe(data=pd.DataFrame(args[i][1], columns=['Quantity', 'Percentage']), hide_index=True)

    elif object == 'metric':
        for i in range(len(columns)):
            with columns[i]:
                st.metric(label=args[i]['label'], value=args[i]['value'])

    elif object == 'slider':
        sliderObj = {}
        for i in range(len(columns)):
            with columns[i]:
                sliderObj[i] = st.slider(label=args[i], min_value=-100, max_value=100, value=0)
        return list(sliderObj.values())


def defineQuadrant(x,y):
    if x >= 0 and y >= 0:
        return 'Q1'
    elif x < 0 and y >= 0:
        return 'Q2'
    elif x < 0 and y < 0:
        return 'Q3'
    else:
        return 'Q4'


def plotBacklog(backlog, quadrant, color):
    cols = st.columns([0.05, 0.9, 0.05])

    with cols[1]:
        st.markdown("<h4 style='text-align: center;'>Análise do Backlog</h4>", unsafe_allow_html=True)

        chartCols = st.columns(2)
        with chartCols[0]:
            colorColumn = st.selectbox("Escolha a coluna que vai definir a cor",
                                       options=["Quadrante", "Tipo de voo", "Tipo de Viagem", "Rota"])
        with chartCols[1]:
            hoverColumn = st.selectbox("Escolha a coluna que vai definir o nome de cada ponto",
                                       options=["Pedido", "Operação", "Tipo de voo", "Tipo de Viagem", "Rota"])

        mapper = {"Quadrante": 'quadrant', "Tipo de voo": 'flight_class',
                  "Tipo de Viagem": 'travel_type', "Pedido": 'OrderID', "Operação": 'OperationID',
                  "Rota": "FlightRoute"}

        try:
            colormap = {k: v for k, v in zip(quadrant, color)} if colorColumn == "Quadrante" else generateColors(
                np.unique(backlog[mapper[colorColumn]].values))
            fig = px.scatter(backlog, x='xscore', y='yscore', color=mapper[colorColumn], hover_name=mapper[hoverColumn],
                             color_discrete_map=colormap,
                             width=1000, height=500)

            st.plotly_chart(fig)

        except IndexError:

            st.markdown(
                "<h3 style='text-align:center;'>Selecione no máximo 50 rotas para poder usar elas para as cores</h3>",
                unsafe_allow_html=True)


@st.cache_data
def getBacklog(path):
    return pd.read_csv(path)


def defineScores(path, slidersArray, sliders):
    backlog = getBacklog(path)

    data = backlog[['IsSafraAcquirer', 'NoiseIndex', 'ExponentialDaysUntilExpiration', 'TotalExpiredOffers',
                    'TotalRefusedOffers', 'OrderByJR', 'LogarithmicTimesRouted', 'OrderPR']]

    xscores = np.matmul(slidersArray, data.values.transpose())
    yscores = sliders['H10'] * backlog['Margin'].values

    quadrantFunction = np.vectorize(defineQuadrant)
    quadrant = quadrantFunction(xscores, yscores)
    color = np.where(quadrant == 'Q1', 'green',
                     np.where(quadrant == 'Q2', 'yellow', np.where(quadrant == 'Q3', 'red', 'orange')))

    backlog['xscore'] = xscores
    backlog['yscore'] = yscores
    backlog['score'] = np.sqrt(np.square(xscores) + np.square(yscores))
    backlog['quadrant'] = quadrant

    return backlog, quadrant, color

def main():

    st.set_page_config(page_title="OPV 2.0", layout="wide")

    st.header("Bem vindo ao nosso ambiente de análise do Backlog")
    st.write("Aqui você pode checar todas as informações sobre a nossa fila de operação e escolher quais pedidos devem ser priorizados")

    indexesLabels = ["Adquirente SafraPay",
                     "Índice de Barulho",
                     "Proximidade da Validade",
                     "Já enviamos voo - Não respondeu ao contato",
                     "Já enviamos voo - Recusou Explicitamente",
                     "Solicitações Especiais",
                     "Pedidos Roteados",
                     "Pedidos em PR",
                     "Margem de Contribuição"]

    sliders = {}

    st.write("#### **Defina os pesos para a prioridade**")
    for i in range(0, len(indexesLabels)-1, 3):
        if i < 6:
            sliders[f'H{i+1}'], sliders[f'H{i+2}'], sliders[f'H{i+3}'] = writeColumns('slider', indexesLabels[i], indexesLabels[i + 1], indexesLabels[i + 2])
        else:
            sliders[f'H{i + 1}'], sliders[f'H{i + 2}'] = writeColumns('slider', indexesLabels[i], indexesLabels[i + 1])

    # st.write("#### **Defina o peso para a margem**")
    # sliders['H10'] = writeColumns('slider', "Margem de Contribuição")
    sliders['H10'] = 1

    slidersArray = np.array([sliders['H1'], sliders['H2'], sliders['H3'], -1 * sliders['H4'], -1 * sliders['H5'], sliders['H6'],
                             sliders['H7'], sliders['H8']])

    backlog, quadrant, color = defineScores('Query2_OPV20.csv', slidersArray, sliders)

    st.write("#### **Área de análise do Backlog**")
    st.write("Estes filtros são opcionais, servindo apenas para ajudar a dar uma visão mais detalhada do Backlog caso necessário")

    st.write("**Escolha das cidades**")
    columns = st.columns(3)
    with columns[0]:
        route = st.multiselect(label="Defina as possíveis rotas", options=np.unique(backlog['FlightRoute'].values.astype('str')))
    with columns[1]:
        flightClass = st.multiselect(label="Defina os tipos de voos", options=np.unique(backlog['flight_class'].values.astype('str')))
    with columns[2]:
        travelType = st.multiselect(label="Defina o tipo de viagem", options=np.unique(backlog['travel_type'].values.astype('str')))

    monthNames = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    months = st.multiselect(label="**Escolha os meses de viagem**", options=monthNames)
    monthsNumbers = list(map(lambda x: monthNames.index(x) + 1, months))

    st.write("")
    st.write("**Margens desejadas**")
    st.write("Escolha o valor mínimo ou máximo do percentual de margem que deseja observar")
    leftCol, rightCol = st.columns([1, 3])

    with leftCol:
        overUnder = st.selectbox(label="Escolha a margem", options=["Acima de", "Abaixo de"], label_visibility='hidden')

    with rightCol:
        margins_slider = st.slider(label="Select", min_value=-200, max_value=200, step=1, label_visibility="hidden")


    if len(route) > 0:
        backlog = backlog[(backlog['FlightRoute'].isin(route))]
    if len(flightClass) > 0:
        backlog = backlog[(backlog['flight_class'].isin(flightClass))]
    if len(travelType) > 0:
        backlog = backlog[(backlog['travel_type'].isin(travelType))]
    if len(months) > 0:
        backlog = backlog[(backlog['TravelMonth'].isin(monthsNumbers))]
    if margins_slider and overUnder:
        backlog = backlog[(backlog['Margin'] > (margins_slider / 100) if overUnder == "Acima de" else backlog['Margin'] < (margins_slider / 100))]

    st.write('')
    st.write('')

    plotBacklog(backlog, quadrant, color)

    st.write('')
    st.write('')
    st.write('')
    st.write('')

    st.write("#### **Lista de pedidos**")
    st.write("Confira a lista dos pedidos filtrados")
    st.dataframe(backlog, hide_index=True)

main()
