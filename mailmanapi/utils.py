import json
import logging
from time import strftime
from bottle import HTTPResponse

try:
    from Mailman import MailList, Errors
except ImportError:
    logging.error('Could not import Mailman module')

ERROR_CODES = {
    'MMSubscribeNeedsConfirmation': 406,
    'MMNeedApproval': 401,
    'MMAlreadyAMember': 405,
    'MembershipIsBanned': 403,
    'MMBadEmailError': 400,
    'MMHostileAddress': 403,
    'NotAMemberError': 400,
    'MissingInformation': 400,
    'BadListNameError': 404,
    'AssertionError': 500,
    'InvalidPassword': 400,
    'MMUnknownListError': 500,
    'MMListAlreadyExistsError': 400,
    'InvalidParams': 400,
}

def get_error_code(class_name):
    return ERROR_CODES.get(class_name, 500)

def parse_boolean(value):
    if value and value.lower() == 'true':
        return True
    return False

def jsonify(obj, status=200):
    response = HTTPResponse(content_type='application/json')
    response.body = json.dumps(obj, encoding='latin1')
    response.status = status
    return response

def get_mailinglist(listname, lock=True):
    try:
        return MailList.MailList(listname, lock=lock)
    except Errors.MMUnknownListError:
        raise jsonify("Unknown Mailing List `{}`.".format(listname), 404)

def get_timestamp():
    return strftime('%a, %d %b %Y %H:%M:%S %z (%Z)')

def remove_list(listname):
    #TODO
    #see /usr/lib/mailman/bin/rmlist
    pass
