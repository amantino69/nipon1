
from workadays import workdays as wd
from apiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import smtplib
from flask import render_template, request, jsonify
from app.models import MalaDireta
import __future__
import datetime
import pandas as pd
import os
import base64
from email.mime.text import MIMEText
from app.blueprint.utils import texto
from app.blueprint.utils import carta
import genderbr
from nameparser import HumanName
import shutil
from flask import url_for
import os
import glob

# Página inicial do sistema que solicita ao usuários escolher qual operadora
# e qual para quantidades de dias quer tratar as NIPs

# Eu
prefixo_pastas_word = "C:/Users/amantino/documents"
prefixo_pastas_excel = "C:/Users/amantino/documents/fontes"
prefixo_fonte = "C:/Users/amantino/documents/Minhas fontes de dados"


def index():
    if request.method == "POST":
        operadora = request.form.get("operadora")
        dias = request.form.get("dias")
        saida = MalaDireta.job(operadora, dias)
        tabela = pd.read_excel("planilha/responder.xlsx")
        tabela_html = tabela.to_html(
            classes=["table", "table-striped", "table-bordered", "table-hover"],
            index=False,
        )

        return render_template("saida.html", tabela_html=tabela_html)

    return render_template("index.html")


def direcionador():
    if request.method == "POST":
        lista_arquivos = glob.glob("C:/Users/amantino/Downloads/*direcionamento*.xlsx")
        arquivo_recente = max(lista_arquivos, key=os.path.getctime)
        # Capturar a data de alteração do arquivo mais recente
        data = datetime.datetime.fromtimestamp(os.path.getmtime(arquivo_recente))
        mensagem = f"O arquivo mais recente encontrado foi: {arquivo_recente}"
        tabela = pd.read_excel(arquivo_recente)
        direcionador_HAP = tabela.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], index=False
    )

              
        return render_template("direcionador.html", arquivo_recente=arquivo_recente, mensagem=mensagem, direcionador_HAP=direcionador_HAP, data=data)
    
    
 
    return render_template("direcionador.html")


def carga():
    if request.method == "POST":
        data = request.get_json(force=True)
        df = pd.read_excel("planilha/responder.xlsx")
        for key, values in data.items():
            index = int(key)
            df.at[index, "Contrato"] = values["Contrato"]
            df.at[index, "Modalidade"] = values["Modalidade"]
            df.at[index, "Registro"] = values["Registro"]
        df.to_excel("planilha/responder.xlsx", index=False)
        return jsonify({"success": True})

    df = pd.read_excel("planilha/responder.xlsx")
    return render_template("carga.html", df=df)


# Tela de retorno após processar a mala direta e tras um resumo dos beneficiários
# que se enquadraram nas opções escolhidas
def saida():
    tabela = pd.read_excel("planilha/responder.xlsx")
    tabela_html = tabela.to_html(
        classes=["table", "table-striped", "table-bordered", "table-hover"], index=False
    )

    return render_template("saida.html", tabela_html=tabela_html)


# *************************************************************************
# def texto(operadora, hoje, first_name, demanda, situacao):
#     # Chama a funcão para capitular os nomes de pessoas de forma correta.
#     # Esse nome será utilizado para criar a beneficiário mantendo o padrão de
#     # da empresa que não utiliza caixa alta nos nomes das pastas

#     name = HumanName(first_name)
#     name.capitalize(force=True)
#     hoje = datetime.datetime.now().strftime('%d/%m/%Y')

#     origem_excel = (
#         f"{prefixo_pastas_excel}/{hoje}/{operadora}/{name}/{demanda}/{name}.xlsx"
#     )
#     destino_excel = f"{prefixo_fonte}/fonte.xlsx"

#     try:
#         shutil.copyfile(origem_excel, destino_excel)
#         os.startfile(
#             f"{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx"
#         )
#         print("Arquivo copiado com sucesso")

