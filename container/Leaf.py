
import utils

import logging
import json
import requests
from threading import Thread
import pycarwings2
import time
from time import sleep
from configparser import SafeConfigParser
import sys
import datetime
from datetime import datetime
import _thread
import traceback

class LeafHandler(utils.BaseApp):
    #Persistent info
    PersistentSession = None
    LastUpdate = None
    LastUpdated = None
    LastSuccess = None
    Updating = False
    Error = False
    
    def __init__(self):
        print("Opening LEAF connection")
        self.PersistentSession = self.Login()
        #self.RequestUpdate_Threaded(self.PersistentSession)
        self.StartUpdateLoop(self.PersistentSession)
        #self.GetLatestStatus(self.PersistentSession, True)
        print("LEAF ready!")

    def ProcessIntent(self, intent, request):
        speech = "Sorry, but there was an error processing the request."
        try:
            if intent == "LEAF_UpdateStatus":
                #Requests an update of battery stats
                self.RequestUpdate_Threaded(self.PersistentSession)
                speech = "Status update requested!"
            elif intent == "LEAF_GetStatus":
                speech = self.GetStatusResponse(self.PersistentSession)
            elif intent == "LEAF_ClimateOn":
                #Turns on the climate control for preheating/cooling
                dialog_state = request.json['request']['dialogState']
                if (dialog_state == "STARTED"):
                    return utils.continue_dialog()
                elif (dialog_state == "IN_PROGRESS"):
                    choice = request.json['request']['intent']['confirmationStatus'] == "CONFIRMED"
                    speech = self.ActivateClimateControl(self.PersistentSession, choice)
            elif intent == "LEAF_ClimateOff":
                #Turns off the climate control
                self.DeactivateClimateControl(self.PersistentSession)
                speech = "Turning off climate control."
            elif intent == "LEAF_StartCharge":
                dialog_state = request.json['request']['dialogState']
                if (dialog_state == "STARTED"):
                    return self.StartCharging_Start(self.PersistentSession)
                elif (dialog_state == "IN_PROGRESS"):
                    choice = request.json['request']['intent']['confirmationStatus'] == "CONFIRMED"
                    speech = self.StartCharging_Confirm(self.PersistentSession, choice)
            else:
                speech = "Sorry, no handler was found for the intent "+intent
        except:
            speech = "Hmm, an internal error occured while processing the request."
            traceback.print_exc()
        return utils.return_speech(speech)
        
    def Ready(self):
        return self.LastUpdate != None
        
    def GetStatsForDisplay(self):
        stats = ""
        if not self.Ready(): return "LEAF processor is not ready."
        stats += "LEAF processor is ready.</br>"
        #LEAF is (not) plugged in with (N) bars.
        #LEAF is charging.
        #Last updated at [time]
        stats += "LEAF is "
        if (not self.LastUpdate.is_connected):
            stats += "not "
        stats += "plugged in with {0} bars.</br>".format(self.LastUpdate.battery_remaining_amount)
        if (self.LastUpdate.is_charging): stats += "LEAF is charging.</br>"
        stats += "Last updated at {0}.</br>".format(self.LastSuccess)
        
        return stats
        
        
    def GetStatusResponse(self, leaf):
        #Lets the user know the status of the car
        #If not charging: "The TIE Fighter is at 58 percent charge"
        #If charging: "The TIE fighter is at 58 percent charge and will finish charging in 2 hours 30 minutes

        #if updating, let the user know
        speech = "Error"
        if self.Updating:
            speech = "The status is currently being updated. Try again in a few minutes."
        else:
            results = self.GetLatestStatus(leaf, False)
            if results:
                date = datetime.strptime(results.answer["BatteryStatusRecords"]["OperationDateAndTime"], "%b %d, %Y %I:%M %p")
                minutes = int((datetime.now() - date).total_seconds() / 60)
                pluggedMsg = ""
                if (not results.is_connected):
                    pluggedMsg = "not "
                speech = "As of {0} minutes ago the leaf is at {1} bars and is {2}plugged in.".format(minutes, int(results.battery_remaining_amount), pluggedMsg)  
                if (results.is_charging):
                    hours = 0
                    minutes = 0
                    time_holder = None
                    if (results.time_to_full_trickle):
                        time_holder = results.time_to_full_trickle
                    elif (results.time_to_full_l2):
                        time_holder = results.time_to_full_l2
                    elif (results.time_to_full_l2_6kw):
                        time_holder = results.time_to_full_l2_6kw      

                    hours = int(time_holder.total_seconds() / 3600)
                    minutes = int((time_holder.total_seconds() - (int(hours)*3600)) / 60)
                    speech += " It is charging with "
                    if (int(hours) > 0): speech += "{0} hours ".format(hours)
                    if (int(hours) > 0 and int(minutes) > 0): speech += "and "
                    if (int(minutes) > 0): speech += "{0} minutes ".format(minutes)
                    speech += "remaining."
            else:
                speech = "No results cached. Try again in a few minutes."
                self.RequestUpdate_Threaded(leaf)

        #self.RequestUpdate_Threaded(leaf)
        return speech
  


