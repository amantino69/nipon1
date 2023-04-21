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
        driver.maximize_window()

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

        # Aguardar a conclusão do doenload do arquivo
        time.sleep(20)

        # Utilizei a planilha que o Espaço Nip disponibiliza para download para criar um dataframe com o Excel 'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls' a primeira linha é o cabeçalho.
        # Criar um dataframe com o Excel 'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls' a primeira linha é o cabeçalho.
        Excel_NIP = pd.read_excel(
            'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls', header=0)
        # Os textos do cabeçalho de Excel_NIP e das demais linhas são acentuados no formato portugues do Brasil.

        # buscar  mais recente e data de alteração do arquivo do direcionador da Hapvida 
        lista_arquivos = glob.glob("C:/Users/amantino/Downloads/*direcionamento*.xlsx")
        arquivo_recente = max(lista_arquivos, key=os.path.getctime)
        # Capturar a data de alteração do arquivo mais recente
        data = datetime.datetime.fromtimestamp(os.path.getmtime(arquivo_recente))
        direcionador_hapvida= pd.read_excel(arquivo_recente, header=0)
        # formatar direcionador_hapvida como dataframe
        direcionador_hapvida = pd.DataFrame(direcionador_hapvida)

        
        # se operadora contiver a string 'Hapvida' em maiúsculo ou minúsculo
      

        # Excluir 'C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls'
        os.remove('C:/Users/amantino/Downloads/demandas_aguardando_resposta.xls')

        # Conferte Excel_NIP para dataframe
        Excel_NIP = pd.DataFrame(Excel_NIP)
        # Converte Direcionamento para dataframe 
        direcionador_hapvida = pd.DataFrame(direcionador_hapvida)
        # Atrinir cabalhahos a Excel_NIP: data, demanda, protocolo, beneficiario, cpf, descricao, prazo, respondido, natureza
        Excel_NIP.columns = ['Data', 'Demanda', 'Protocolo', 'Beneficiário', 'cpf', 'descrição', 'Prazo', 'Respondido', 'Natureza']
        print("=========== Excel_NIP  =============================================", Excel_NIP) 
        
        #Atribuir cabelhahos a direcionador_hapvida: natureza, demanda, data, prazo5, prazo10, operadora, area, link, uf, responsavel, assunto, escritorio 
        direcionador_hapvida.columns = ["natureza", "Demanda", "data", "prazo5", "prazo10", "operadora", "area", "link", "uf", "responsavel", "assunto", "escritorio"]
        print("===========  direcionador_hapvida  =============================================", direcionador_hapvida)             
        # Deixar em Excel_NIP apenas as linhas  que coincidams com Direcionamento na coluna "demanda" 
         
        df = Excel_NIP[Excel_NIP['Demanda'].isin(direcionador_hapvida['Demanda'])]
        # elimine linha vazias em df
        df = df.dropna()
        
        
        
        hoje = time.strftime('%d-%m-%Y')  # data de hoje no formato dd-mm-aaaa

        # Acrescente as colunas "Operadora" e Hoje no dataframe df com os conteúdos das variáveis operadora e hoje respectivamente mantendo as demais colulas e seus conteúdos. Essas duas novas colunas devem ser as primeiras colunas do dataframe
        df.insert(0, 'Operadora', operadora)
        df.insert(1, 'Hoje', hoje)
        df.insert(11, 'Contrato', 'XXXXXXX')
        df.insert(12, 'Registro', 'YYYYYYY')
        df.insert(13, 'Modalidade', 'ZZZZZZZ')

        # Substituir os conteúdos do cabeçalho de df para os conteúdos da lista abaixo
        df.columns = ['Operadora', 'Hoje', 'Notificação', 'Demanda', 'Protocolo',
                      'Beneficiário', 'CPF', 'Descrição', 'Prazo', 'Respondido', 'Natureza', 'Contrato', 'Registro', 'Modalidade']

        if not os.path.exists('planilha'):
            os.makedirs('planilha')  # criar pasta planilha se não existir

        # Criar o DataFrame responder apenas com as linhas onde Prazo == dias e Respondido == 'NO'

        dia_compara = int(dias)
        
        responder = df[(df['Prazo'] == dia_compara)
                       & (df['Respondido'] == 'NO')]
        
        print("===========Responder depois  =============================================", responder)

        # salvar o dataframe responder em um arquivo excel
        responder.to_excel('planilha/responder.xlsx', index=False)
        # salvar o dataframe df em um arquivo excel
        
        df.to_excel('planilha/tarefas.xlsx', engine='xlsxwriter')
        
        print("////////////////////////////////////////df.colluns ///////////////////////", df.columns)
        print("////////////////////////////////////////df.colluns ///////////////////////", df.index)
        Demanda1 = df.iloc[0, 3]
        prazo1 = df.iloc[0, 8]
        Demanda2 = df.iloc[1, 3]
        prazo2 = df.iloc[1, 8]
        Demanda3 = df.iloc[2, 3]
        prazo3 = df.iloc[2, 8]
        print("===========Demanda1  =============================================", Demanda1)
        print("===========prazo1  =============================================", prazo1)
        print("===========Demanda2  =============================================", Demanda2)
        print("===========prazo2  =============================================", prazo2)
        print("===========Demanda3  =============================================", Demanda3)
        print("===========prazo3  =============================================", prazo3)
        

                    
        

        dict_info = []

        if not df.empty:
            j = 1
            for j in range(len(df)):  # Percorre todas as linhas do dataframe df
                print(" df>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", df)
                linhas = len(df)  # quantidade de linhas do dataframe df
                print ("linhas>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", linhas)
                # seleciona o nome do beneficiário
                demanda = df.iloc[j, 3]  # seleciona a demanda
                print("prazo>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", demanda)
                prazo = df.iloc[j, 8]  # seleciona o prazo
                print("prazo>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", prazo)
                first_name = df.iloc[j, 5]
                # seleciona se a demanda foi respondida ou não
                respondido = df.iloc[j, 9]

                # se o prazo for igual ao dia de hoje e a demanda não foi respondida

                if prazo == int(dias) and respondido == 'NO':
                    # separa o nome do beneficiário em primeiro nome e sobrenome
                    name = HumanName(first_name)
                    # capitaliza o primeiro nome e o sobrenome
                    name.capitalize(force=True)
                    # cria o caminho da pasta para salvar o arquivo word
                    demanda_path_word = f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/'
                    # cria o caminho da pasta para salvar o arquivo excel
                    demanda_path_excel = f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/'

                    # cria a pasta para salvar o arquivo word
                    os.makedirs(demanda_path_word, exist_ok=True)
                    # cria a pasta para salvar o arquivo excel
                    os.makedirs(demanda_path_excel, exist_ok=True)

                    try:
                        # clicar no botão de pesquisar DEMANDA
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="formContent:j_idt81"]/span'))).click()
                        time.sleep(10)
                        driver.find_element(By.ID, 'formContent:idObjeto').send_keys(
                            demanda)  # digitar o número da demanda
                        time.sleep(15)
                        # clicar no botão de BUSCAR
                        driver.find_element(
                            By.ID, 'formContent:j_idt82').click()
                        time.sleep(10)
                        # clicar no botão de DETALHE
                        driver.find_element(
                            By.ID, 'formContent:j_idt85:tbDemandaAguardandoResposta:0:j_idt114').click()

                    except NoSuchElementException:
                        # Handle the exception here, e.g., logging the error, skipping the iteration, or trying another approach
                        pass

                    # seleciona toda a tabela DEMANDA
                    resumo = wait.until(
                        EC.presence_of_element_located((By.ID, 'formContent')))
                    nip_tables = [pd.read_html(resumo.get_attribute('outerHTML'))[
                        i] for i in range(6)]  # ler a tabela e carrega df
                    nip = pd.concat(nip_tables, ignore_index=True)
                    nip = nip.iloc[:, 0].drop(nip.index[-3:]).str.replace('?', ':').str.split(
                        ':', n=1, expand=True)  # separa a coluna 0 em duas colunas
                    try:
                        element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
                            (By.ID, 'formContent:j_idt203:0:j_idt214')))  # Clicar no botão de VISUALIZAR
                        element.click()
                    except TimeoutException:
                        try:
                            driver.find_element(
                                By.ID, 'formContent:j_idt191:0:j_idt202').click()
                        except NoSuchElementException:
                            print(
                                "======================Não foi possível clicar no botão VISUALIZAR =============")

                    # seleciona a tabela DOCUMENTO
                    documento = wait.until(EC.presence_of_element_located(
                        (By.ID, 'formContent:dlgDocumento')))

                    notifica = pd.read_html(documento.get_attribute('outerHTML'))[
                        0].drop_duplicates()
                    protocolo = driver.find_element(
                        By.XPATH, '//*[@id="formContent:obDocumento"]/table[2]/tbody/tr[1]/td').text
                    numeroProtocolo = re.findall(r'\d+', protocolo)

                    ano_protocolo = numeroProtocolo[1]
                    digito_protocolo = numeroProtocolo[0]
                    notifica = notifica.drop(
                        notifica.index[0:7]).iloc[:, 0].drop(notifica.index[-1])
                    protocoloNIP = notifica.iloc[2]
                    situacao = notifica.iloc[9]

                    if len(str(protocoloNIP)) < 4:
                        protocoloNIP = notifica.iloc[3]

                    new_rows = [
                        ['Protocolo NIP', protocoloNIP], ['DEMANDA', demanda], [
                            'NIP', protocolo], ['NUMPROTOCOLO', numeroProtocolo],
                        ['ANO_PROTOCOLO', ano_protocolo], [
                            'DIGITO_PROTOCOLO', digito_protocolo], ['Nome', first_name]
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
                        wait.until(EC.element_to_be_clickable(
                            (By.ID, 'formContent:j_idt230'))).click()
                    except TimeoutException:
                        driver.find_element(
                            By.ID, 'formContent:j_idt218').click()

                    try:
                        wait.until(lambda d: d.execute_script(
                            "return document.readyState") == "complete")
                        driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")
                    except TimeoutException:
                        pass

                    try:
                        wait.until(EC.presence_of_element_located(
                            (By.ID, 'formContent:pgDetalhes')))
                    except TimeoutException:
                        pass

                    try:
                        wait.until(EC.element_to_be_clickable(
                            (By.ID, 'formContent:j_idt208'))).click()
                    except TimeoutException:
                        # clicar no botão de VOLTAR
                        driver.find_element(
                            By.ID, 'formContent:j_idt220').click()

                    shutil.copy(
                        f'grifos/{operadora}.docx', (f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx'))  # copia o arquivo word para a pasta

            return dict_info
