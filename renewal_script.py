#! /usr/bin/env python

# must catch exceptions within here, so that errors can be reported to the user

# limit on number of times a book can be renewed == 99
# now need to update script to check date and therefore only renew if within two days.... (DONE)
# must have proper error checking so errors can be reported back to me within here! (it only takes one little change in their HTML and the whole thing can full over)

import httplib
import urllib
import HTMLParser
import datetime
import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

class Handler:

    # The below needs to be set to ('library_number', 'email@address.co.uk', 'brighton (or sussex)')
    USERS = [
        ('', '', '')]

    def run(self):
        print ''
        for x in self.USERS:
            the_req = RequestSession(x[0],x[2])
            the_result = the_req.send_request()
            email_part = EmailNotification(x[0],x[1],x[2],x[3],x[4])
            print x[1] + ' ' + x[2] + ' ' + x[0] + ':'
            print ''
            if( len(the_result) == 0 ):
                print '\033[91m' + 'No Books to Renew' + '\033[0m'
                email_part.addText('I have checked your library account and you currently have no books to renew<br />')
                email_part.sendMail()
            else:
                email_part.addText('I have done the following:<br /><br /><table style=\"border: 1px solid black;padding: 5px;\"><tr><th style=\"border: 1px solid black;padding: 5px;\">Book Name</th><th style=\"border: 1px solid black;padding: 5px;\">Due Date</th><th style=\"border: 1px solid black;padding: 5px;\">Action</th></tr>')
                for y in the_result:
                    if( y[1] == 1 ):
                        renewed = '\033[94m' + 'Renewed' + '\033[0m'
                        email_renewed = 'Renewed'
                        background = 'green'
                    elif( y[1] == 2 ):
                        renewed = '\033[93m' + 'Not Renewed, as not due until ' + DealWithDate.date_in_format(y[2]) + '\033[0m'
                        email_renewed = 'Not Renewed, not due until ' + DealWithDate.date_in_format(y[2])
                        background = 'green'
                    else:
                        renewed = '\033[91m' + 'Not Renewed - Unknown Reason' + '\033[0m'
                        email_renewed = 'Unable to Renew, please login to check.'
                        background = 'red'
                    due_date = '\033[34m' + 'Due: ' + DealWithDate.date_in_format(y[2]) + ' ' + '\033[0m'
                    ready_for_print = 'Book: ' + y[0]
                    while len(ready_for_print) <= 90:
                        ready_for_print = ready_for_print + ' '
                    print due_date + ready_for_print + ' ' + renewed
                    email_part.addText('<tr><td style=\"border: 1px solid black;padding: 5px;background-color: ' + background + ';color: white;\">' + y[0] + ' </td><td style=\"border: 1px solid black;padding: 5px;background-color: ' + background + ';color: white;\">' + DealWithDate.date_in_format(y[2]) + '</td><td style=\"border: 1px solid black;padding: 5px;background-color: ' + background + ';color: white;\">' + email_renewed + '</td></tr>')
                email_part.addText('</table>')
                email_part.sendMail()
            print ''

