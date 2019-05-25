from twisted.application import service

from chat.ai_server.server import ToxicService
import ai


def get_model_dummy(_):
    checker = ai.Checker()
    checker.load_from_package(100)
    return checker

toxic_service = ToxicService('', get_model_dummy)
application = service.Application('toxic_service')
toxic_service.setServiceParent(application)
