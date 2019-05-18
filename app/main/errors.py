from . import main

@main.errorhandler(404)
def handle404(e):
    return "404",404

@main.errorhandler(500)
def handle500(e):
    return "500",500