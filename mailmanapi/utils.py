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
    'MMUnknownListError': 404,
    'MMListAlreadyExistsError': 400,
    'InvalidParams': 400,
}

ERROR_MESSAGES = {
    'MMSubscribeNeedsConfirmation': 'Subscribe needs confirmation',
    'MMNeedApproval': 'Need approval',
    'MMAlreadyAMember': 'Already a member',
    'MembershipIsBanned': 'Membership is banned',
    'MMBadEmailError': 'Bad email',
    'MMHostileAddress': 'Hostile address',
    'NotAMemberError': 'Not a member',
    'MissingInformation': 'Missing information',
    'BadListNameError': 'Bad list name',
    'AssertionError': 'Assertion',
    'InvalidPassword': 'Invalid password',
    'MMUnknownListError': 'Unknown list',
    'MMListAlreadyExistsError': 'List already exists',
    'InvalidParams': 'Invalid parameters',
}


def get_error_code(class_name):
    return ERROR_CODES.get(class_name, 500)


def get_error_message(class_name):
    return ERROR_MESSAGES.get(class_name, 'Error')


def parse_boolean(value):
    if value and value.lower() == 'true':
        return True
    return False


def get_mailinglist(listname, lock=True):
    try:
        return MailList.MailList(listname, lock=lock)
    except Errors.MMUnknownListError:
        message = get_error_message('MMUnknownListError') + ': ' + listname
        status_code = get_error_code('MMUnknownListError')
        raise HTTPResponse(status=status_code,
                           body=json.dumps({'message': message}),
                           content_type='application/json')


def get_timestamp():
    return strftime('%a, %d %b %Y %H:%M:%S %z (%Z)')


def remove_list(listname):
    """
    TODO: see /usr/lib/mailman/bin/rmlist
    """
    pass
