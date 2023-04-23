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
from selenium.webdriver.chrome.options import Options
from app.blueprint.utils import find_gender
import os
import shutil
import re
import time
import pandas as pd
import datetime
import glob


load_dotenv()

prefixo_pastas_word = os.getenv("PREFIXO_PASTAS_WORD")
prefixo_pastas_excel = os.getenv("PREFIXO_PASTAS_EXCEL")
prefixo_fonte = os.getenv("PREFIXO_FONTE")


def get_credentials():
    user_cpf = os.environ.get('USER_CPF') or getpass('Digite o CPF: ')
    user_password = os.environ.get(
        'USER_PASSWORD') or getpass('Digite a senha: ')
    return user_cpf, user_password


cpf, senha = get_credentials()


class MalaDireta():

    @staticmethod
    def job(resposta, dias):
        def safe_click(xpath):
            try:
                element = WebDriverWait(driver, 30).until(
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
        # chrome_options.add_argument("--headless")
        # Ignora erros de certificação digital
        chrome_options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get('https://www2.ans.gov.br/ans-idp/')

        # Informa o CPF e a senha

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'input-mask')))
        driver.find_element(By.ID, 'input-mask').send_keys(cpf)
        driver.find_element(By.ID, 'mod-login-password').send_keys(senha)
        driver.find_element(By.ID, 'botao').click()
        # driver.maximize_window()

        wait = WebDriverWait(driver, 30)  # 15 segundos de tempo limite

        # Recebe o nome da operadora
        caminho_operadora = "//*[contains(text(),'" + resposta + "' )]"
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, caminho_operadora)))
        # clicar na linha da operadora escolhida
        operadora = driver.find_element(By.XPATH, caminho_operadora).click()

        operadora = resposta

        continue_button_locator = (By.ID, 'form:btnContinuar')
        while True:
            try:
                # clicar no botão CONFIRMAR
                wait.until(EC.element_to_be_clickable(
                    continue_button_locator)).click()
                break
            except StaleElementReferenceException:
                pass

        actions = ActionChains(driver)

        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Fiscalização"]')))
        e1 = driver.find_element(By.XPATH, '//span[text()="Fiscalização"]')

        e2 = driver.find_element(By.XPATH, '//span[text()="Espaço NIP"]')

        # Passar o mouse sobre Fiscalização e Espaço NIP
        actions.move_to_element(e1).move_to_element(e2).perform()
        e2.click()  # clicar em Espaço NIP

        # mudar para o frame do Espaço NIP Título DEMANDA
        driver.switch_to.frame('frameConteudoDialog')

        # Aguardar o formContent:j_idt85:j_idt220  e clicar
        wait.until(EC.element_to_be_clickable(
            (By.ID, 'formContent:j_idt85:j_idt119'))).click()

        # Aguardar a conclusão do download do arquivo
        time.sleep(30)

        # excluir as 7 primeiras linhas do arquivo da planilha excel no caminho C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls
        Excel_NIP = pd.read_excel(
            'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls')
        # exluir as 7 primeiras linhas
        Excel_NIP = Excel_NIP.drop([0, 1, 2, 3, 4, 5, 6])

        # # Atrinir cabalhahos a Excel_NIP: data, demanda, protocolo, beneficiario, cpf, descricao, prazo, respondido, natureza
        Excel_NIP.columns = ['Data da Notificação', 'Demanda', 'Protocolo',
                             'Beneficiário', 'CPF', 'Descrição', 'Prazo', 'Respondido', 'Natureza']
        
        
        # Se a operadora for 368253 -    HAPVIDA ASSISTENCIA MEDICA S.A
        if operadora == '368253 - HAPVIDA ASSISTENCIA MEDICA S.A':

            # buscar  mais recente e data de alteração do arquivo do direcionador da Hapvida
            lista_arquivos = glob.glob(
                "C:/Users/amantino/Downloads/*direcionamento*.xlsx")
            arquivo_recente = max(lista_arquivos, key=os.path.getctime)
            # Capturar a data de alteração do arquivo mais recente
            data = datetime.datetime.fromtimestamp(
                os.path.getmtime(arquivo_recente))
            direcionador_hapvida = pd.read_excel(arquivo_recente, header=0)
            # formatar direcionador_hapvida como dataframe
            direcionador_hapvida = pd.DataFrame(direcionador_hapvida)
            direcionador_hapvida.columns = ["natureza", "Demanda", "data", "prazo5", "prazo10",
                                            "operadora", "area", "link", "uf", "responsavel", "assunto", "escritorio"]
            # Deixar em Excel_NIP apenas as linhas  que coincidams com Direcionamento na coluna "demanda"
            responder = Excel_NIP[Excel_NIP['Demanda'].isin(
                direcionador_hapvida['Demanda'])]
        else:
            responder = Excel_NIP

        tarefas = Excel_NIP
        # Aquivo será utilizado para agendar tarefas
        tarefas.to_excel('planilha/tarefas.xlsx', engine='xlsxwriter')

        # Excluir 'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls'
        os.remove('C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls')

        # Criar a variável hoje com a data de hoje no formato Dia, mês e ano sem munutos e segundos
        hoje = datetime.datetime.now().strftime('%d/%m/%Y')
        # Substituir "/" por "-" na variável hoje
        hoje = hoje.replace("/", "-")
        # Imprimir a variável hoje

        print("=============================  H O J E   ali==========", hoje)

        # Acrescente as colunas "Operadora" e Hoje no dataframe df com os conteúdos das variáveis operadora e hoje respectivamente mantendo as demais colulas e seus conteúdos. Essas duas novas colunas devem ser as primeiras colunas do dataframe
        responder.insert(0, 'Operadora', operadora)
        # responder.insert(1, 'Hoje', hoje)
        responder.insert(10, 'Contrato', 'XXXXXXX')
        responder.insert(11, 'Registro', 'YYYYYYY')
        responder.insert(12, 'Modalidade', 'ZZZZZZZ')

        

        if not os.path.exists('planilha'):
            os.makedirs('planilha')  # criar pasta planilha se não existir

        # Criar o DataFrame responder apenas com as linhas onde Prazo == dias e Respondido == 'NO'
        dia_compara = int(dias)
        responder = responder[(responder['Prazo'] == dia_compara)
                              & (responder['Respondido'] == 'NO')]

        # salvar o dataframe responder em um arquivo excel
        responder.to_excel('planilha/responder.xlsx', index=False)
        # salvar o dataframe df em um arquivo excel

        if not responder.empty:
            for j in range(len(responder)):  # Percorre todas as linhas do dataframe df

                # seleciona o nome do beneficiário
                operadora = responder.iloc[j, 0]
                notificação = responder.iloc[j, 1]
                demanda = responder.iloc[j, 2]  # seleciona a demanda
                protocolo = responder.iloc[j, 3]
                first_name = responder.iloc[j, 4]
                CPF = responder.iloc[j, 5]
                descrição = responder.iloc[j, 6]
                prazo = responder.iloc[j, 7]  # seleciona o prazo
                respondido = responder.iloc[j, 8]
                natureza = responder.iloc[j, 9]
                print("=============================  H O J E  acolá ==========", hoje)
                print("============================= P R A Z O  ==========", prazo)
                print("============================= D I A S  ==========", dias)
                print(
                    "============================= R E S P O N D I D O   ==========", respondido)
                print(
                    "============================= F I R S T N A M E   ==========", first_name)

               
                # Verifica se o beneficiário é do sexo feminino ou masculino
                genero = find_gender(first_name)
                print("=========G E N E R O================================", genero)
                print("========= N O M E  ================================", first_name)
                
                # Salvar na coluna Sexo1 na linha j de do dataframe responder "o" se o genero não for "F" e na coluna Sexo2 " " linha "j" se o genero não for "F"
                if  genero != 'F':
                    responder.insert(13, 'SEXO1', 'O')
                    responder.insert(14, 'SEXO2', '')
      
                else:
                    responder.insert(13, 'SEXO1', 'a')
                    responder.insert(14, 'SEXO2', 'a')
                
                print("=========G E N E R O================================", genero)
                print("========= N O M E  ================================", first_name)



                # separa o nome do beneficiário em primeiro nome e sobrenome
                name = HumanName(first_name)
                # capitaliza o primeiro nome e o sobrenome
                name.capitalize(force=True)

                # cria o caminho da pasta para salvar o arquivo word
                demanda_path_word = f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/'
                print(
                    "demandapathword >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", demanda_path_word)
                # cria o caminho da pasta para salvar o arquivo excel
                demanda_path_excel = f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/'
                print(
                    "demandapathexcel >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", demanda_path_excel)
                # salvar em arquivo .txt demanda_pastas_excel
                with open('demandas_pastas_excel.txt', 'w') as f:
                     f.write(demanda_path_excel)
                     f.close() 

                # 

                # cria a pasta para salvar o arquivo word
                os.makedirs(demanda_path_word, exist_ok=True)
                # cria a pasta para salvar o arquivo excel
                os.makedirs(demanda_path_excel, exist_ok=True)

                # new_rows = [
                #     ['Protocolo NIP', protocolo], ['DEMANDA', demanda], ['Nome', first_name]]

                # df = df.append(pd.DataFrame(new_rows))

                # genero = find_gender(first_name)

                # df.iloc[0, 0] = 'Nome'
                # df.iloc[0, 1] = first_name

                # df = df.T

                # df.columns = df.iloc[0]
                # df = df.drop(df.index[0])
                # mantar somente a linha "j"do df responder
                responder1 = responder.iloc[[j]] 
                # Remova as colunas SEXO1 e SEXO2 do dataframe responder1
                responder = responder.drop(['SEXO1', 'SEXO2'], axis=1)
                
                responder1.to_excel(
                    f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/{first_name}.xlsx')

                shutil.copy(
                    f'grifos/{operadora}.docx', (f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx'))  # copia o arquivo word para a pasta

            return responder
