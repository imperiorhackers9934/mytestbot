import requests as req # type: ignore
import re
import telebot
from telebot import types
from bs4 import BeautifulSoup
flag=False
bot = telebot.TeleBot("7459395965:AAGQ0WDMNluMbvwWalplnKqKhU8syiHyNW0")
myuser={}
headers = {'host': 'erp.psit.ac.in', 'Cookie': ''}
base_url = f"https://103.120.30.61"
def make_request(session, method,url, **kwargs):
    try: 
        res = session.request(method, url, verify=False, timeout=5, **kwargs)
        if res.status_code == 200:
            return {'status': 'success','data':res}
        else:
            return {'status': 'error','msg':f'HTTPError: {res.status_code}'}
    except req.ConnectionError:
        return {'status': 'error','msg':'No Internet Connection'}
    except req.Timeout:
        return {'status': 'error','msg':'Request timed out.\nSlow internet connection'}
    
def extract_info(data, pattern):
    match = re.search(pattern, data)
    return match.group(1) if match else "Not found"
def login(user,password,chat_id):
        global base_url,headers
        req.packages.urllib3.disable_warnings()
        session = req.Session()
        login_data = {"username": user, "password": password}

        # LOGIN-----------------------------------------------------------------------------------
        login_url = f"{base_url}/Erp/Auth"
        login_res = make_request(session, 'post',login_url, headers=headers, data=login_data)
        if login_res['status'] == 'error':
            base_url = f"https://erp.psit.ac.in"
            login_url = f"{base_url}/Erp/Auth"
            login_res = make_request(session, 'post',login_url, headers=headers, data=login_data)
            if login_res['status'] == 'error':
                bot.send_message(chat_id, "Error Occured"+login_res["msg"])
                pass
        
        session_id = login_res['data'].cookies.get("PHPSESSID")
        headers["Cookie"] = f"PHPSESSID={session_id}"
        bot.send_message(chat_id, "Login Successfully")
        bot.send_message(chat_id, "\nNow you Can use the Followig Commands -: \n /Attendance -> To know about your Attendance\n /login  -> To Login into your Erp with User Id and Password\n /Timetable -> To Know about Today's TimeTable\n /Marks -> To Know about your Marks in Various Tests\n /Notice -> To Know about the top Notices of College\n /author -> To Know about the author of this Bot")


def getAttendance(chat_id):
     # ATTENDENCE------------------------------------------------------------------------------
        attendance_url = f"{base_url}/Student/MyAttendanceDetail"
        session = req.Session()
        attendance_res = make_request(session, 'get', attendance_url, headers=headers)
        if attendance_res['status'] == 'error':
            return f'Error: {attendance_res["msg"]}'
        
        data = attendance_res['data'].text
        total_lecture = extract_info(data, "Total Lecture : ([0-9]*)")
        total_absent = extract_info(data, "Total Absent \+ OAA: ([0-9]*)")
        attendance_percentage = extract_info(data, "Attendance Percentage : ([0-9.]*)\s%")
        bot.send_message(chat_id, "Your Attendance Percentage is -: "+attendance_percentage+"%\nTotal Lectures -: "+total_lecture+"\nAbsent Lectures -: "+total_absent)

def getNotices(chat_id):
        notices_url = f"{base_url}/Student"
        session = req.Session()
        notices_res = make_request(session, 'get', notices_url, headers=headers)
        if notices_res['status'] == 'error':
            bot.send_message(chat_id, f'Error: {notices_res["msg"]}') 
        
        soup = BeautifulSoup(notices_res['data'].text,'html.parser')
        ntcHTML = soup.select('.table2 > tbody tr')
        notices = []
        for i in range(5):
            ntc = ntcHTML[i].find("a")
            notices.append([ntc.get_text(),ntc['href']])
        for notice in notices:
            bot.send_message(chat_id, "Notice -: "+notice[0].capitalize()+"\nLink-:"+notice[1])
def shorten_name(full_name):
    match = re.match(r'^(\S+)', full_name)
    if match:
        first_word = match.group(1)
        return first_word + " " + ' '.join(word[0] + '.' for word in full_name.split()[1:])
    return full_name

