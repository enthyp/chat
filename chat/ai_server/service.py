from twisted.application import service

from chat.ai_server.server import ToxicService
import ai


def get_model_dummy(_):
    return ai.Checker()

toxic_service = ToxicService('', get_model_dummy)
application = service.Application('toxic_service')
toxic_service.setServiceParent(application)
