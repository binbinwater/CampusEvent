from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from campusevent import create_app

app = create_app()


def not_found(_environ, start_response):
    return Response("Not Found", status=404)(_environ, start_response)


# Nginx forwards /campusevent/... unchanged, so the Flask app sees the prefix in
# SCRIPT_NAME and generates correct links without application-level string hacks.
application = DispatcherMiddleware(not_found, {"/campusevent": app})