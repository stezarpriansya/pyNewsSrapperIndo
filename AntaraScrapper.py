from antara import Antara #class news Scrapper
from datetime import timedelta, date, datetime
from IPython.display import clear_output
import sys, getopt
from requests.exceptions import ConnectionError

obj = Antara()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

#date(2018, 2, 27) - date(2018, 8, 13)
logfile = ''
start_date = ''
end_date = ''
page = ''

try:
    opts, args = getopt.getopt(sys.argv[1:], "hs:e:p:",["start_date=","end_date=","page="])
except getopt.GetoptError:
    print('AntaraScrapper.py -s <start date (YYYY-mm-dd)> -e <end date (YYYY-mm-dd)> -p <num of page>')
    sys.exit(2)

if opts:
    for opt, arg in opts:
        if opt == '-h':
            print('AntaraScrapper.py --start_date <start date (YYYY-mm-dd)> --end_date <end date (YYYY-mm-dd)> --page <num of page>')
            sys.exit()
        elif opt in ("-s", "--start_date"):
            start_date = datetime.strptime(arg, "%Y-%m-%d")
        elif opt in ("-e", "--end_date"):
            end_date = datetime.strptime(arg, "%Y-%m-%d")
        elif opt in ("-p", "--page"):
            page = int(arg)
else:
    print("Arguments not found, it will use antara's log file..")
    args = open('antara.log', 'r').readlines()
    start_date = datetime.strptime(args[1].replace('start_date=', '').strip(' \n\r\t'), "%Y-%m-%d")
    end_date = datetime.strptime(args[0].replace('end_date=', '').strip(' \n\r\t'), "%Y-%m-%d")
    page = int(args[2].replace('page=', '').strip(' \n\r\t'))

init_page = page
for single_date in daterange(start_date, end_date):
    file = open("antara.log", "w")
    file.write("end_date="+end_date.strftime('%Y-%m-%d').strip(" \n\r\t")+"\n")
    file.close()
    clear_output()
    print(single_date.strftime("%Y-%m-%d"))
    obj.getAllBerita([], init_page, datetime.strftime(single_date, "%d-%m-%Y"))
    init_page = 1
