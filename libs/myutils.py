# -*- coding: utf-8 -*-

import os, shutil, time, smtplib, math, re, datetime, requests, random
import socket, subprocess, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.header import Header
from base64 import encodebytes
import email
import mimetypes
from ftplib import FTP
from slacker import Slacker
import logging
import numpy as np

DEBUG = 0

ftpsite = "realmeteo.ru"
username = "realmeteo_ramen"
userpass = "dbiBqVSx"
request = 'http://sms.ru/sms/send?api_id=ea1ff78d-d4d9-fd94-c58c-59b8632a1104&to=79253676292&text='
source = time.strftime('c://logger/%Y%m/')
dest = 'c://logger/'
foldername = time.strftime('%Y%m/')
FLAG_FTP = False
slack = Slacker('xoxp-358301679235-357856603441-358313623603-f108482dfdd570db7933695bbe0073e6')
###############################################################################
########################### МАССИВ с ПРОГНОЗАМИ ###############################
zambrettiForecast_falling = (
"Settled fine","Fine weather","Fine becoming",
"Fairly Fine, Showery (snowy) Later","Showery (snowy) becoming, more unsettled",
"Unsettled, rain (snow) later","Rain (snow) at times, worse later",
"Rain (snow) at times, becoming very unsettled","Very unsettled rain (snow)")

zambrettiForecast_steady = (
"Settled fine","Fine weather","Fine, possibly showers",
"Fairly Fine, Showers (snowy) likely","Showery (snowy) bright intervals",
"Changeable some rain (snow)","Unsettled, rain (snow) at times",
"Rain (snow) at Frequent Intervals","Very Unsettled, Rain (snow)",
"Stormy, much rain (snow)")

zambrettiForecast_rising = (
"Settled fine","Fine weather","Becoming Fine",
"Fairly Fine, Improving","Fairly Fine, Possibly showers (snow), early",
"Showery (snowy) Early, Improving","Changeable Mending",
"Rather Unsettled, Clearing Later","Unsettled, Probably Improving",
"Unsettled, short fine Intervals","Very Unsettled, Finer at times",
"Stormy, possibly improving","Stormy, much rain (snow)")

###############################################################################
#Функция ищет все файлы с именем filename во всех подкаталогах каталога catalog

def find_files(catalog, f, mode = 'extansion'):
    find_files = []
    try:
        for root, dirs, files in os.walk(catalog):
            if mode == "extansion":
                find_files += [os.path.join(root,name) for name in files if name[-3:] == f]
            elif mode == "name":
                find_files += [os.path.join(root,name) for name in files if name[:-4] == f]
        return find_files
    except Exception as e:
        return e
###############################################################################

def copy(from_catalog,to_catalog ):
    path = to_catalog
    timestamp0 = time.time()
    for root, dirs, files in os.walk(from_catalog): # пройти по директории рекурсивно
        for name in files:
            to_catalog = root.replace(from_catalog,path)
            fullname = os.path.join(root, name) # получаем полное имя файла

            if os.path.exists(to_catalog):
                pass
                shutil.copy(fullname,to_catalog)
                #print fullname + ' --> ' + to_catalog
            else:
                os.makedirs(to_catalog)
                shutil.copy(fullname,to_catalog)
                #print fullname + ' --> ' + to_catalog
        print ("The ",len(files),"'s copy to ",to_catalog," ",time.time()-timestamp0," s")
###############################################################################

def logfile(string, to_catalog = time.strftime('c://logger/%Y%m/'), filename = time.strftime('report.log')):  
    
    if os.path.exists(to_catalog):
        outfile = open(to_catalog+filename,'a')
        outfile.write(string)
        outfile.close()
    else:
        os.makedirs(to_catalog)
        outfile = open(to_catalog+filename,'w')
        outfile.write(string)
        outfile.close()
        
###############################################################################

