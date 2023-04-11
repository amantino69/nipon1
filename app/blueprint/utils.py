import genderbr

def find_gender(nome):
    first_name = nome.split(' ')[0]
    genero = genderbr.get_gender(first_name)
    return(genero)