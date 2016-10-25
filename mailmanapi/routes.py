from bottle import default_app
from . import api


def create_routes(app):
    app.route('/', method='GET', callback=api.list_lists)
    app.route('/<listname>', method='PUT', callback=api.create_list)
    app.route('/<listname>', method='DELETE', callback=api.delete_list)
    app.route('/<listname>', method='GET', callback=api.list_attr)
    app.route('/<listname>/members', method='PUT', callback=api.subscribe)
    app.route('/<listname>/members', method='DELETE', callback=api.unsubscribe)
    app.route('/<listname>/members', method='GET', callback=api.members)


def get_application():
    bottle_app = default_app()

    def application(environ, start_response):
        create_routes(bottle_app)
        return bottle_app(environ, start_response)
    return application
