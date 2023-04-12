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

        chrome_options = webdriver.ChromeOptions()
        # Inicia o driver sem abrir a tela
        # chrome_options.add_argument("--headless")
        # Ignora erros de certificação digital
        chrome_options.add_argument('ignore-certificate-errors')

        with webdriver.Chrome(chrome_options=chrome_options) as driver:
            chrome_driver_path = 'chromedriver.exe'  # Replace this with the path to your ChromeDriver executable
            s = ChromeService(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=s)
            driver.get('https://www2.ans.gov.br/ans-idp/')  # Replace this with the URL of your target web page


            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'input-mask')))
            driver.find_element(By.ID, 'input-mask').send_keys(cpf)
            driver.find_element(By.ID, 'mod-login-password').send_keys(senha)
            driver.find_element(By.ID, 'botao').click()
            driver.maximize_window()

        wait = WebDriverWait(driver, 10)  # 10 segundos de tempo limite
        
        caminho_operadora = "//*[contains(text(),'" + resposta + "' )]"
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, caminho_operadora)))
        operadora = driver.find_element(By.XPATH, caminho_operadora).click()

        operadora = resposta
        
        continue_button_locator = (By.ID, 'form:btnContinuar')
        while True:
            try:
                wait.until(EC.element_to_be_clickable(continue_button_locator)).click()
                break
            except StaleElementReferenceException:
                pass

        actions = ActionChains(driver)

        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Fiscalização"]')))
        e1 = driver.find_element(By.XPATH, '//span[text()="Fiscalização"]')

        e2 = driver.find_element(By.XPATH, '//span[text()="Espaço NIP"]')

        actions.move_to_element(e1).move_to_element(e2).perform()
        e2.click()

        driver.switch_to.frame('frameConteudoDialog')

        table = driver.find_element(By.ID, 'conteudoPrincipal')

        df = pd.read_html(table.get_attribute('outerHTML'))[1]

        elements = driver.find_elements(By.CLASS_NAME, 'ui-paginator-pages')
        paginas = elements[-1].text

        if len(paginas) > 9:
            paginas = paginas[:-2]
        else:
            paginas = paginas[:-1]

        try:
            if int(paginas) >= 1:

                todasDF = df
                e = 2
                for e in paginas:
                    driver.find_element(
                        By.XPATH, '//*[@id="formContent:j_idt85:tbDemandaAguardandoResposta_paginator_bottom\"]/span[4]/span').click()  # clicar na próxima

                    time.sleep(10)
                    table1 = driver.find_element(
                        By.ID, 'formContent:j_idt22')
                    time.sleep(10)
                    df1 = pd.read_html(table1.get_attribute('outerHTML'))[1]
                    todasDF = pd.concat([todasDF, df1], ignore_index=True)
                df = todasDF  # concatenar as duas tabelas
                
        except:
            print("Não há mais páginas")

        hoje = time.strftime('%d-%m-%Y')

        df.insert(0, 'Operadora', operadora)
        df.insert(0, 'Hoje', hoje)

        if not os.path.exists('planilha'):
            os.makedirs('planilha')

        responder = df[(df['Prazo'] == dias + " dias úteis")
                       & (df['Respondido'] == 'NO')]

        responder.to_excel('planilha/responder.xlsx', index=False)
        df.to_excel('planilha/tarefas.xlsx', engine='xlsxwriter')
        
        dict_info = []

        if len(responder) > 0:
            for j in range(len(df)):
                linhas = len(df)
                first_name = df.loc[j, 'Beneficiário']
                prazo = df.loc[j, 'Prazo']
                demanda = int(df.loc[j, 'Demanda'])
                respondido = df.loc[j, 'Respondido']
                if prazo == (dias + ' dias úteis') and (respondido == 'NO'):
                    name = HumanName(first_name)
                    name.capitalize(force=True)
                    demanda_path_word = f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/'
                    demanda_path_excel = f'{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/'

                    os.makedirs(demanda_path_word, exist_ok=True)
                    os.makedirs(demanda_path_excel, exist_ok=True)

                    try:
                        driver.find_element(By.XPATH, '//*[@id="formContent:j_idt81"]/span ').click()
                        time.sleep(10)
                        driver.find_element(By.ID, 'formContent:idObjeto').send_keys(demanda)  
                        driver.find_element(By.ID, 'formContent:j_idt82').click()
                        time.sleep(10)
                        driver.find_element(By.ID, 'formContent:j_idt85:tbDemandaAguardandoResposta:0:j_idt114').click()

                    except NoSuchElementException:
                        # Handle the exception here, e.g., logging the error, skipping the iteration, or trying another approach
                        pass

                    time.sleep(10)
                    resumo = driver.find_element(By.ID, 'conteudo')
                    
                    nip_tables = [pd.read_html(resumo.get_attribute('outerHTML'))[i] for i in range(6)]
                    nip = pd.concat(nip_tables, ignore_index=True)
                    nip = nip.iloc[:, 0].drop(nip.index[-3:]).str.replace('?', ':').str.split(':', n=1, expand=True)
                    try:
                        element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'formContent:j_idt203:0:j_idt214')))
                        element.click()
                    except TimeoutException:
                        try:
                            driver.find_element(By.ID, 'formContent:j_idt191:0:j_idt202').click()
                        except NoSuchElementException:
                            pass                  
                    time.sleep(15)
                    documento = driver.find_element(By.ID, 'formContent:dlgDocumento')
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
                        driver.find_element(By.ID, 'formContent:j_idt220').click()

                    shutil.copy(
                        f'grifos/{operadora}.docx', (f'{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx'))

                    return dict_info