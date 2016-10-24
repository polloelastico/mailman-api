import os
import uuid
from .utils import parse_boolean, jsonify, get_mailinglist, get_timestamp, get_error_code
from Mailman import (Errors, Post, mm_cfg, UserDesc,
                     MailList, Utils, Defaults)
from bottle import request, response, template, abort

CWD = os.path.abspath(os.path.dirname(__file__))

def list_lists():
    """Lists existing mailing lists on the server.

    **Method**: GET

    **URI**: /

    Returns a list of dictionaries containing the basic attributes for
    each mailing list that exist on this server.

    **Parameters**:
      * `address` (optional): email address to search for in lists."""

    all_lists = Utils.list_names()
    lists = []

    address = request.query.get('address')
    for listname in all_lists:
        if listname == Defaults.MAILMAN_SITE_LIST:
            continue

        mlist = get_mailinglist(listname, lock=False)

        members = mlist.getMembers()
        if not address or address in members:
            list_values = {
                'listname': listname,
                'archive_private': mlist.archive_private,
                'real_name': mlist.real_name,
                'description': mlist.description,
            }

            lists.append(list_values)

    return jsonify(lists)

def list_attr(listname):
    """Returns basic attributes of specific list.

    **Method**: GET

    **URI**: /<listname>

    Returns a dictionary containing the basic attributes for
    a specific mailing list that exist on this server."""

    all_lists = Utils.list_names()
    lists = []

    response.status = 200
    response.content_type = 'application/json'
    try:
        mlist = get_mailinglist(listname)
    except Errors.MMUnknownListError, e:
        response.status = get_error_code(e.__class__.__name__)
        return {'message': str(e)}
    list_values = {
        'listname': listname,
        'archive_private': mlist.archive_private,
        'real_name': mlist.real_name,
        'description': mlist.description,
        'member_count': len(mlist.getMembers()),
        'created': mlist.created_at,
        'owner': mlist.owner
    }
    lists.append(list_values)
    return jsonify(lists)

def subscribe(listname):
    """Adds a new subscriber to the list called `<listname>`

    **Method**: PUT

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be subscribed to the list.
      * `fullname`: full name of the person being subscribed to the list.
      * `digest`: if this equals `true`, the new subscriber will receive
        digests instead of every mail sent to the list.

    """
    address = request.forms.get('address')
    fullname = request.forms.get('fullname')
    digest = parse_boolean(request.forms.get('digest'))

    mlist = get_mailinglist(listname)
    userdesc = UserDesc.UserDesc(address, fullname, digest=digest)
    message = 'Success'
    response.status = 200
    response.content_type = 'application/json'
    try:
        mlist.AddMember(userdesc)
    except (Errors.MMSubscribeNeedsConfirmation,
            Errors.MMNeedApproval,
            Errors.MMAlreadyAMember,
            Errors.MembershipIsBanned,
            Errors.MMBadEmailError,
            Errors.MMHostileAddress), e:
        response.status = get_error_code(e.__class__.__name__)
        message = str(e)
    finally:
        mlist.Save()
        mlist.Unlock()
    return jsonify({'message': message})

def unsubscribe(listname):
    """Unsubscribe an email address from the mailing list.

    **Method**: DELETE

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be unsubscribed from the list

    """
    address = request.forms.get('address')
    mlist = get_mailinglist(listname)
    message = 'Success'
    response.status_code = 200
    response.content_type = 'application/json'
    try:
        mlist.ApprovedDeleteMember(address, admin_notif=False, userack=True)
    except Errors.NotAMemberError, e:
        response.status_code = get_error_code(e.__class__.__name__)
        message = str(e)
    finally:
        mlist.Save()
        mlist.Unlock()
    return jsonify({'message': message})

def create_list(listname):
    """Create an email list.

    **Method**: PUT

    **URI**: /<listname>

    **Parameters**:

      * `admin`: email of list admin
      * `password`: list admin password
      * `subscribe_policy`: 1) Confirm; 2) Approval; 3)Confirm and approval.
      Default is Confirm (1)
      * `archive_private`: 0) Public; 1) Private. Default is Public (0) """
    admin = request.forms.get('admin')
    password = request.forms.get('password')
    subscribe_policy = request.forms.get('subscribe_policy', 1)
    archive_private = request.forms.get('archive_private', 0)

    message = 'Success'
    response.status_code = 200
    response.content_type = 'application/json'
    try:
        subscribe_policy = int(subscribe_policy)
        archive_private = int(archive_private)
    except ValueError, e:
        response.status_code = get_error_code('InvalidParams')
        return jsonify({'message': 'Invalid parameters: %s' %str(e)})

    if subscribe_policy < 1 or subscribe_policy > 3:
        subscribe_policy = 1

    if archive_private < 0 or archive_private > 1:
        archive_private = 0

    if password == '':
        response.status_code = get_error_code('InvalidPassword')
        return jsonify({'message': 'Invalid password'})
    else:
        password = Utils.sha_new(password).hexdigest()

    mail_list = MailList.MailList()
    try:
        mail_list.Create(listname, admin, password)
        mail_list.archive_private = archive_private
        mail_list.subscribe_policy = subscribe_policy
        mail_list.Save()
    except (Errors.BadListNameError, AssertionError,
            Errors.MMBadEmailError, Errors.MMListAlreadyExistsError), e:
        response.status_code = get_error_code(e.__class__.__name__)
        message = str(e)
    finally:
        mail_list.Unlock()
    return jsonify({'message': message})

def delete_list():
    """Delete an email list.

    **Method**: DELETE

    **URI**: /<listname>"""
    mlist = get_mailinglist(listname)
    message = 'Success'
    response.status_code = 200
    response.content_type = 'application/json'
    try:
        mlist.ApprovedDeleteMember(address, admin_notif=False, userack=True)
    except Errors.NotAMemberError, e:
        response.status_code = get_error_code(e.__class__.__name__)
        message = str(e)
    finally:
        mlist.Save()
        mlist.Unlock()
    return jsonify({'message': message})

def members(listname):
    """Lists subscribers for the `listname` list.

    **Method**: GET

    **URI**: /<listname>/members

    **Parameters**:

      * `address` (optional): email address to search for in list."""

    address = request.query.get('address')
    response.status_code = 200
    response.content_type = 'application/json'
    try:
        mlist = MailList.MailList(listname.lower(), lock=False)
    except Errors.MMUnknownListError, e:
        response.status_code = get_error_code(e.__class__.__name__)
        return jsonify({'message': str(e)})
    if not address:
      return jsonify(mlist.getMembers())
    else:
      member = []
      try:
        memberKey = mlist.getMemberKey(address)
      except Errors.NotAMemberError, e:
        response.status_code = get_error_code(e.__class__.__name__)
        return jsonify({'message': str(e)})
      member_values = {
          'address' : memberKey,
          'fullname' : mlist.getMemberName(memberKey)
      }
      member.append(member_values)
      return jsonify(member)
