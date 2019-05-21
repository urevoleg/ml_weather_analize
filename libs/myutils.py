# -*- coding: utf-8 -*-

import os, shutil, time, smtplib, math, re, datetime, requests, random
import numpy as np

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
