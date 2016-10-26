import sys
from nose.tools import *
from .utils import MailmanAPITestCase
from Mailman import MailList, UserDesc, Defaults

class TestAPI(MailmanAPITestCase):
    url = '/'
    data = {'address': 'user@email.com'}
    list_name = 'test_list'

    def setUp(self):
        super(TestAPI, self).setUp()
        self.create_list(self.list_name)

    def tearDown(self):
        super(TestAPI, self).tearDown()
        self.remove_list(self.list_name)

    def test_subscribe_no_moderation(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 0)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'message': 'Success'})

    def test_subscribe_confirm(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 1)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 406)
        self.assertEqual(resp.json, {'message': 'Subscribe needs confirmation'})

    def test_subscribe_approval(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 2)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': 'Need approval: subscriptions to Test_list require moderator approval'})

    def test_subscribe_banned(self):
        path = '/members'
        mlist = MailList.MailList(self.list_name)
        mlist.ban_list.append(self.data['address'])
        mlist.Save()
        mlist.Unlock()

        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json, {'message': 'Membership is banned: user@email.com'})

    def test_subscribe_already_member(self):
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)
        mlist = MailList.MailList(self.list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.json, {'message': 'Already a member: user@email.com'})

    def test_subscribe_bad_email(self):
        path = '/members'
        data = {'address': 'user@emailcom'}
        resp = self.client.put(self.url + self.list_name + path,
                               data, expect_errors=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': 'Bad email: user@emailcom'})

    def test_unsubscribe(self):
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)
        mlist = MailList.MailList(self.list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.delete(self.url + self.list_name + path,
                                  self.data, expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'message': 'Success'})

    def test_unsubscribe_not_member(self):
        path = '/members'
        resp = self.client.delete(self.url + self.list_name + path,
                                  self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json, {'message': 'Not a member: user@email.com'})

    def test_mailman_site_list_not_listed_among_lists(self):
        mailman_site_list = Defaults.MAILMAN_SITE_LIST

        self.create_list(mailman_site_list)

        resp = self.client.get(self.url, expect_errors=False)

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            self.assertNotEqual(mlist.get("listname"), mailman_site_list)

    def test_list_lists(self):
        resp = self.client.get(self.url, expect_errors=False)
        total_lists = len(resp.json)
        found = False

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertGreaterEqual(total_lists, 1)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            if mlist.get("listname") == self.list_name:
                found = True

        self.assertTrue(found)

    def test_create_list(self):
        new_list = 'new_list'
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456'}

        resp = self.client.post(url, data, expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'message': 'Success'})
        self.remove_list(new_list)

    def test_create_list_already_exists(self):
        new_list = self.list_name
        url = self.url + new_list
        data = {'admin': self.data['address'], 'password': '123456'}
        resp = self.client.post(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual({'message': 'List already exists: ' + new_list}, resp.json)

    def test_create_private_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 1}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_public_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 0}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_archive_private_out_of_max_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 2}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_archive_private_out_of_min_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': -1}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_confirm_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 1}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_approval_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 2}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 2)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_confirm_and_approval_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 3}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 3)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_subscribe_policy_out_of_max_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 4}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_subscribe_policy_out_of_min_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 0}
        resp = self.client.post(url, data, expect_errors=False)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_invalid_params(self):
        new_list = "new_list"
        url = self.url + new_list
        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 'Invalid', 'archive_private': 'Invalid'}
        resp = self.client.post(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': "Invalid parameters: invalid literal for int() with base 10: 'Invalid'"})
        self.remove_list(new_list)

    def test_create_list_invalid_password(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': ''}
        resp = self.client.post(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': 'Invalid password'})
        self.remove_list(new_list)

    def test_members(self):
        list_name = 'list13'
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)

        self.create_list(list_name)

        mlist = MailList.MailList(list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.get(self.url + list_name + path, expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([self.data['address']], resp.json)

    def test_members_address(self):
        list_name = 'list14'
        path = '/members'
        user_desc1 = UserDesc.UserDesc(self.data['address'], 'fullname1', 1)
        user_desc2 = UserDesc.UserDesc('another@email.address', 'fullname2', 1)
        self.create_list(list_name)
        mlist = MailList.MailList(list_name)
        mlist.AddMember(user_desc1)
        mlist.AddMember(user_desc2)
        mlist.Save()
        mlist.Unlock()
        # Known address.
        resp = self.client.get(self.url + list_name + path,
                               {'address': 'another@email.address'},
                               expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json,
                         [{'address': 'another@email.address',
                           'fullname': 'fullname2'}])
        # Unknown address.
        resp = self.client.get(self.url + list_name + path,
                               {'address': 'unknown@email.address'},
                               expect_errors=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json,
                         {'message': 'Not a member: unknown@email.address'})

    def test_members_unknown_list(self):
        list_name = 'list15'
        path = '/members'

        resp = self.client.get(self.url + list_name + path, expect_errors=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json, {'message': 'Unknown list: ' + list_name})

    def test_delete_non_existing_list(self):
        list_name = 'fake_list'
        resp = self.client.delete(self.url + list_name, expect_errors=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json, {'message': 'Unknown list: ' + list_name})

    def test_delete_existing_list(self):
        list_name = 'new_list'
        self.create_list(list_name)
        mlist = MailList.MailList(list_name)
        mlist.Save()
        mlist.Unlock()
        resp = self.client.delete(self.url + list_name,
                                  expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'message': 'Success'})

        # Delete archives as well.
        list_name = 'new_list2'
        self.create_list(list_name)
        mlist = MailList.MailList(list_name)
        mlist.Save()
        mlist.Unlock()
        resp = self.client.delete(self.url + list_name,
                                  {'delete_archives': True},
                                  expect_errors=False)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'message': 'Success'})

    def test_list_attr(self):
        resp = self.client.get(self.url + self.list_name, expect_errors=False)
        total_lists = len(resp.json)
        found = False

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(total_lists, 1)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            if mlist.get("listname") == self.list_name:
                found = True
        self.assertTrue(found)

    def test_fake_list_attr(self):
        resp = self.client.get(self.url + 'fake_list', expect_errors=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json, {'message': 'Unknown list: fake_list'})
