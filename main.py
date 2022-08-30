from __future__ import print_function
from flask import Flask, render_template, request # Importa a biblioteca
from itertools import count
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

app = Flask(__name__) # Inicializa a aplicação
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('C:/workspace/nipon1/app/dist/client_secret.json', SCOPES)

    creds = tools.run_flow(flow, store, flags) \
        if flags else tools.run(flow, store)
CAL = build('calendar', 'v3', http=creds.authorize(Http()))

@app.route('/') # Nova rota
def main():
    primeira = request.args.get('primeira')
    segunda = request.args.get('segunda')
    primeira = f"'{primeira}T13:00:00%s % GMT_OFF'"
    segunda = f"'{segunda}T13:00:00%s % GMT_OFF'"

    GMT_OFF = '-04:00'          # ET/MST/GMT-4
    EVENT1 = {
        'summary': 'Buy apples',
        'start': {'dateTime': primeira},
        'end': {'dateTime': segunda},
    }

    e = CAL.events().insert(calendarId='primary', sendNotifications=True, body=EVENT1).execute()
     
    return "Hello, World"

if __name__ == '__main__':
  app.run(debug=True) # Executa a aplicação