def logfile_new(string, to_catalog = time.strftime('c://logger/%Y%m/'), filename = time.strftime('report.log')):
    
    string = time.strftime('%d.%m.%y %H:%M:%S.') + str(time.time() - int(time.time()))[2:] + '\t' + string + '\n'
    
    if os.path.exists(to_catalog):
        outfile = open(to_catalog+filename,'a')
        outfile.write(string)
        outfile.close()
    else:
        os.makedirs(to_catalog)
        outfile = open(to_catalog+filename,'w')
        outfile.write(string)
        outfile.close()
###############################################################################

def gmail(mail_subj, mail_text, attach_file, mailto):
    
    try:
        mail_from   = 'urevolegginfo@gmail.com' # отправитель
        mail_to     = mailto   # получатель
        """
        mail_text   = 'Тестовое письмо!\nПослано из python' # текст письма
        mail_subj   = 'Тестовое письмо' # заголовок письма
        attach_file = 'C:\\log.log' # прикрепляемый файл
        """
        mail_coding = 'windows-1251'
        
        # Параметры SMTP-сервера
        smtp_server = "smtp.gmail.com"
        smtp_port   = 587
        smtp_user   = "urevolegginfo@gmail.com" # пользователь smtp
        smtp_pwd    = "0KvixaqCw2"              # пароль smtp
             
        # формирование сообщения
        multi_msg = MIMEMultipart()
        multi_msg['From'] = Header(mail_from, mail_coding)
        multi_msg['To'] = Header(mail_to, mail_coding)
        multi_msg['Subject'] =  Header(mail_subj, mail_coding)
        
        msg = MIMEText(mail_text.encode('cp1251'), 'plain', mail_coding)
        msg.set_charset(mail_coding)
        multi_msg.attach(msg)
             
        # присоединяем атач-файл
        if(os.path.exists(attach_file) and os.path.isfile(attach_file)):
            file = open(attach_file, 'rb')
            attachment = MIMEBase('application', "octet-stream")
            attachment.set_payload(file.read())
            email.encoders.encode_base64(attachment)
            file.close()
            only_name_attach = Header(os.path.basename(attach_file),mail_coding);
            attachment.add_header('Content-Disposition','attachment; filename="%s"' % only_name_attach)
            multi_msg.attach(attachment)
        else:
            if(attach_file.lstrip() != ""):
                print("Файл для атача не найден - " + attach_file)
         
        # отправка
        smtp = smtplib.SMTP("smtp.gmail.com:587")
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_user, smtp_pwd)
        smtp.sendmail(mail_from, mail_to, multi_msg.as_string())
        smtp.quit()
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'c://python_scripts34/notification.py' + '\t'
        report += 'notification to ' + mailto + ' OK' + '\n'
        logfile(report, dest + foldername, 'report.log')
    except:
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'c://python_scripts34/notification.py' + '\t'
        report += 'notification Error' + '\n'
        logfile(report, dest + foldername, 'report.log')
    
############################################################################### 
def ftp_upload(source, filename):
    print('1-0')
    try:
        print('1-1')
        r = requests.head('http://'+ftpsite, timeout = 5)
        print('1-2')        
        print(r.headers)
        FLAG_FTP = True
        print('1-3')
    except:
        report = 'c://python_scripts/realmeteo.py' + '\t'
        report += ftpsite + ' 503 ERROR'
        logfile_new(string = report)
        print("503 ERROR")
        FLAG_FTP = False
        print('1-4')
        
    if FLAG_FTP == True:
        print('1-5')
        try:
            ftp = FTP(ftpsite)
            ftp.login(username, userpass)
            localfile = open(source + filename, "rb")
            ftp.storbinary("STOR " + filename, localfile)
            ftp.close
            localfile.close()
            report = 'c://python_scripts/realmeteo.py' + '\t'
            report += 'ftp_upload OK'
            logfile_new(string = report)
            print('OK')
        except:
            #localfile.close()
            ftp.close
            report = 'c://python_scripts/realmeteo.py' + '\t'
            report += 'ftp_upload Error'
            logfile_new(string = report)
            print("error upload")
        
