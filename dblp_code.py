import streamlit as st
from PIL import Image
import base64
import pandas as pd
import math
import itertools
import numpy as np
import xml.etree.ElementTree as et
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt

#Standalone
#Page expands to full width
st.set_page_config(layout="wide")
#Add logo
LOGO_IMAGE = "CSminer.jpg"

st.markdown(
    """
    <style>
    .container {
        display: flex;
    }
    .logo-text {
        font-weight:700 !important;
        font-size:50px !important;
        padding-top: 75px !important;
    }
    .logo-img {
        float:right;
	width: 270px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="container">
        <img class="logo-img" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
        
    </div>
    """,
    unsafe_allow_html=True
)
st.title(""" Who are CS miner""")
st.subheader("Is a software that help all researcher or who are interset in computer science field to find career path and co-author relationships for a specific author or find top ten journals.")

col1 = st.sidebar
col2, col3 = st.columns((2,1))

#Sidebar + Main panel
col1.header(" Select an Option")

#Radio button
button =st.sidebar.radio("",["Career Path","Co-author","Top Ten Journal"])

Co_author_flag= False
if button =="Co-author":
    if Co_author_flag==0:
	 #Read Files
         publication_df=pd.read_pickle("./publication_df.pkl")
	 #List of authors name
         col_one_list = publication_df["Authors"].tolist()
         coauthor_df=pd.read_pickle("./coauthor_df.pkl")
         Co_author_flag = True
    #get input from user
    name = st.selectbox("""Select Author Name""", col_one_list)

    #Check if the entered author in Author1 column or Author2 column for the visualization
    coauthor_list1 = coauthor_df[(coauthor_df['Author1'] == name)].Author2.values.tolist()
    common_list1 = coauthor_df[(coauthor_df['Author1'] == name)].Common.values.tolist()
    coauthor_list2 = coauthor_df[(coauthor_df['Author2'] == name)].Author1.values.tolist()
    common_list2= coauthor_df[(coauthor_df['Author2'] == name)].Common.values.tolist()

    coauthor_list = coauthor_list1+ coauthor_list2
    common_list = common_list1+ common_list2
    coauthor_list.insert(0,name)
    common_list.insert(0,100)

    #non-interactive visualization
    G=nx.Graph()
    fig = plt.figure(figsize = (30, 20))
    plt.margins(0.3)
    plt.title(name+' Co-author\'s', fontsize=18)
    common_list_count=0
    for i in range(len(coauthor_list)):
        G.add_edge(coauthor_list[i],name, weight=common_list[common_list_count])
        common_list_count+=1
    pos=nx.spring_layout(G)
    limits = plt.axis("off")  
    colors=['#F16A70' for i in range(len(coauthor_list)-1)]
    colors.insert(0,'lightskyblue')
    nx.draw_networkx(G,pos,with_labels=True,node_size=[i * 30 for i in common_list], node_color=colors,linewidths=1.97,width=1,font_size=12)
    nx.draw_networkx_edge_labels(G,pos,edge_labels=nx.get_edge_attributes(G,'weight'))
    st.pyplot(fig)

Career_flag=False   
if button =="Career Path":
    if Career_flag==False:
	 #Read Files
         publication_df=pd.read_pickle("./publication_df.pkl")
	 #List of authors name
         col_one_list = publication_df["Authors"].tolist()
         Career_flag = True
	 
    #get input from user
    author_name = st.selectbox("""Select Author Name""", col_one_list)

    #Get all index in publication_df
    index = publication_df.index
    #Find index for input author
    author_index = index[publication_df["Authors"] == author_name]

    #Return data for each type for the input author
    article_data=publication_df.iloc[author_index[0]]['Articles']
    book_data=publication_df.iloc[author_index[0]]['Books']
    conference_data=publication_df.iloc[author_index[0]]['Conferenece']
    collections_data=publication_df.iloc[author_index[0]]['Collections']
    Informal_and_Others_data=publication_df.iloc[author_index[0]]['Informal and Others']
    
    #Visualize the career path of the input author
    fig1 = go.Figure(go.Bar(x=list(article_data.keys()), y=list(article_data.values()), marker_color='#B24F73',name='Articles',width=0.6))
    fig1.add_trace(go.Bar(x=list(book_data.keys()), y=list(book_data.values()),marker_color='#90A7C5', name='Books',width=0.6))
    fig1.add_trace(go.Bar(x=list(conference_data.keys()), y=list(conference_data.values()),marker_color='#C3E0D0', name='Conferences',width=0.6))
    fig1.add_trace(go.Bar(x=list(collections_data.keys()), y=list(collections_data.values()),marker_color='#9999CC', name='Collections',width=0.6))
    fig1.add_trace(go.Bar(x=list(Informal_and_Others_data.keys()), y=list(Informal_and_Others_data.values()),marker_color='silver', name='Informal and Other Publications',width=0.6))

    fig1.update_layout(barmode='stack',  title="%s's Career Path"%(author_name),
        title_x=0.5,
        font_family="sans-serif",
        font_size=14,
        font_color="black",
        yaxis=dict(
        title='Number Of Publication',
        titlefont_size=14,
        tickfont_size=14,),
        xaxis=dict(
        titlefont_size=16,
        tickfont_size=14,
        categoryorder='category ascending'))
    st.plotly_chart(fig1, use_container_width=True)

    #Second visualize
    visualise = publication_df.iloc[author_index[0]]['Top Journals']
    if None in visualise.keys():
    	visualise.pop(None)

    data_items = visualise.items()
    data_list = list(data_items)
    df = pd.DataFrame(data_list)
    df.columns = ['Journal Name', 'Number of publication']

    titles = "%s's Top Journals"%(author_name)
    colors=["#9999CC", "#C3E0D0", "#90A7C5", "#B24F73", "silver"]
    fig2 = px.pie(df,names='Journal Name', values='Number of publication', title= titles)
    fig2.update_layout(
        title=titles,
        title_x=0.5,
        font_family="arial",
        font_size=16,
        font_color="black",
        titlefont_size=24,
        title_font_family="arial",
        title_font_color="black")
    fig2.update_traces(marker=dict(colors=colors))
    st.plotly_chart(fig2, use_container_width=True)