#         # Imprimir f"{prefixo_pastas_word}/{hoje}/{operadora}/{name}/{demanda}/{name}.docx")

#     except Exception as e:
#         print(
#             "=========================================",
#             f"Erro ao copiar o arquivo: {e}",
#         )

#     return url_for("webui.responder")


def carta(responder):
    try:
        file_name = "planilha/responder.xlsx"  # File name
        sheet_name = 0  # 4th sheet
        header = 0  # The header is the 1nd row
        respNow = pd.read_excel(file_name, sheet_name, header)
        # Salvar respNow como um dataframe
        respNow = pd.DataFrame(respNow)
        # Transpor o dataframe
        # respNow = respNow.T
        respNow = pd.DataFrame(data=respNow)
    except Exception as e:
        print(e)

    return respNow


# **********************************************************************


# Essa função permite que o usuário escolha um argumento de pesquisa e uma
# quantidade de dias que quer pesquisar tarefas agendadas. Por padrão toda
# tarefa agendade de forma automática peo sistema recebe o prefíxo NIPON
# para facilitar a pesquisar

# O Google exige uma autenticação para sistemas de tereiros possam acessar as APIs
# Nessa caso estou utilizando a API Google Calendar. Para isso tive que criar crecencias de
# de autenticação e armazenar em um arquivo chamado token.json.
# Também estou utilizando o módulo googleapiclient.discovery para fazer a autenticação


def tarefas():
    if request.method == "POST":
        argumento = request.form.get("argumento")
        qdade = request.form.get("qdade")

        if argumento == "":
            argumento = "NIPON"
        if qdade == "":
            qdade = 10
    else:
        argumento = "NIP"
        qdade = 10

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                maxResults=qdade,
                singleEvents=True,
                orderBy="startTime",
                q=argumento,
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("Sem eventos com esse argumento")
            return render_template(
                "tarefas.html", event="Sem eventos com esse argumento"
            )

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print("An error occurred: %s" % error)

        return render_template("tarefas.html")

    print("Event created: %s" % (event.get("htmlLink")))
    return render_template("tarefas.html", events=events, start=start)


# Essa função permite que o usuário escolha qual beneficiário que vai fazer a mesclagem
# Ela executa o processo e abre o Word com o modelo já mesclado com os dados do beneficiário


def responder():
    if request.method == "POST":
        operadora = request.form.get("operadora")
        hoje = request.form.get("hoje")
        first_name = request.form.get("beneficiario")
        demanda = request.form.get("demanda")
        situacao = request.form.get("situacao")
        opcao = texto(hoje, operadora, first_name, demanda, situacao)

    resposta = carta(responder)
    colunas = resposta.columns.values
    linhas = resposta.values
    tuples = [tuple(x) for x in [resposta[coluna].values for coluna in colunas]]
    quantidade = len(tuples[0])

    return render_template(
        "responder.html",
        tuples=tuples,
        colunas=colunas,
        linhas=linhas,
        quantidade=quantidade,
    )


