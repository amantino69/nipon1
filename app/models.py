from __future__ import print_function
from selenium import webdriver
from nameparser import HumanName
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from app.blueprint.utils import find_gender
import os
import shutil
import re
import time
import pandas as pd



load_dotenv()

prefixo_pastas_word = os.getenv("PREFIXO_PASTAS_WORD")
prefixo_pastas_excel = os.getenv("PREFIXO_PASTAS_EXCEL")
prefixo_fonte = os.getenv("PREFIXO_FONTE")

def get_credentials():
    user_cpf = os.environ.get('USER_CPF') or getpass('Digite o CPF: ')
    user_password = os.environ.get('USER_PASSWORD') or getpass('Digite a senha: ')
    return user_cpf, user_password

cpf, senha = get_credentials()

class MalaDireta():

    @staticmethod
    def job(resposta, dias):
        def safe_click(xpath):
            try:
                element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                element.click()
                return True
            except (NoSuchElementException, TimeoutException):
                return False

        # webdriver é DRIVER que permite a biblioteca Selenium do Python acessar
        # e entender a navegação do Google Chrome. Se for outro navegador esse arquivo
        # preciso ser substituído pelo respectivo driver. O arquivo de ficar na mesma
        # pasta onde o progra será executado ou estar na path
        chrome_options = webdriver.ChromeOptions()
        # Inicia o navegador sem abrir a tela
        chrome_options.add_argument("--headless")
        # Ignora erros de certificação digital
        chrome_options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get('https://www2.ans.gov.br/ans-idp/')

            # Informa o CPF e a senha

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'input-mask')))
        driver.find_element(By.ID, 'input-mask').send_keys(cpf)
        driver.find_element(By.ID, 'mod-login-password').send_keys(senha)
        driver.find_element(By.ID, 'botao').click()
        driver.maximize_window()

        wait = WebDriverWait(driver, 10)  # 10 segundos de tempo limite
        
        caminho_operadora = "//*[contains(text(),'" + resposta + "' )]" # Recebe o nome da operadora
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, caminho_operadora)))
        operadora = driver.find_element(By.XPATH, caminho_operadora).click() # clicar na linha da operadora escolhida

        operadora = resposta
        
        continue_button_locator = (By.ID, 'form:btnContinuar') 
        while True:
            try:
                wait.until(EC.element_to_be_clickable(continue_button_locator)).click() # clicar no botão CONFIRMAR
                break
            except StaleElementReferenceException:
                pass

        actions = ActionChains(driver)

        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Fiscalização"]')))
        e1 = driver.find_element(By.XPATH, '//span[text()="Fiscalização"]')

        e2 = driver.find_element(By.XPATH, '//span[text()="Espaço NIP"]')

        actions.move_to_element(e1).move_to_element(e2).perform() # Passar o mouse sobre Fiscalização e Espaço NIP
        e2.click() # clicar em Espaço NIP

        driver.switch_to.frame('frameConteudoDialog') # mudar para o frame do Espaço NIP Título DEMANDA

        table = driver.find_element(By.ID, 'conteudoPrincipal') # selecionar a tabela

        df = pd.read_html(table.get_attribute('outerHTML'))[1] # ler a tabela e carrega df

        elements = driver.find_elements(By.CLASS_NAME, 'ui-paginator-pages') # selecionar a quantidade de páginas
        paginas = elements[-1].text # pegar o texto da quantidade de páginas

        if len(paginas) > 9:
            paginas = paginas[:-2] # remover 2 caracteres se for maior que 9
        else:
            paginas = paginas[:-1] # remover 1 caractere se for menor que 9

        try:
            if int(paginas) >= 1: # se tiver mais de uma página

                todasDF = df
                e = 2
                for e in paginas: # Percorre todas as páginas e acumula o conteúdo em uma única tabela (df)
                    driver.find_element(
                        By.XPATH, '//*[@id="formContent:j_idt85:tbDemandaAguardandoResposta_paginator_bottom\"]/span[4]/span').click()  # clicar na próxima

                    time.sleep(10)
                    table1 = driver.find_element(
                        By.ID, 'formContent:j_idt22')
                    df1 = pd.read_html(table1.get_attribute('outerHTML'))[1]
                    todasDF = pd.concat([todasDF, df1], ignore_index=True)
                df = todasDF  # concatenar as duas tabelas
                
        except:
            print("Não há mais páginas")

        hoje = time.strftime('%d-%m-%Y') # data de hoje no formato dd-mm-aaaa

        df.insert(0, 'Operadora', operadora) # inserir coluna Operadora no dataframe df 
        df.insert(0, 'Hoje', hoje) # inserir coluna Hoje no dataframe df

        if not os.path.exists('planilha'):
            os.makedirs('planilha') # criar pasta planilha se não existir

        responder = df[(df['Prazo'] == dias + " dias úteis") 
                       & (df['Respondido'] == 'NO')] # selecionar as linhas que tem o prazo igual ao dia de hoje

        responder.to_excel('planilha/responder.xlsx', index=False) # salvar o dataframe responder em um arquivo excel
        df.to_excel('planilha/tarefas.xlsx', engine='xlsxwriter') # salvar o dataframe df em um arquivo excel
        
        dict_info = []

        if len(responder) > 0:
            for j in range(len(df)): # Percorre todas as linhas do dataframe df
                linhas = len(df) # quantidade de linhas do dataframe df
                first_name = df.loc[j, 'Beneficiário'] # seleciona o nome do beneficiário
                prazo = df.loc[j, 'Prazo'] # seleciona o prazo
                demanda = int(df.loc[j, 'Demanda']) # seleciona a demanda
                respondido = df.loc[j, 'Respondido'] # seleciona se a demanda foi respondida ou não
                if prazo == (dias + ' dias úteis') and (respondido == 'NO'): # se o prazo for igual ao dia de hoje e a demanda não foi respondida
                    name = HumanName(first_name) # separa o nome do beneficiário em primeiro nome e sobrenome
                    name.capitalize(force=True) # capitaliza o primeiro nome e o sobrenome
                    demanda_path_word = f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/' # cria o caminho da pasta para salvar o arquivo word
                    demanda_path_excel = f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/' # cria o caminho da pasta para salvar o arquivo excel

                    os.makedirs(demanda_path_word, exist_ok=True) # cria a pasta para salvar o arquivo word
                    os.makedirs(demanda_path_excel, exist_ok=True) # cria a pasta para salvar o arquivo excel

                    try:
                        driver.find_element(By.XPATH, '//*[@id="formContent:j_idt81"]/span ').click() # clicar no botão de pesquisar DEMANDA
                        time.sleep(10)
                        driver.find_element(By.ID, 'formContent:idObjeto').send_keys(demanda)  # digitar o número da demanda
                        driver.find_element(By.ID, 'formContent:j_idt82').click() # clicar no botão de BUSCAR
                        time.sleep(10)
                        driver.find_element(By.ID, 'formContent:j_idt85:tbDemandaAguardandoResposta:0:j_idt114').click() # clicar no botão de DETALHE

                    except NoSuchElementException:
                        # Handle the exception here, e.g., logging the error, skipping the iteration, or trying another approach
                        pass

                    time.sleep(15)
                    resumo = driver.find_element(By.ID, 'conteudo') # seleciona toda a tabela DEMANDA
                    
                    nip_tables = [pd.read_html(resumo.get_attribute('outerHTML'))[i] for i in range(6)] # ler a tabela e carrega df
                    nip = pd.concat(nip_tables, ignore_index=True)
                    nip = nip.iloc[:, 0].drop(nip.index[-3:]).str.replace('?', ':').str.split(':', n=1, expand=True) # separa a coluna 0 em duas colunas
                    try:
                        element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'formContent:j_idt203:0:j_idt214'))) # Clicar no botão de VISUALIZAR
                        element.click()
                    except TimeoutException:
                        try:
                            driver.find_element(By.ID, 'formContent:j_idt191:0:j_idt202').click() #
                        except NoSuchElementException:
                            pass                  
                    # time.sleep(15)
                    documento = driver.find_element(By.ID, 'formContent:dlgDocumento') # seleciona a tabela DOCUMENTO
                    notifica = pd.read_html(documento.get_attribute('outerHTML'))[0].drop_duplicates()
                    protocolo = driver.find_element(By.XPATH, '//*[@id="formContent:obDocumento"]/table[2]/tbody/tr[1]/td').text
                    numeroProtocolo = re.findall(r'\d+', protocolo)

                    ano_protocolo = numeroProtocolo[1]
                    digito_protocolo = numeroProtocolo[0]
                    notifica = notifica.drop(notifica.index[0:7]).iloc[:, 0].drop(notifica.index[-1])
                    protocoloNIP = notifica.iloc[2]
                    situacao = notifica.iloc[9]

                    if len(str(protocoloNIP)) < 4:
                        protocoloNIP = notifica.iloc[3]

                    new_rows = [
                        ['Protocolo NIP', protocoloNIP], ['DEMANDA', demanda], ['NIP', protocolo], ['NUMPROTOCOLO', numeroProtocolo],
                        ['ANO_PROTOCOLO', ano_protocolo], ['DIGITO_PROTOCOLO', digito_protocolo], ['Nome', first_name]
                    ]

                    nip = nip.append(pd.DataFrame(new_rows))

                    genero = find_gender(first_name)
                    if genero == 'F':
                        nip = nip.append(pd.DataFrame([['SEXO1', 'a']]))
                        nip = nip.append(pd.DataFrame([['SEXO2', 'a']]))
                    else:
                        nip = nip.append(pd.DataFrame([['SEXO1', 'o']]))
                        nip = nip.append(pd.DataFrame([['SEXO2', '']]))

                    dict_info.append({'Nome': first_name, 'Prazo': prazo,
                                    'Demanda': demanda, 'Gênero': genero, 'Situaçao': situacao})

                    nip.iloc[0, 0] = 'Nome'
                    nip.iloc[0, 1] = first_name

                    nip = nip.T

                    nip.columns = nip.iloc[0]
                    nip = nip.drop(nip.index[0])

                    nip.to_excel(
                        f'{prefixo_pastas_excel}/{hoje}/{operadora}/{first_name}/{demanda}/{first_name}.xlsx')
                    try:
                        wait.until(EC.element_to_be_clickable((By.ID, 'formContent:j_idt230'))).click()
                    except TimeoutException:
                        driver.find_element(By.ID, 'formContent:j_idt218').click()

                    try:
                        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    except TimeoutException:
                        pass

                    try:
                        wait.until(EC.presence_of_element_located((By.ID, 'formContent:pgDetalhes')))
                    except TimeoutException:
                        pass

                    try:
                        wait.until(EC.element_to_be_clickable((By.ID, 'formContent:j_idt208'))).click()
                    except TimeoutException:
                        driver.find_element(By.ID, 'formContent:j_idt220').click() # clicar no botão de VOLTAR

                    shutil.copy(
                        f'grifos/{operadora}.docx', (f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx')) # copia o arquivo word para a pasta

                    return dict_info