###############################################################################
################# МЕТЕО #######################################################
###############################################################################
#################РАСЧЕТ ЭФФЕКТИВНОЙ ТЕМПЕРАТУРЫ################################
def temp_eff(t, h, v, lux):
    #скорость ветра принимаем за константу
    e = 0.01*h*6.105*np.exp((17.27*t)/(237.7+t))
    Q = lux
    result = t - 0.348*e - 0.7*v + 0.7*Q/(v + 10) - 4.25    
    return result
###############################################################################
#################РАСЧЕТ ТОЧКИ РОСЫ#############################################
def dew_point(t,h):
    h = h + 1
    a = 17.27
    b = 237.7
    func = (a*t)/(b+t) + np.log(0.01*h)
    result = (b*func)/(a-func)
    return result
###############################################################################
##############Вероятность заморозка############################################
def freezing(t13,t21):
    z, z_num = "", ''
    delta_temperature = t13 - t21
    if delta_temperature < 0:
        z = "Temp is rising!"
        z_num = False
    elif t21 < 0:
        z = "Temp is below zero!"
        z_num = True
    elif t21 <= 11:
        a0 = (0.382, 14, 0)
        a = (0.375, 10.9, 10, 3.1)
        b = (0.391, 8.6, 20, 7.6923)
        c = (0.382, 6.7, 40, 10.526)
        d = (0.382, 4.6, 60, 9.756)
        e = (0.391, 2.7, 80, 9.3)
        f = (0.4, 1.5, 100, 20)
        approx = (a0,a,b,c,d,e,f)
        i = 0
        while i < len(approx)-1:
            y = approx[i][0]*delta_temperature + approx[i][1]
            if t21 > y:
                p = round(approx[i][2] - (t21-y)*approx[i][3], 1)
                z = "Probability: " + str(p) + '%'
                z_num = p
                break
            else:
                z = "Probability: 100%"
                z_num = 100
            i = i + 1
    elif t21 > 11:
        z = "Too warm!"
        z_num = False
    return (z, z_num)
###############################################################################
############# ПРОГНОЗ ЗАМБРЕТТИ ###############################################
def zambretti(source, filename):
    flag, flag_last = 0, 0
    now_date = datetime.datetime.today()
    whatMonth = now_date.month 
    whatHour = now_date.hour
    whatHour_last = whatHour - 3
    # чтение последней строки с метеоданными
    localfile = open(source+filename, 'r')
    localfile.close
    localfile = localfile.readlines()    

    BAROMETER, BAROMETER_LAST = 0, 0    
    
    for line in localfile:  
        if str(whatHour_last)+':00:' in line and flag_last == 0:
            result = re.split(r'\t',line)
            BAROMETER_LAST = round(0.1*int(result[3]),1)
            if DEBUG == 1:            
                print(str(whatHour_last)+':00'+' line:\t', line)
                print('BAROMETER_LAST:\t', BAROMETER_LAST)
            flag_last = 1
            
        if str(whatHour)+':00:' in line and flag == 0:
            result = re.split(r'\t',line)
            BAROMETER = round(0.1*int(result[3]),1)
            if DEBUG == 1:
                print(str(whatHour)+':00:'+' line:\t', line)            
                print('BAROMETER:\t', BAROMETER)
            flag = 1
            
    if BAROMETER_LAST == 0:
        BAROMETER_LAST = BAROMETER
  
    delta_P = round(BAROMETER - BAROMETER_LAST, 1)
    print('delta:\t', delta_P)
    if delta_P > 0:
        trend = 'rising'
    elif delta_P == 0:
        trend = 'steady'
    elif delta_P < 0:
        trend = 'falling'
    
    if DEBUG == 1:
        print('trend:\t', trend)
        print('BAROMETER, BAROMETER_LAST\t', BAROMETER, BAROMETER_LAST)
        
