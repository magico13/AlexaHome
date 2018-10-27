import json
from datetime import datetime

class BaseApp():
    def ProcessIntent(self, intent, request):
        return ""
    
    def Ready(self):
        return True
        
#Response Generation
def return_speech(speech):
    text = build_speech(speech)
    body = {}
    body['outputSpeech'] = build_speech(speech)
    return generate_response(body)

def continue_dialog():
    message = {}
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return generate_response(message, should_end_session=False)
    
#Utility
def PrintTimed(toPrint):
    print("{0} - {1}".format(datetime.now(), toPrint))
    
#Internal use
def generate_response(message, session_attributes={}, should_end_session=True):
    response = {}
    #speechlet['card'] = build_SimpleCard(title, body)
    response['shouldEndSession'] = should_end_session
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    '''response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": output_speech
			},
            "shouldEndSession": should_end_session
        }
    }'''
    return json.dumps(response)

def build_speech(body):
    speech = {}
    speech['type'] = 'PlainText'
    speech['text'] = body
    return speech
