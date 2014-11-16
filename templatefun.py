#coding: utf-8
import datetime


def dateformat(datestamp):
    mydate = datetime.datetime.fromtimestamp(datestamp)
    mydatestring = mydate.strftime("%Y-%m-%d %H-%M-%S")
    return mydatestring

    