####################### ВЫЧИСЛЕНИЕ ПРОГНОЗА ###################################
######### РОСТ ДАВЛЕНИЯ #######################################################
    if trend == 'rising':
        i = int(152.84-0.147545*BAROMETER*1.33322)
		# корректировка с учетом времени года
        if whatMonth >=4 and whatMonth<=9:
            i = i+1
            if i>=8: i=8
        result = zambrettiForecast_rising[i]

########### ПАДЕНИЕ ДАВЛЕНИЯ ##################################################
    if trend == 'falling':
        i = int(130.276-0.123628*BAROMETER*1.33322)
		# корректировка с учетом времени года
        if (whatMonth >=1 and whatMonth<=3) or (whatMonth >=10 and whatMonth<=12):
            i = i-1
            if i<0:i=0
        if i >= len(zambrettiForecast_falling):i = len(zambrettiForecast_falling)-1
        result = zambrettiForecast_falling[i]
        
########### ДАВЛЕНИЕ СТАБИЛЬНО ################################################
    if trend == 'steady':
        i = int(138.242-0.133062*BAROMETER*1.33322)
        result = zambrettiForecast_steady[i]
#*****************************************************************************#
    return (result, trend)
###############################################################################
######################## ОТПРАВКА SMS (sms.ru) ################################
def sendsms(sms, count):  
    if count < 170:
        r = requests.get(request + sms)
        code = str(r.status_code) + ' OK'
    else:
        code = 'NO, more than 170 simbols'
    report = time.strftime('%d.%m.%y %H:%M') + '\t'
    report += 'c://python_scripts34/sendsms.py' + '\t'
    report += 'sendsms: ' + code + '\n'
    logfile(report, dest + foldername, 'report.log')
###############################################################################
############# ПРОГНОЗ ТЕМПЕРАТУРЫ (на основе МНК) #############################

###############################################################################
############## ОТПРАВКА SMS GSM MODEM #########################################
def gsmmodem(phone, sms):
    try:
        cmd = 'c://python_scripts34/sms/smssender -n"+%d" -m"%s"'
        proc = subprocess.Popen(cmd % (phone, sms), shell=True, stdout=subprocess.PIPE)
        out = proc.communicate()
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'gsmmodem' + '\t'
        report += 'sms to ' + str(phone) + ' OK \n'
        logfile(report, dest + foldername, 'report.log')
    except:
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'gsmmodem' + '\t'
        report += 'sms to ' + str(phone) + ' ERROR \n'
        logfile(report, dest + foldername, 'report.log')

###############################################################################
############# РАСЧЕТ ВРЕМЕНИ ДЛЯ НАГРЕВА ######################################
def heater(T, T_ref, V, P):
    V = 5.0 * 3.85 * 2.5
    r = 1.2041
    c = 1.2
    m = r*V
    return (m*c*(T_ref - T)/P)  
