import os
import whois
import requests
import sqlite3
from bs4 import BeautifulSoup
from lxml import html
from socket import gaierror, timeout

def sendRequestToCaseJsp(case_prefix, case_year, case_seq) :
    url = "http://www.wipo.int/amc/en/domains/search/case.jsp"
    payload = "case_prefix="+case_prefix+"&case_year="+case_year+"&case_seq="+case_seq
    headers = {
        'connection': "keep-alive",
        'cache-control': "no-cache",
        'origin': "http://www.wipo.int",
        'upgrade-insecure-requests': "1",
        'content-type': "application/x-www-form-urlencoded",
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'referer': "http://www.wipo.int/amc/en/domains/search/",
        'accept-encoding': "gzip, deflate",
        'accept-language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        'cookie': "ABIW=balancer.cms41; JSESSIONID=9D70C16AA8A1301D184EB0BBDE4AFEA7; wipo_language=en; _ga=GA1.2.172058182.1531763218; _gid=GA1.2.1651531982.1531763218; _gat_UA-138270-1=1; _gat_UA-138270-24=1",
        'postman-token': "cacc55d8-e705-4339-8d18-40a5e6a92933"
        }
    response = requests.request("POST", url, data=payload, headers=headers)

    return response.text

def getRegistrationDateOfDomaine(domaine_name) :
    try:
        domaine_info = whois.whois(domaine_name)
        register_date = domaine_info.creation_date
        print("Registration date: " + str(register_date))
        return str(register_date[1])
    except timeout:
        return "Such domaine not found"
    except ConnectionResetError:
        return "Such domaine not found"
    except ConnectionRefusedError:
        return "Such domaine not found"
    except whois.parser.PywhoisError :
        return "Such domaine not found"
    except TypeError:
        return str(register_date)
    except gaierror :
        #os.system("whois " + domaine_name + " | grep \"Creation Date\ > tmp")
        #register_date = open('tmp', 'r').read()
        #return register_date.split(': ')[1]
        return "Such domaine not found"

def addInformationToDB(case_information, db_connect, id) :
    case_number = case_information.get("wipo case number")
    domain = case_information.get("domain name(s)")
    reg_date = case_information.get("registration date")
    complainant = case_information.get("complainant")
    decision = case_information.get("decision")
    cur = db_connect.cursor()
    sql = "INSERT INTO WIPO_CASES VALUES(%s, '%s', '%s', '%s', '%s', '%s')" % (str(id), case_number, domain, reg_date, complainant.replace('\'', '\'\''), decision)
    print("SQL: " + sql)
    with db_connect :
        cur.execute(sql)

def getInformationFromSummaryPage(summary_page) :
    try:
        soup = BeautifulSoup(summary_page)
        table = soup.find('table')
        rows = table.find_all('tr')
        register_date = ''
        case_information = {}
        for row in rows :
            cells = row.findAll("td")
            key = cells[0].find(text=True)
            value = cells[1].find(text=True)
            print(key + " : " + value)
            case_information.update({key.lower():value.lower()})
            if key.lower() == 'domain name(s)':
                register_date = getRegistrationDateOfDomaine(value.lower())
        case_information.update({"registration date":str(register_date)})
        return case_information
    except AttributeError:
        return None

if __name__ == "__main__":
    case_prefix = 'D'
    case_year = 2016
    case_seq = 283
    id =  1774
    while True:
        id += 1
        case_seq += 1
        db_connect = sqlite3.connect('wipo.db')
        summary_page = sendRequestToCaseJsp(case_prefix, str(case_year), str(case_seq).rjust(4, '0'))
        case = getInformationFromSummaryPage(summary_page)
        if case == None:
            case_year += 1
            id -= 1
            case_seq = 0
            continue
        addInformationToDB(case, db_connect, id)
