import streamlit as st
from PIL import Image
import pandas as pd
import math
import itertools
import numpy as np
import xml.etree.ElementTree as et
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import fpcommon as fpc

#read dblp dataset
xtree = et.parse("subset1000(withSymbol).xml")
xroot = xtree.getroot()
#Publications less than 30 authors
rows = []
#Publications with missing authors
missing_rows = []
#Publications with more than 30 authors
more_30_rows =[]

authors={}
book={}
article={}
proceedings={}
others={}

for node in xroot:
    #Name of journal
    if node.find("journal") is not None:
        journal_name=node.find("journal").text 
    #Type of the publication                       
    pub_type= node.tag 
    #Title of the publication
    if node.find("title") is not None:
        title = node.find("title").text 
    #Year of the publication
    if node.find("year") is not None:
        year = node.find("year").text
        
    info = {"Journal_Name" : journal_name ,"Type" :pub_type , "Title" :title , "Year" : year}  
    
    num_of_authors = len(node.findall("author")) 
    #Fill three list rows, missing_rows, more_30_rows
    if(num_of_authors == 0):
        missing_rows.append(info)  
    else:
        author_list=[]
        for x in node.findall("author")[:29]:
            name = x.text
            author_list.append(name)
            if name in authors:
                authors[name]+=1
            else:
                authors[name]=1
        
            #Initilaze  
            if name not in article:
                article[name]={year:0}
                book[name]={year:0}
                proceedings[name]={year:0}
                others[name]={year:0}
            #Check the publication type to increment the number of publication in a specific year  
            if pub_type=="book":                           
                if year in book[name]:
                    book[name][year]+=1  
                else:
                    book[name][year]=1
            elif pub_type=="inproceedings":
                if year in proceedings[name]:
                    proceedings[name][year]+=1  
                else:
                    proceedings[name][year]=1
            elif pub_type=="article":          
                if year in article[name]:
                    article[name][year]+=1  
                else:
                    article[name][year]=1  
            else:          
                if year in others[name]:
                    others[name][year]+=1  
                else:
                    others[name][year]=1  
                    
        if(num_of_authors > 30): 
            more_30_rows.append({**info, ** {"Authors":author_list}})
        else:
            rows.append( {**info, ** {"Authors":author_list}})
         

# Create dataframes.
missing_df =  pd.DataFrame(missing_rows, columns = ["Type","Title", "Year"]) 
more_30_df =  pd.DataFrame(more_30_rows, columns = ["Type","Title", "Year","Authors"]) 
total_pub_df = pd.DataFrame(authors.items(), columns=["Authors", "Total Publications"])

df_cols =["Journal_Name","Type","Title", "Year","Authors"]
dblp_df = pd.DataFrame(rows, columns = df_cols)
#Career path dataframe
publication_df =pd.DataFrame(article.items(), columns=["Authors", "Articles"])
publication_df.loc[ : ,'Others'] = others.values()
publication_df.loc[ : ,'Books',] = book.values()
publication_df.loc[ : ,'Proceedings',] = proceedings.values()

#Co-authoring 
def new_fpgrowth(df, min_support=0.5, use_colnames=False, max_len=None, verbose=0):
    
    fpc.valid_input_check(df)

    if min_support <= 0.:
        raise ValueError('`min_support` must be a positive '
                         'number within the interval `(0, 1]`. '
                         'Got %s.' % min_support)

    colname_map = None
    if use_colnames:
        colname_map = {idx: item for idx, item in enumerate(df.columns)}

    tree, _ = fpc.setup_fptree(df, min_support)
    minsup = math.ceil(min_support * len(df.index))  # min support as count
    generator = fpg_step(tree, minsup, colname_map, max_len, verbose)

    return new_generate_itemsets(generator, len(df.index), colname_map) 

def new_generate_itemsets(generator, num_itemsets, colname_map):
    itemsets = []
    # supports = []
    commons = []
    for com, iset in generator:
        itemsets.append(frozenset(iset))
        #### before: 
        #supports.append(com / num_itemsets)
        #### now:
        commons.append(com)

    res_df = pd.DataFrame({'support': commons, 'itemsets': itemsets})

    if colname_map is not None:
        res_df['itemsets'] = res_df['itemsets'] \
            .apply(lambda x: frozenset([colname_map[i] for i in x]))

    return res_df


def fpg_step(tree, minsup, colnames, max_len, verbose):
    count = 0
    items = tree.nodes.keys()
    if tree.is_path():
        # If the tree is a path, we can combinatorally generate all
        # remaining itemsets without generating additional conditional trees
        size_remain = len(items) + 1
        if max_len:
            size_remain = max_len - len(tree.cond_items) + 1
        for i in range(1, size_remain):
            for itemset in itertools.combinations(items, i):
                count += 1
                support = min([tree.nodes[i][0].count for i in itemset])
                yield support, tree.cond_items + list(itemset)
    elif not max_len or max_len > len(tree.cond_items):
        for item in items:
            count += 1
            support = sum([node.count for node in tree.nodes[item]])
            yield support, tree.cond_items + [item]

    if verbose:
        tree.print_status(count, colnames)

    # Generate conditional trees to generate frequent itemsets one item larger
    if not tree.is_path() and (not max_len or max_len > len(tree.cond_items)):
        for item in items:
            cond_tree = tree.conditional_tree(item, minsup)
            for sup, iset in fpg_step(cond_tree, minsup,
                                      colnames, max_len, verbose):
                yield sup, iset

Name_list = np.array(dblp_df.iloc[:, 4].values)