###############################################################################
############### LAST METEO DATA ###############################################
def getMeteo(source, filename):
    
    # чтение последней строки с метеоданными
    localfile = open(source+filename, 'r')
    localfile.close
    localfile = localfile.readlines()
    
    flag_13 = 0
    flag_21 = 0
    
    # поиск значений для расчета вероятности заморозков
    for line in localfile:
        if re.match(r'13:00.*',line) and flag_13 == 0:
            result1 = re.split(r'\t',line)
            t_13 = 0.01*int(result1[1])
            flag_13 = 1
    
        if re.match(r'21:00.*',line) and flag_21 == 0:
            result1 = re.split(r'\t',line)
            t_21 = 0.01*int(result1[1])
            flag_21 = 1
    
    # формирование пакета данных
    
    result = re.split(r'\t',localfile[len(localfile) - 1])
    
    WEATHER_TS = time.strftime('%d.%m.%y %H:%M')
    OUTSIDETEMP = round(float(0.01*int(result[1])),1)
    OUTSIDEHUMIDITY = round(float(0.01*int(result[2])),1)
    BAROMETER = round(float(0.1*int(result[3])),1)
    EFFECTTEMP = round(temp_eff(OUTSIDETEMP, OUTSIDEHUMIDITY, 0.5, 0),1)
    INSIDETEMP = round(float(0.01*int(result[5])),1)
    
    data = 'WEATHER_TS: ' + WEATHER_TS + '\n'
    data += 'OUTSIDETEMP: ' + str(OUTSIDETEMP) + '\n'
    data += 'OUTSIDEHUMIDITY: ' + str(OUTSIDEHUMIDITY) + '\n'
    data += 'BAROMETER: ' + str(BAROMETER) + '\n'
    data += 'EFFECTTEMP: ' + str(EFFECTTEMP) + '\n'
    data += 'INSIDETEMP: ' + str(INSIDETEMP) + '\n'
    try:
        data += 'FORECAST: ' + zambretti(source, filename)[0] + '\n'
    except:
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'zambretti error\t' + time.strftime('%H:%M:%S') + '\n'
        logfile(report, dest + foldername, 'report.log')
    # добавление вероятности заморозков, если пришло время
    if flag_13 == 1 and flag_21 == 1:
        data += 'FREEZING: ' + freezing(t_13, t_21)+'\n'
    return data

###############################################################################
##################### SLACK ###################################################
def slack_message(channel = '#notifications', text = 'defaul text'):
    # Send a message to #xxx channel
    try:
        slack.chat.post_message('%s' % channel, '%s' % text)
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'slack message to ' + channel + '\t200 OK\n'
        logfile(report, dest + foldername, 'report.log')
    except:
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'slack message to ' + channel + '\tERROR\n'
        logfile(report, dest + foldername, 'report.log')
        
###############################################################################
################### READ FLAG STATE ###########################################
def readFlag(file):
    try:
        # чтение состояния FLAG
        localfile = open(file, 'r')
        localfile.close
        localfile = localfile.readlines()
        result = re.split(r'\t',localfile[len(localfile)-1])
        FLAG = int(result[2])
        return FLAG
    except:
        return None

###############################################################################
################## BACKUP YANDEX ##############################################
def backupToYandex(from_catalog,to_catalog):
    now_file = time.strftime("%Y%m%d")
    i, j = 0, 0
    for root, dirs, files in os.walk(from_catalog): # пройти по директории рекурсивно
        to = root.replace(from_catalog,to_catalog)
        for name in files:
            if now_file not in name:
                if not os.path.exists(os.path.join(to, name)):
                    if os.path.exists(to):
                        shutil.copy(os.path.join(root, name),to)
                        #print (os.path.join(root, name) + ' --> ' + to_catalog)
                        i += 1
                    else:
                        os.makedirs(to)
                        shutil.copy(os.path.join(root, name) ,to)
                        #print (os.path.join(root, name) + ' --> ' + to_catalog)
                        j += 1
    report = time.strftime("%d.%m.%y %H:%M\t") + "backup create %d folders and copy %d files\n" % (j, i)
    print(report)
    logfile(report, time.strftime("c://logger_k/%Y%m/"), "report.log")
###############################################################################
################## TELEGRAM BOT ###############################################
import telepot
token = '279783998:AAE6cxVCwU97lSbyAu0Af6EWrhpAIUV6wno'

def tlgMsg(message):
    try:
        TelegramBot = telepot.Bot(token)
        """
        updates = TelegramBot.getUpdates(67179841 + 1)
        print(updates)
        """
        """
        chat_id = #notification
        """
        TelegramBot.sendMessage(chat_id = '-155357321', text = message) 
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'telegram message to notification\t200 OK\n'
        logfile(report, dest + foldername, 'report.log')
    except:
        report = time.strftime('%d.%m.%y %H:%M') + '\t'
        report += 'telegram message to notification\tERROR\n'
        logfile(report, dest + foldername, 'report.log')
###############################################################################
        
        