class EmailNotification:

    GMAILUSER = 'libraryrenewalscript@gmail.com'
    GMAILPASSWORD = ''
    MAILSERVERADDRESS = 'smtp.gmail.com'
    MAILSERVERPORT = '587'

    def __init__(self, library_id, recipient, uni, first_name, surname):
        self.library_id = library_id
        self.uni = uni
        self.recipient = recipient
        self.message = '<html>Dear ' + first_name + ' ' + surname + ',<br /><br />Regarding your University of ' + uni.capitalize() + ' library account number : ' + library_id + '.<br /><br />'

    def addText(self, message):
        self.message += message

    def sendMail(self):
        self.message += '<br />Kind Regards<br /><br />Library Renewal Bot</html>'
        msg = MIMEMultipart()
        msg['From'] = self.GMAILUSER
        msg['To'] = self.recipient
        msg['Subject'] = 'Library Renewal, library no: ' + self.library_id + ' ' + self.uni.capitalize() + ' account'
        msg.attach(MIMEText(self.message,'html'))
        mailServer = smtplib.SMTP(self.MAILSERVERADDRESS, self.MAILSERVERPORT)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(self.GMAILUSER, self.GMAILPASSWORD)
        mailServer.sendmail(self.GMAILUSER, self.recipient, msg.as_string())
        mailServer.close()

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
    REFERER_URL1 = 'https%3A%2F%2Fprism.talis.com%2F'
    REFERER_URL2 = '-ac%2Faccount'

    def __init__(self, library_number, uni) :

        self.referer_url = self.REFERER_URL1 + uni + self.REFERER_URL2
        self.form_data = urllib.urlencode({
            self.BARCODE: library_number,
            self.INSTITUTIONID: '',
            self.BORROWERLOGINBUTTON: self.LOGIN,
            self.REFERER: self.referer_url})
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
                                    if(datetime.date.today()>=(self.due_date - datetime.timedelta(days=2))):
                                        renew_the_book = RenewBookSession( self.the_cookie, self.lastbookid, self.uni )
                                        the_result = renew_the_book.send_request()
                                        self.the_result.append((attr[1][7:],the_result,self.due_date))
                                    else:
                                        self.the_result.append((attr[1][7:],2,self.due_date))
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
            self.due_date = DealWithDate.create_date_object(data)

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

class DealWithDate():

    @staticmethod
    def create_date_object(lib_date_value):
        split_date = lib_date_value.split()

        split_date[0] = split_date[0].replace('st','')
        split_date[0] = split_date[0].replace('nd','')
        split_date[0] = split_date[0].replace('rd','')
        split_date[0] = split_date[0].replace('th','')
        split_date[1] = split_date[1].upper()

        if( split_date[1] == 'JANUARY' or split_date[1] == 'JAN' ):
            split_date[1] = '1'
        elif( split_date[1] == 'FEBRUARY' or split_date[1] == 'FEB' ):
            split_date[1] = '2'
        elif( split_date[1] == 'MARCH' or split_date[1] == 'MAR' ):
            split_date[1] = '3'
        elif( split_date[1] == 'APRIL' or split_date[1] == 'APR' ):
            split_date[1] = '4'
        elif( split_date[1] == 'MAY' ):
            split_date[1] = '5'
        elif( split_date[1] == 'JUNE' or split_date[1] == 'JUN' ):
            split_date[1] = '6'
        elif( split_date[1] == 'JULY' or split_date[1] == 'JUL' ):
            split_date[1] = '7'
        elif( split_date[1] == 'AUGUST' or split_date[1] == 'AUG' ):
            split_date[1] = '8'
        elif( split_date[1] == 'SEPTEMBER' or split_date[1] == 'SEP' ):
            split_date[1] = '9'
        elif( split_date[1] == 'OCTOBER' or split_date[1] == 'OCT' ):
            split_date[1] = '10'
        elif( split_date[1] == 'NOVEMBER' or split_date[1] == 'NOV' ):
            split_date[1] = '11'
        elif( split_date[1] == 'DECEMBER' or split_date[1] == 'DEC' ):
            split_date[1] = '12'
        else:
            print 'Error'
            # will need to throw custom date format error here

        todays_date_information = str(datetime.date.today()).split('-')
        if(int(split_date[1])<int(todays_date_information[1])):
            year = int(todays_date_information[0]) + 1
        else:
            year = int(todays_date_information[0])

        return datetime.date(year,int(split_date[1]),int(split_date[0]))

    @staticmethod
    def date_in_format(date_object):
        the_day = date_object.day
        if(the_day<10):
            the_day_return = '0' + str(the_day)
        else:
            the_day_return = str(the_day)
        the_month = date_object.month
        if(the_month<10):
            the_month_return = '0' + str(the_month)
        else:
            the_month_return = str(the_month)

        return the_day_return + '/' + the_month_return + '/' + str(date_object.year)

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
