#! /usr/bin/env python

# must catch exceptions within here, so that errors can be reported to the user

import httplib
import urllib
import HTMLParser

class Handler:

    def run(self):
        print ''
        for x in self.USERS:
            if( x[2] == 'brighton' ):
                the_req = RequestSession(x[0])
                the_result = the_req.send_request()
                print x[1] + ':'
                print ''
                if( len(the_result) == 0 ):
                    print '\033[91m' + 'No Books to Renew' + '\033[0m'
                else:
                    for y in the_result:
                        if( y[1] == 1 ):
                            renewed = '\033[94m' + 'Renewed' + '\033[0m'
                        else:
                            renewed = '\033[93m' + 'Not Renewed' + '\033[0m'
                        ready_for_print = 'Book: ' + y[0]
                        while len(ready_for_print) <= 90:
                            ready_for_print = ready_for_print + ' '
                        print ready_for_print + ' ' + renewed
                print ''

class RequestSession:

    HOSTNAME = 'prism.talis.com'
    PATH = '/brighton-ac/sessions'
    HEADERS = {'Host': 'prism.talis.com',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Accept': 'text/html'}
    BARCODE = 'barcode'
    INSTITUTIONID = 'institutionID'
    BORROWERLOGINBUTTON = 'borrowLoginButton'
    LOGIN = 'Login'
    REFERER = 'referer'
    REFERER_URL = 'https%3A%2F%2Fprism.talis.com%2Fbrighton-ac%2Faccount'

    def __init__(self, library_number) :

        self.form_data = urllib.urlencode({
            self.BARCODE: library_number,
            self.INSTITUTIONID: '',
            self.BORROWERLOGINBUTTON: self.LOGIN,
            self.REFERER: self.REFERER_URL})

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOSTNAME)
        connection.request('POST', self.PATH, self.form_data, self.HEADERS)
        return self.deal_with_response(connection.getresponse()) 

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]

	the_details = Get_Details(the_cookie)
        return the_details.send_request()

class Get_Details:

    PATH = '/brighton-ac/account'
    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'

    def __init__(self, cookie):
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('GET', self.PATH, headers=self.headers)
        return self.deal_with_response(connection.getresponse())

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]

        sort_account_page = SortAccountPageNew(the_cookie)
        sort_account_page.feed(response.read())
        return sort_account_page.get_result_list()

class SortAccountPageNew(HTMLParser.HTMLParser):

    def __init__(self, the_cookie) :
	HTMLParser.HTMLParser.__init__(self)
        self.the_cookie = the_cookie
        self.the_result = []
        self.foundtheform = 0
        self.aftertheinput = 0
        self.lastbookid = 0

    def handle_starttag(self, tag, attrs):
        found_class_ajax = 0
        found_method_post = 0
        found_action_loans = 0

        type_hidden = 0
        type_loan_ids = 0
        has_value = 0

        if( tag == 'form' ):
            for attr in attrs:
                if( attr[0] == 'class' and attr[1] == 'ajaxify inlineForm renewForm' ):
                    found_class_ajax = 1
		elif( attr[0] == 'method' and attr[1] == 'post' ):
                    found_method_post = 1
                elif( attr[0] == 'action' and attr[1] == 'https://prism.talis.com/brighton-ac/account/loans' ):
                     found_action_loans = 1
            if( found_class_ajax == 1 and found_method_post == 1 and found_action_loans == 1 ):
                self.foundtheform = 1
        elif( self.foundtheform == 1 ):
            if( self.aftertheinput == 1 ):
                for attr in attrs:
                    if( attr[0] == 'title' ):
                        renew_the_book = RenewBookSession( self.the_cookie, self.lastbookid )
                        the_result = renew_the_book.send_request()
                        self.the_result.append((attr[1][7:],the_result))
            else:
                for attr in attrs:
                    if( attr[0] == 'type' and attr[1] == 'hidden' ):
                        type_hidden = 1
                    elif( attr[0] == 'name' and attr[1] == 'loan_ids[]' ):
                        type_loan_ids = 1
                    elif( attr[0] == 'value' ):
                        has_value = 1
                        the_book_id = attr[1]
                if( type_hidden == 1 and type_loan_ids == 1 and has_value == 1 ):
                    self.lastbookid = the_book_id
                    self.aftertheinput = 1

    def handle_endtag(self, tag):
        if( tag == 'form' ):
            self.foundtheform = 0
            self.aftertheinput = 0

    def get_result_list(self):
        return self.the_result

class RenewBookSession:

    PATH = '/brighton-ac/account/loans'
    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    CONTENT_TYPE_HEADER = 'Content-Type'
    CONTENT_TYPE = 'application/x-www-form-urlencoded'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'
    LOAN_IDS = 'loan_ids[0]'
    RENEW = 'Renew'

    def __init__(self, cookie, book_number) :
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.CONTENT_TYPE_HEADER: self.CONTENT_TYPE,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}

        self.form_data = urllib.urlencode({
            self.LOAN_IDS: book_number,
            self.RENEW: self.RENEW})

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('POST', self.PATH, self.form_data, self.headers)
        return self.deal_with_response(connection.getresponse()) 

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]
            elif x[0] == 'location':
                the_location = x[1]

        check_for_success = ConfirmSuccessful(the_cookie, the_location)
        return check_for_success.send_request()

class ConfirmSuccessful:

    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'

    def __init__(self, cookie, location):
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}

        self.location = location.replace('#loans','').replace('https://prism.talis.com','')

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('GET', self.location, headers=self.headers)
        return self.deal_with_response(connection.getresponse())

    def deal_with_response(self, response) :
        check_for_succeed = CheckForSucceed()
        check_for_succeed.feed(response.read())
        return check_for_succeed.check_if_successful()

class CheckForSucceed(HTMLParser.HTMLParser):

    def __init__(self) :
	HTMLParser.HTMLParser.__init__(self)
        self.foundsuccessmarker = 0

    def handle_data(self, data):
        if( data.strip().lower() == 'request succeeded' ):
            self.foundsuccessmarker = 1

    def check_if_successful(self):
        to_be_returned = self.foundsuccessmarker
        return to_be_returned

if __name__ == "__main__":
   start = Handler()
   start.run()