# Essa função coleta todos os beneficiários que abriram reclamação e cria uma
# tarefa no Gmail do operador do sistema considerando o número de dias utéis
# dado como prazo final para a operadora responder se penalidades
def agendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

    except HttpError as error:
        print('An error occurred: %s' % error)

        return render_template('tarefas.html')
    
    
    # Ler com pandas o arquivo excel mais recente cujo nome contem o o trech "demandas_aguardando_resposta" o no caminho "C:/Users/amantino/Downloads/"  e converta ele para dataframe
    tarefas = pd.read_excel('planilha/tarefas.xlsx', header=0)

    # Buscar o nome da operadora na celula A5 do arquivo excel e armazenar na variavel operadora
    operadora = tarefas.iloc[9, 1]
    
        # incluir coluna agendada com valor 'NO' para todas as linhas
    tarefas['agendada'] = 'NO'

    todas_demandas = pd.read_excel('planilha/todas_demandas.xlsx')
    # criar coluna agendada na planilha excel todas_demandas

    todas_demandas['agendada'] = "SIM"


    # Concatenar todas_demandas e tarefas
    todas_demandas = pd.concat([todas_demandas, tarefas], ignore_index=True)

    # Eliminar as duplicadas
    todas_demandas.drop_duplicates(
        subset="Demanda", keep="first", inplace=True)
    # Salvar planilha excel todas_demandas
    todas_demandas.to_excel('planilha/todas_demandas.xlsx', index=False)


    event = " "
    for i in range(len(todas_demandas)):
        demanda = todas_demandas['Demanda'][i]
        demanda = str(demanda)
        protocolo = todas_demandas['Protocolo'][i]
        beneficiario = todas_demandas['Beneficiário'][i]
        natureza = todas_demandas['Natureza'][i]
        notificacao = todas_demandas['Data da Notificação'][i]
        prazo = todas_demandas['Prazo'][i]
        prazo = int(prazo)
        # somar prazo em uteis a data de hoje
        # d1 = date.today()
        prazo_final = wd.workdays(notificacao, 10)
        prazo_subsidio = wd.workdays(notificacao, 8)
        # Converter data em str 'YYYY-mm-dd'
        prazo_final = prazo_final.strftime('%Y-%m-%d')
        beneficiario1 = beneficiario.upper()
        dia = 18
        mes = 1
        ano = 2023
        summary = f'{natureza} - NIP {operadora} - {beneficiario} - DEMANDA Nº {demanda} [{dia}/{mes}]'

        if todas_demandas["agendada"][i] == "NO":

            event = {
                'summary': summary,
                'location': 'Gomes e Campello',
                'description': natureza,
                'start': {
                    'date': prazo_final,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'date': prazo_final,
                    'timeZone': 'America/Los_Angeles',
                },
                'attendees': [
                    # {'email': 'Juliana.morais@campellogomes.com.br'},
                    # {'email': 'gabriela.faustino@campellogomes.com.br'},
                    # {'email': 'felipe.gomes@campellogomes.com.br'},
                    # {'email': 'marcio.campello@campellogomes.com.br'},
                    {'email': 'amantino@yahoo.com'},
                    {'email': 'claudio.vieiraamantino@gmail.com'},
                    

                ],
                'guestsCanSeeOtherGuests': True,
                'transparency': 'transparent',
                'colorId': 9,
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created: %s' % (event.get('htmlLink')))

            # Enviar e-mail
            with open("grifos/email-operadora.txt", "rb") as file:
                body = file.read().decode("utf-8")
                body = f"Boa tarde. Gabriele.\n\n Segue nova demanda ASSISTENCIAL recepcionada no Espaço NIP da Operadora em [{dia}/{mes}] \n\n\n Reclamação: Interlocutora, que se identifica como irmã da beneficiária, questiona a não cobertura para tomografia em caráter de urgência. O procedimento foi solicitado no dia [{dia}/{mes}/{ano}], para realização no município RECIFE, entretanto, a operadora negou com a justificativa de que a beneficiária está em carência para o procedimento [não soube especificar se no contrato há alguma cláusula de redução de carência]. Protocolo: não possui protocolo. (sic). \n\n\n Prazo de resolução e contato para fins de RVE (art. 10, I e II, da RN nº 483/22): {prazo_final} \n\n Prazo para envio dos subsídios: {prazo_subsidio} \n\n\n" + \
                    body
            smtp_server = "smtp.gmail.com"
            port = 587
            sender_email = "claudio.vieiraamantino@gmail.com"
            password = "qgexibuowwmpbbbq"
            recipient_emails = [attendee['email']
                                for attendee in event['attendees']]
            subject = summary
            message = f"Subject: {subject}\n\n{body}"
            message = message.encode('utf-8')

            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, recipient_emails,
                                message)

    return render_template('tarefas.html', event=event)