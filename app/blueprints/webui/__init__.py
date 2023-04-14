from flask import Blueprint
from .views import index, saida, responder, tarefas, agendar

bp = Blueprint("webui", __name__, template_folder="templates", static_folder="static")

bp.add_url_rule("/", view_func=index, methods=['POST', 'GET'])
bp.add_url_rule("/saida/", view_func=saida , methods=['POST', 'GET'])
bp.add_url_rule("/responder/", view_func=responder, methods=['POST', 'GET'])
bp.add_url_rule("/tarefas/", view_func=tarefas, methods=['POST', 'GET'])
bp.add_url_rule("/agendar/", view_func=agendar, methods=['POST', 'GET'])




def init_app(app):
    app.register_blueprint(bp)