Top_flag=False
if button =="Top Ten Journal":
    if Top_flag==False:
	   #Read Files
           top_10=pd.read_pickle("./top_10.pkl")
           Top_flag=True

    #Visualize top ten journals
    information=['Name: IEEE Access'+'<br>Impact Factor: 4.48'+'<br>Quartile: <br>Computer Science (miscellaneous) (Q1); <br>Engineering (miscellaneous) (Q1); <br>Materials Science (miscellaneous) (Q2)',
                'Name: Sensors'+'<br>Impact Factor: 4.35'+'<br>Quartile: <br>Analytical Chemistry (Q2); <br>Atomic and Molecular Physics, and Optics (Q2); <br>Electrical and Electronic Engineering (Q2); <br>Information Systems (Q2); <br>Instrumentation (Q2); <br>Medicine (miscellaneous) (Q2); <br>Biochemistry (Q3).',
                'Name: Remote Sensing '+'<br>Impact Factor: 5.33'+'<br>Quartile: <br>Earth and Planetary Sciences (miscellaneous) (Q1)',
                'Name: Neurocomputing'+'<br>Impact Factor: 5.719'+'<br>Quartile: <br>Artificial Intelligence (Q1); <br>Computer Science Applications (Q1); <br>Cognitive Neuroscience (Q2)',
                'Name: Multimedia Tools And Applications Ranking'+'<br>Impact Factor: 2.757'+'<br>Quartile: <br>Media Technology (Q1); <br>Computer Networks and Communications (Q2); <br>Hardware and Architecture (Q2); <br>Software (Q2)',
                'Name: NeuroImage'+'<br>Impact Factor: 6.82'+'<br>Quartile: <br>Neuroscience (Q1); <br>Neurology (Q1);',
                'Name: Applied Mathematics and Computation'+'<br>Impact Factor: 4.31'+'<br>Quartile: <br>Applied Mathematics (Q1); <br>Computational Mathematics (Q1)',
                'Name: IEEE Transactions on Industrial Electronics'+'<br>Impact Factor: 9.59'+'<br>Quartile: <br>Computer Science Applications (Q1); <br>Control and Systems Engineering (Q1); <br>Electrical and Electronic Engineering (Q1)',
                'Name: Expert Systems with Applications'+'<br>Impact Factor: 6.954'+'<br>Quartile: <br>Artificial Intelligence (Q1); <br>Computer Science Applications (Q1); <br>Engineering (miscellaneous) (Q1);',
                'Name: IEEE Transactions on Vehicular Technology'+'<br>Impact Factor: 7.8'+'<br>Quartile: <br>Aerospace Engineering (Q1); <br>Applied Mathematics (Q1); <br>Automotive Engineering (Q1); <br>Computer Networks and Communications (Q1); <br>Electrical and Electronic Engineering (Q1)']

    fig = go.Figure(data=[go.Scatter(
            x=top_10.values,
            y=[1,3,5,1,3,5,1,3,5,1],
            text=information,
            mode='markers',
            marker=dict(
            #Impact factor 
	    color=['LightBlue', 'LightSteelBlue', 'LightSkyBlue', 'DodgerBlue', 'lightgray', 'CornflowerBlue', 'silver', 'Navy','Blue','MediumBlue'],
            #color=['Navy','MediumBlue','Blue','CornflowerBlue','DodgerBlue', 'LightSkyBlue','LightBlue', 'LightSteelBlue','silver','lightgray'],
            size=top_10.values/300))])


    fig.update_layout(
            title='Top Ten Journals',
            title_x=0.5,
            font_family="sans-serif",
            font_size=14,
            font_color="black",
            xaxis=dict(
            title='Number of Publication',),
            yaxis=dict(visible= False,))
    st.plotly_chart(fig, use_container_width=True)