te = TransactionEncoder()
te_ary = te.fit(Name_list).transform(Name_list)
one_hot_encoder = pd.DataFrame(te_ary, columns=te.columns_)

co_authoring = new_fpgrowth(one_hot_encoder, min_support=0.0001, use_colnames=True)
co_authoring = co_authoring.rename(columns={'support': 'common'})
co_authoring['length'] = co_authoring['itemsets'].apply(lambda x: len(x))
co_authoring = co_authoring[co_authoring['length']==2]

coauthor_df = pd.DataFrame(list(co_authoring['itemsets'].values),columns=['Author1', 'Author2'])
coauthor_df['Common'] = co_authoring['common'].values

#standalone
## Page expands to full width
st.set_page_config(layout="wide")
#add logo
image = Image.open('CSminer.jpg')
#st.image(image, width = 200)
st.image(image, caption=None, width=300, use_column_width=None, clamp=False, channels="RGB", output_format="auto")
st.title(""" Who are CS miner""")
st.subheader("Is a software that help all researcher or who are interset in computer science field to find career path and co-author relationships for a specific author or find top ten journals.")

col1 = st.sidebar
col2, col3 = st.columns((2,1))

# Sidebar + Main panel
col1.header(" Select an Option")

rad =st.sidebar.radio("",["Career Path","Co-author","Top Ten Journal"])
if rad =="Co-author":
    #get input from user
    col_one_list = total_pub_df['Authors'].tolist()
    author_name = st.selectbox("""Select Author Name""", col_one_list)
    coauthor_list = []
    common_list = []

    coauthor_list1 = coauthor_df[(coauthor_df['Author1'] == name)].Author2.values.tolist()
    common_list1 = coauthor_df[(coauthor_df['Author1'] == name)].Common.values.tolist()

    coauthor_list2 = coauthor_df[(coauthor_df['Author2'] == name)].Author1.values.tolist()
    common_list2= coauthor_df[(coauthor_df['Author2'] == name)].Common.values.tolist()

    coauthor_list = coauthor_list1+ coauthor_list2
    common_list = common_list1+ common_list2
    
    HtmlFile = open("test.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read() 
    components.html(source_code, height = 900,width=900)
    
    net = Network()
    net.add_node(0,label=name )
    net.add_nodes([i for i in range(1,len(coauthor_list)+1)], 
              label=coauthor_list,
              color= ['blue' for i in range(len(coauthor_list))], 
              title = [('# common publications: %d'%i) for i in common_list],
              size= (np.array(common_list)*20).tolist() )

    net.add_edges([(0,i) for i in range(1,len(coauthor_list)+1)])
    net.repulsion(node_distance=90, spring_length=200)
    net.show('test.html')
    from IPython.core.display import display, HTML
    display(HTML('test.html'))

if rad =="Career Path":
    #get input from user
    col_one_list = total_pub_df['Authors'].tolist()
    author_name = st.selectbox("""Select Author Name""", col_one_list)
    #Get all index in publication_df
    index = publication_df.index
    #Find index for input author
    author_index = index[publication_df["Authors"] == author_name]
    #Return data for each type for the input author
    article_data=publication_df.iloc[author_index[0]]['Articles']
    book_data=publication_df.iloc[author_index[0]]['Books']
    proceedings_data=publication_df.iloc[author_index[0]]['Proceedings']
    others_data=publication_df.iloc[author_index[0]]['Others']
    #Return all years
    Year = list(article_data.keys())
    #Visualize the career path of the input author
    fig1 = go.Figure(go.Bar(x=Year, y=list(article_data.values()) ,  marker_color='#DC143C',name='Articles',width=0.6))
    fig1.add_trace(go.Bar(x=Year, y=list(book_data.values()),marker_color='lightblue', name='Books',width=0.6))
    fig1.add_trace(go.Bar(x=Year, y=list(proceedings_data.values()),marker_color='#A8E4A0', name='Proceedings',width=0.6))
    fig1.add_trace(go.Bar(x=Year, y=list(others_data.values()),marker_color='lightslategrey', name='Others',width=0.6))
    fig1.update_layout(barmode='stack',  title='Career Path',
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
    
if rad =="Top Ten Journal":
    #Top ten journal
    top=dblp_df[((dblp_df.Year>='1990')& (dblp_df.Type=='article'))].Journal_Name
    top_10=top.value_counts()[:10].sort_values(ascending=False)

    #Visualize top ten journals
    information=['Name:'+top_10.index[0]+'<br>Impact Factor: 11'+'<br>Quadratic: Q1'
             ,'Name:'+top_10.index[1]+'<br>Impact Factor: 11'+'<br>Quadratic: Q1',
            'Name:'+top_10.index[2]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[3]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[4]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[5]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[6]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[7]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[8]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1',
            'Name:'+top_10.index[9]+'<br>Impact Factor: 11'+'<br>Quadratic Number: Q1']

    fig2 = go.Figure(data=[go.Scatter(
        x=top_10.values,
        y=[10,11,12,13,15,17,19,21,23,25],
        text=information,
        mode='markers',
        marker=dict(
        #Impact factor 
        color=['Navy','MediumBlue','Blue','CornflowerBlue','DodgerBlue', 'LightSkyBlue','LightBlue', 'LightSteelBlue','silver','lightgray'],
        size=top_10.values/20
        )
        )])
    fig2.update_layout(
        title='Top Ten Journals',
        title_x=0.5,
        font_family="sans-serif",
        font_size=14,
        font_color="black",
        xaxis=dict(
            title='Number of Publication',))
    st.plotly_chart(fig2, use_container_width=True)
