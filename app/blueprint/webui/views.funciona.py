from workadays import workdays as wd
from apiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import smtplib
from flask import render_template, request
from app.models import MalaDireta
import __future__
import pandas as pd
import os
import datetime
import base64
from email.mime.text import MIMEText


# Página inicial do sistema que solicita ao usuários escolher qual operadora
# e qual para quantidades de dias quer tratar as NIPs
def index():

    if request.method == 'POST':
        operadora = request.form.get('operadora')
        dias = request.form.get('dias')
        saida = MalaDireta.job(operadora, dias)

        return render_template('saida.html', saida=saida)

    return render_template('index.html')


# Tela de retorno após processar a mala direta e tras um resumo dos beneficiários
# que se enquadraram nas opções escolhidas
def saida():

    return render_template('saida.html')


# Essa função permite que o usuário escolha um argumento de pesquisa e uma
# quantidade de dias que quer pesquisar tarefas agendadas. Por padrão toda
# tarefa agendade de forma automática peo sistema recebe o prefíxo NIPON
# para facilitar a pesquisar

# O Google exige uma autenticação para sistemas de tereiros possam acessar as APIs
# Nessa caso estou utilizando a API Google Calendar. Para isso tive que criar crecencias de
# de autenticação e armazenar em um arquivo chamado token.json.
# Também estou utilizando o módulo googleapiclient.discovery para fazer a autenticação

def tarefas():

    if request.method == 'POST':
        argumento = request.form.get('argumento')
        qdade = request.form.get('qdade')

        if argumento == '':
            argumento = 'NIPON'
        if qdade == '':
            qdade = 10
    else:
        argumento = "NIP"
        qdade = 10

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

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary',
                                              maxResults=qdade, singleEvents=True,
                                              orderBy='startTime', q=argumento).execute()
        events = events_result.get('items', [])

        if not events:
            print('Sem eventos com esse argumento')
            return render_template('tarefas.html', event='Sem eventos com esse argumento')

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)

        return render_template('tarefas.html')

    print('Event created: %s' % (event.get('htmlLink')))
    return render_template('tarefas.html', events=events, start=start)


# Essa função permite que o usuário escolha qual beneficiário que vai fazer a mesclagem
# Ela executa o processo e abre o Word com o modelo já mesclado com os dados do beneficiário

def responder():
    if request.method == 'POST':
        operadora = request.form.get('operadora')
        hoje = request.form.get('hoje')
        first_name = request.form.get('beneficiario')
        demanda = request.form.get('demanda')
        situacao = request.form.get('situacao')
        opcao = MalaDireta.texto(
            operadora, hoje, first_name, demanda, situacao)

    resposta = MalaDireta.carta(responder)
    colunas = resposta.columns.values
    linhas = resposta.values
    tuples = [tuple(x)
              for x in [resposta[coluna].values for coluna in colunas]]
    quantidade = len(tuples[0])

    return render_template('responder.html', tuples=tuples, colunas=colunas, linhas=linhas, quantidade=quantidade)


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

    todas_demandas = pd.read_excel('planilha/todas_demandas.xlsx')
    # criar coluna agendada na planilha excel todas_demandas

    todas_demandas['agendada'] = "SIM"

    tarefas = pd.read_excel('planilha/tarefas.xlsx')

    # incluir coluna agendada com valor 'NO' para todas as linhas
    tarefas['agendada'] = 'NO'

    # Concatenar todas_demandas e tarefas
    todas_demandas = pd.concat([todas_demandas, tarefas], ignore_index=True)

    # Eliminar as duplicadas
    todas_demandas.drop_duplicates(
        subset="Demanda", keep="first", inplace=True)
    # Salvar planilha excel todas_demandas
    todas_demandas.to_excel('planilha/todas_demandas.xlsx', index=False)

    # Abrir Excel para leitura
    todas_demandas = pd.read_excel('planilha/todas_demandas.xlsx')

    event = " "

    for i in range(len(todas_demandas)):
        demanda = todas_demandas['Demanda'][i]
        demanda = str(demanda)
        protocolo = todas_demandas['Protocolo'][i]
        beneficiario = todas_demandas['Beneficiário'][i]
        operadora = todas_demandas['Operadora'][i]
        natureza = todas_demandas['Natureza'][i]
        notificacao = todas_demandas['Data da Notificação'][i]
        notificacao = notificacao[0:10]
        dia, mes, ano = notificacao.split('/')
        # Variável criada para usar no agendamento das tarefas
        dia1, mes1, ano1 = notificacao.split('/')
        notificacao = f'{ano}-{mes}-{dia}'
        notificacao = datetime.datetime.strptime(notificacao, '%Y-%m-%d')
        hoje = todas_demandas['Hoje'][i]
        # Separa dia mês e ano
        dia, mes, ano = hoje.split('-')
        hoje = f'{ano}-{mes}-{dia}'
        # converter a data para o formato do google calendar
        hoje = datetime.datetime.strptime(hoje, '%Y-%m-%d')

        prazo = todas_demandas['Prazo'][i]
        prazo = prazo.split(' ')
        prazo = prazo[0]
        prazo = int(prazo)
        # somar prazo em uteis a data de hoje
        # d1 = date.today()
        prazo_final = wd.workdays(notificacao, 10)
        # Converter data em str 'YYYY-mm-dd'
        prazo_final = prazo_final.strftime('%Y-%m-%d')
        operadora1 = operadora.split(' ')
        operadora1 = operadora1[2]
        operadora1 = operadora1.upper()
        beneficiario1 = beneficiario.upper()
        summary = f'{natureza} - NIP {operadora1} - {beneficiario1} - DEMANDA Nº {demanda} [{dia1}/{mes1}]'

        if todas_demandas["agendada"][i] == "SIM":

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
            smtp_server = "smtp.gmail.com"
            port = 587
            sender_email = "claudio.vieiraamantino@gmail.com"
            password = "pdrzpituclaxvnag"
            recipient_emails = [attendee['email']
                                for attendee in event['attendees']]
            subject = "Cezar"
            message = "Olá Mundo, tudo bem com você?"
            message = f"Subject: {subject}\n\n{body}"
            message = message.encode('utf-8')

            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, recipient_emails,
                                message)

    return render_template('tarefas.html', event=event)
