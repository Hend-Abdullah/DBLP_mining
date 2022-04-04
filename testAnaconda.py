# The current version 
import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import xml.etree.ElementTree as et
#import plotly.graph_objects as go
#from fpgrowth_py.utils import *
import networkx as nx
import matplotlib.pyplot as plt
from mlxtend.preprocessing import TransactionEncoder
#from mlxtend.frequent_patterns import fpgrowth

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

#standalone
## Page expands to full width
st.set_page_config(layout="wide")
#add logo
image = Image.open('logo.jpg')
st.image(image, width = 500)
st.write("""# Professional Bibliographic Visualization Tool""")
st.write("""Description of the system will be here""")

col1 = st.sidebar
col2, col3 = st.columns((2,1))

# Sidebar + Main panel
col1.header('Select Options')

rad =st.sidebar.radio("",["Career Path","Co-author","Top Ten Journal"])
if rad =="Co-author":
	st.write("co-author")
if rad =="Career Path":
	#get input from user
	col_one_list = total_pub_df['Authors'].tolist()
	author_name = st.selectbox('Select Author Name', col_one_list)
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

if rad =="Top Ten Journal":
	#Top ten journal
	top=dblp_df[((dblp_df.Year>='1990')& (dblp_df.Type=='article'))].Journal_Name
	top_10=top.value_counts()[:10].sort_values(ascending=False)
	#Visualize top ten journals