def getTimeTable(chat_id):
        timetable_url = f"{base_url}/Student/MyTimeTable"
        session = req.Session()
        timetable_res = make_request(session, 'get', timetable_url, headers=headers)
        if timetable_res['status'] == 'error':
            bot.send_message(chat_id, f'Error: {timetable_res["msg"]}')

        soup = BeautifulSoup(timetable_res['data'].text, 'html.parser')
        ttable = soup.select('.danger h5')
        ttlist = []
        if not ttable:
            bot.send_message(chat_id, 'NO TIMETABLE For Today')
            
        else:
            pattern = re.compile(r'\[\s*(.*?)\s*\]')
            for i in range(8):
                matches = pattern.findall(ttable[i].get_text())
                ttlist.append([matches[0],matches[1],matches[2]])
            data = ''
            for i in range(len(ttlist)):
                bot.send_message(chat_id, f'Lecture No.{i+1} {ttlist[i][1]:<14} {shorten_name(ttlist[i][0])}\n')
def getmarks(chat_id):
    marks_url = f"{base_url}/Student/TestSubjectMarksReport"
    session = req.Session()
    marks_res = make_request(session, 'get', marks_url, headers=headers)
    if marks_res['status'] == 'error':
            bot.send_message(chat_id, f'Error: {marks_res["msg"]}')
    soup = BeautifulSoup(marks_res['data'].text, 'html.parser')
    global testids
    testids=[]
    tests = soup.select('#cTest > option')
    for i in tests:
        testids.append([i.text,i['value']])
    for i in testids:
        bot.send_message(chat_id, f'{i[0]}')
    bot.send_message(chat_id, 'Please Enter Test Code')
    global flag
    flag=True
    
def getvalMarks(chat_id,id):
    marks_url = f"{base_url}/Student/TestSubjectMarksReport"
    session = req.Session()
    form_data = {
    'cTest': id,
    }
    marks_res = make_request(session, 'post', marks_url, headers=headers,data=form_data)
    if marks_res['status'] == 'error':
            bot.send_message(chat_id, f'Error: {marks_res["msg"]}')
    soup = BeautifulSoup(marks_res['data'].text, 'html.parser')
    testandmarks=[]
    tests = soup.select('.table > thead tr td')
    testval = soup.select('.table > tbody tr td')
    for i in range(len(tests)):
        testandmarks.append([tests[i].text,testval[i].text])
    for i in testandmarks:
         bot.send_message(chat_id, f'{i[0]} -: {i[1]}')
    global flag
    flag=False

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Welcome to ERP Bot Use /login to Continue")
@bot.message_handler(commands=['login'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Please enter your User ID:")
    myuser[message.chat.id] = "yes" 
@bot.message_handler(commands=['Attendance'])
def send_welcome(message):
    getAttendance(message.chat.id)
@bot.message_handler(commands=['Notice'])
def send_welcome(message):
    getNotices(message.chat.id)
@bot.message_handler(commands=['Timetable'])
def send_welcome(message):
    getTimeTable(message.chat.id)
@bot.message_handler(commands=['Marks'])
def send_welcome(message):
    getmarks(message.chat.id)
@bot.message_handler(commands=['help'])
def send_welcome(message):
	bot.reply_to(message, "There Are List of Commands like Helo,Author")
@bot.message_handler(commands=['author'])
def send_welcome(message):
	bot.reply_to(message, "This Telegram bot is Created by Tanishq Mishra.")
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    global username,password
    if chat_id not in myuser:
        bot.send_message(chat_id, "Please start the process by typing /start.")
        return
    
    if myuser[chat_id] == 'yes':
        username = message.text
        bot.send_message(chat_id, f"Username received: {username}\nNow, please enter your password:")
        myuser[chat_id] = 'password'
        
    elif myuser[chat_id] == 'password':
        password = message.text
        bot.send_message(chat_id, "Password received.\nThank you!  \n Please Wait!!")
        login(username,password,chat_id)
        myuser[chat_id] = None
    if(flag):
         for i in testids:
            if(i[0]==message.text):
              getvalMarks(chat_id,i[1])
              break
            
print("Bot is Currently Running !!")  
bot.polling()
