#! /usr/bin/env python

# must catch exceptions within here, so that errors can be reported to the user

# limit on number of times a book can be renewed == 99
# now need to update script to check date and therefore only renew if within two days....

import httplib
import urllib
import HTMLParser

class Handler:

    # The below needs to be set to ('library_number', 'email@address.co.uk', 'brighton (or sussex)')
    USERS = [
        ('', '', '')]

    def run(self):
        print ''
        for x in self.USERS:
            the_req = RequestSession(x[0],x[2])
            the_result = the_req.send_request()
            print x[1] + ' ' + x[2] + ' ' + x[0] + ':'
            print ''
            if( len(the_result) == 0 ):
                print '\033[91m' + 'No Books to Renew' + '\033[0m'
            else:
                for y in the_result:
                    if( y[1] == 1 ):
                        renewed = '\033[94m' + 'Renewed' + '\033[0m'
                    else:
                        renewed = '\033[93m' + 'Not Renewed' + '\033[0m'
                    due_date = 'Due: ' + y[2] + ' '
                    ready_for_print = 'Book: ' + y[0]
                    while len(ready_for_print) <= 90:
                        ready_for_print = ready_for_print + ' '
                    print due_date + ready_for_print + ' ' + renewed
            print ''

class RequestSession:

    HOSTNAME = 'prism.talis.com'
    PATH1 = '/'
    PATH2 = '-ac/sessions'
    HEADERS = {'Host': 'prism.talis.com',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Accept': 'text/html'}
    BARCODE = 'barcode'
    INSTITUTIONID = 'institutionID'
    BORROWERLOGINBUTTON = 'borrowLoginButton'
    LOGIN = 'Login'
    REFERER = 'referer'
    REFERER_URL = 'https%3A%2F%2Fprism.talis.com%2Fbrighton-ac%2Faccount'

    def __init__(self, library_number, uni) :

        self.form_data = urllib.urlencode({
            self.BARCODE: library_number,
            self.INSTITUTIONID: '',
            self.BORROWERLOGINBUTTON: self.LOGIN,
            self.REFERER: self.REFERER_URL})
        self.path = self.PATH1 + uni + self.PATH2
        self.uni = uni

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOSTNAME)
        connection.request('POST', self.path, self.form_data, self.HEADERS)
        return self.deal_with_response(connection.getresponse()) 

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]

	the_details = Get_Details(the_cookie, self.uni)
        return the_details.send_request()

class Get_Details:

    PATH1 = '/'
    PATH2 = '-ac/account'
    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'

    def __init__(self, cookie, uni):
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}
        self.path = self.PATH1 + uni + self.PATH2
        self.uni = uni

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('GET', self.path, headers=self.headers)
        return self.deal_with_response(connection.getresponse())

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]

        try:
            sort_account_page = SortAccountPageNewWithDate(the_cookie, self.uni)
            # Fix bad Brighton HTML so that parser does not throw error
            if self.uni == 'brighton':
                for_feed = response.read().replace("title=\"Cookie Information\"target=\"_blank\"","title=\"Cookie Information\" target=\"_blank\"",1)
            else:
                for_feed = response.read()
            sort_account_page.feed(for_feed)
            sort_account_page.close()
        except HTMLParser.HTMLParseError as HTMLError:
            print 'Problem Parsing get Book HTML Information'
        return sort_account_page.get_result_list()

