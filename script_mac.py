import subprocess
import re
import time
import datetime
import firebase_admin
from pathlib import Path

from firebase_admin import credentials
from firebase_admin import db


class Evenement:
        def __init__(self,type,adresse):
                self.type = type
                self.adresse = adresse
        type = "type"
        adresse = "00:00:00:00:00:00"

#recuperation du path vers le volume "logs"
try:
        pathStr = subprocess.check_output(["/opt/bin/lsblk","-o","label,mountpoint"]).decode("UTF-8")
except:
        pathStr = subprocess.check_output(["/usr/bin/lsblk","-o","label,mountpoint"]).decode("UTF-8")
#extraction du path depuis le resusltat
pathStr = re.findall(r"LOGS\s+(.+)\s",pathStr)[0]

#lis l'identifiant du routeur dans le fichier de configuration sur la memoire externe

fichierConfig = open(pathStr + "/config.txt","r")
routeurType = fichierConfig.readline()
routeurId = fichierConfig.readline()
dbURL = fichierConfig.readline()
fichierConfig.close()

routeurType = routeurType.strip()
routeurId = routeurId.strip()


#initialisation de al base de donee
cred = credentials.Certificate(pathStr + "/cle_db.json")
firebase_admin.initialize_app(cred,{ "databaseURL" : dbURL})
dbRef = db.reference(routeurType + "/" + routeurId)
presenceRef = db.reference("/presence/" + routeurId)

matchList2 = list()
matchList = list()
evenements = list()

macCheck = re.compile(r"(?:[A-Fa-f0-9]{2}:){5}[A-Fa-f0-9]{2}")

while 1:
        try:
                str = subprocess.check_output(["wl","-a","eth1","assoclist"])
        except:
                str = subprocess.check_output(["iw","dev","wlan0","station","dump"])

        matchList = macCheck.findall(str.decode("UTF-8"),0)
	
		for i in matchList:
			i = i.upper()
		
        #si rien n'est vide
        if matchList2 and matchList:
                #nouvelles adresses present dans matchlist mais pas dans matchlist2
                for x in matchList:
                        if x not in matchList2:
                                evenements += [Evenement("ajout",x)]
                #depart adresses non present dans matchlist
                for x in matchList2:
                        if x not in matchList:
                                evenements += [Evenement("depart",x)]
        elif matchList:
                for x in matchList:
                        evenements += [Evenement("ajout",x)]
        elif matchList2:
                for x in matchList2:
                        evenements += [Evenement("depart",x)]

        matchList2 = matchList
        time.sleep(1)

        #si il y a un nouvel evenement
        if len(evenements):
                presenceRef.update({"adresses": matchList})

        for x in evenements:
                dbRef.push({
                        "type" : x.type,
                        "adresse" : x.adresse,
                        "heure" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        evenements = []
