import genderbr
from nameparser import HumanName
import shutil
from flask import url_for
import os


# Ju
# prefixo_pastas_word = 'C:/Users/Juliana Silva/Documents/NIPs'
# prefixo_pastas_excel = 'C:/Users/Juliana Silva/Documents/fontes'
# prefixo_fonte = 'C:/Users/Juliana Silva/documents/Minhas fontes de dados'


# Eu
prefixo_pastas_word = 'C:/Users/amantino/Documents/NIPs'
prefixo_pastas_excel = 'C:/Users/amantino/Documents/fontes'
prefixo_fonte = 'C:/Users/amantino/documents/Minhas fontes de dados'



def find_gender(nome):
    first_name = nome.split(' ')[0]
    genero = genderbr.get_gender(first_name)
    return(genero)

    # O recurso Mala Direta do Office espera que a fonte de dados esteja sempre
    # na pasta \Documents\Minhas fontes de dados.
    # Esse módulo copia a fonte de dados específica de um determinado beneficiário
    # para a pasta \Documents\Minhas fontes de dados antes de realizar a mesclagem

def texto(operadora, hoje, first_name, demanda, situacao):

    # Chama a funcão para capitular os nomes de pessoas de forma correta.
    # Esse nome será utilizado para criar a beneficiário mantendo o padrão de
    # da empresa que não utiliza caixa alta nos nomes das pastas

    name = HumanName(first_name)
    name.capitalize(force=True)

    origem_excel = (
        f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/{name}.xlsx')
    destino_excel = (f'{prefixo_fonte}/fonte.xlsx')

    try:
        shutil.copyfile(origem_excel, destino_excel)
        os.startfile(
            f"{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx")
    except:
        print('Erro ao copiar o arquivo')

    return (url_for('webui.responder'))