#Nissan API Related

    def Login(self):
        parser = SafeConfigParser()
        candidates = [ 'config.ini', 'my_config.ini' ]
        found = parser.read(candidates)

        username = parser.get('get-leaf-info', 'username')
        password = parser.get('get-leaf-info', 'password')

        logging.debug("login = %s , password = %s" % ( username , password)  )

        print("Prepare Session")
        s = pycarwings2.Session(username, password , "NNA")
        print("Login...")
        return s.get_leaf()
      
    def RequestUpdate(self, leaf, block=False):
        utils.PrintTimed("Requesting Update")
        result_key = leaf.request_update()
        if block:
            status = leaf.get_status_from_update(result_key)
            while status is None:
                sleep(10)
                status = leaf.get_status_from_update(result_key)
        utils.PrintTimed("Update Completed")

    def GetLatestStatus(self, leaf, update=False):
        if update: self.SetLastUpdate(leaf)
        return self.LastUpdate

    def ActivateClimateControl(self, leaf, choice):
        if choice:
            leaf.start_climate_control()
            return "Activating climate control."            
        return "Not starting climate control."
  
    def DeactivateClimateControl(self, leaf):
        print("Deactivating Climate Control")
        leaf.stop_climate_control()

    def RequestUpdate_Threaded(self, leaf):
        _thread.start_new_thread(self.FullUpdate, (leaf, ))
        
    def StartCharging_Start(self, leaf):
        #require an existing status, start charging if plugged in
        latest = self.GetLatestStatus(leaf)
        if latest == None:
            self.RequestUpdate_Threaded(leaf)
            return utils.return_speech("No status cached. Try again in a few minutes.")
        elif latest.is_charging:
            return utils.return_speech("Leaf is already charging.")
        elif not latest.is_connected:
            return utils.return_speech("The leaf is not plugged in.")
        else:
            return utils.continue_dialog()
            
    def StartCharging_Confirm(self, leaf, choice):
        if choice:
            if leaf.start_charging():
                return "Starting charge"
            else:
                return "Could not start charge."
        return "Not starting charge. Let me know if you change your mind."

#Update Thread/Loop
  
    def FullUpdate(self, leaf):
        if self.Updating: return
        try:
            self.Updating = True
            self.RequestUpdate(leaf, True)
            self.SetLastUpdate(leaf)
        except:
            traceback.print_exc()
            #self.Error = True
            self.LastUpdated = datetime.utcnow()
            print("Error while performing Full Update")
        finally:
            self.Updating = False

    def SetLastUpdate(self, leaf):
        self.LastUpdate = leaf.get_latest_battery_status()
        self.LastUpdated = datetime.utcnow()
        self.LastSuccess = datetime.utcnow()
        utils.PrintTimed("Status Updated")

    def UpdateLoop(self, leaf, updateFreq, checkFreq):
        utils.PrintTimed("Starting update loop...")
        self.FullUpdate(leaf)
        while not self.Error:
            if (datetime.utcnow() - self.LastUpdated).total_seconds() > 60*updateFreq:
                self.FullUpdate(leaf)
            sleep(60*checkFreq)

    def StartUpdateLoop(self, leaf):
        _thread.start_new_thread(self.UpdateLoop, (leaf, 60, 1))
        #start a thread that periodically updates the status
        #updates every 60 minutes, checks if it should updated every minute