class SortAccountPageNewWithDate(HTMLParser.HTMLParser):

    def __init__(self, the_cookie, uni) :
	HTMLParser.HTMLParser.__init__(self)
        self.the_cookie = the_cookie
        self.the_result = []
        self.uni = uni

        self.found_loans_table = 0
        self.found_loans_tbody = 0
        self.found_due_date = 0
        self.found_form_book_details = 0
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

        if( self.found_loans_table == 1 ):
            if( self.found_loans_tbody == 1 ):
                if( self.found_form_book_details == 1 ):
                    if( self.foundtheform == 1 ):
                        if( self.aftertheinput == 1 ):
                            for attr in attrs:
                                if( attr[0] == 'title' ):
                                    renew_the_book = RenewBookSession( self.the_cookie, self.lastbookid, self.uni )
                                    the_result = renew_the_book.send_request()
                                    self.the_result.append((attr[1][7:],the_result,self.due_date))
                                    self.due_date = None
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
                    elif( tag == 'form' ):
                        for attr in attrs:
                            if( attr[0] == 'class' and attr[1] == 'ajaxify inlineForm renewForm' ):
                                found_class_ajax = 1
		            elif( attr[0] == 'method' and attr[1] == 'post' ):
                                found_method_post = 1
                            elif( attr[0] == 'action' and attr[1] == 'https://prism.talis.com/' + self.uni + '-ac/account/loans' ):
                                found_action_loans = 1
                        if( found_class_ajax == 1 and found_method_post == 1 and found_action_loans == 1 ):
                            self.foundtheform = 1
                elif( tag == 'td' ):
                    if( attrs[0][0] == 'class' ):
                        if( attrs[0][1] == 'accDue' ):
                            self.found_due_date = 1
                        elif( attrs[0][1] == 'accActions' ):
                            self.found_form_book_details = 1
            else:
                if( tag == 'tbody' ):
                    self.found_loans_tbody = 1
        else:
            if( tag == 'table' ):
                for attr in attrs:
                    if( attr[0] == 'id' and attr[1] == 'loans' ):
                        self.found_loans_table = 1

    def handle_data(self, data):
        if self.found_due_date == 1:
            self.due_date = data

    def handle_endtag(self, tag):
        if( tag == 'form' ):
            self.foundtheform = 0
            self.aftertheinput = 0
        if( tag == 'table' ):
            self.found_loans_table = 0
        elif( tag == 'tbody' ):
            self.found_loans_tbody = 0
        elif( tag == 'td' ):
            self.found_due_date = 0
            self.found_form_book_details = 0

    def get_result_list(self):
        return self.the_result

class RenewBookSession:

    PATH1 = '/'
    PATH2 = '-ac/account/loans'
    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    CONTENT_TYPE_HEADER = 'Content-Type'
    CONTENT_TYPE = 'application/x-www-form-urlencoded'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'
    LOAN_IDS = 'loan_ids[0]'
    RENEW = 'Renew'

    def __init__(self, cookie, book_number, uni) :
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.CONTENT_TYPE_HEADER: self.CONTENT_TYPE,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}

        self.form_data = urllib.urlencode({
            self.LOAN_IDS: book_number,
            self.RENEW: self.RENEW})
        self.path = self.PATH1 + uni + self.PATH2
        self.uni = uni

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('POST', self.path, self.form_data, self.headers)
        return self.deal_with_response(connection.getresponse())
        #for testing
        #return 1 

    def deal_with_response(self, response) :
        the_headers = response.getheaders()

        for x in the_headers:
            if x[0] == 'set-cookie':
                the_cookie = x[1]
            elif x[0] == 'location':
                the_location = x[1]

        if 'the_location' in locals():
            check_for_success = ConfirmSuccessful(the_cookie, the_location, self.uni)
            return check_for_success.send_request()
        else:
            return 0

class ConfirmSuccessful:

    HOST = 'Host'
    HOST_NAME = 'prism.talis.com'
    ACCEPT_HEADER = 'Accept'
    ACCEPT = 'text/html'
    COOKIE_HEADER = 'Cookie'

    def __init__(self, cookie, location, uni):
        self.headers = {
            self.HOST: self.HOST_NAME,
            self.ACCEPT_HEADER: self.ACCEPT,
            self.COOKIE_HEADER: cookie}

        self.location = location.replace('#loans','').replace('https://prism.talis.com','')
        self.uni = uni

    def send_request(self) :
        connection = httplib.HTTPSConnection(self.HOST_NAME)
        connection.request('GET', self.location, headers=self.headers)
        return self.deal_with_response(connection.getresponse())

    def deal_with_response(self, response) :
        try:
            check_for_succeed = CheckForSucceed()
            # Fix bad Brighton HTML so that parser does not throw error
            if self.uni == 'brighton':
                for_feed = response.read().replace("title=\"Cookie Information\"target=\"_blank\"","title=\"Cookie Information\" target=\"_blank\"",1)
            else:
                for_feed = response.read()
            check_for_succeed.feed(for_feed)
            check_for_succeed.close()
        except HTMLParser.HTMLParseError as HTMLError:
            print 'Problem Parsing Renew Book HTML Information'
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
