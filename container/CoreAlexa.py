#!/usr/bin/python
import utils
import Leaf


from flask import Flask, make_response, render_template, request
import logging
import json
import sys
import traceback

from OpenSSL import SSL

#Statics
LEAF = None

context = ('certificate.pem', 'private-key.pem')
app = Flask(__name__)
CONTENT_TYPE = {'Content-Type': 'application/json;charset=UTF-8'}


@app.route('/', methods=['GET'])
def get():
    if (LEAF != None): return LEAF.GetStatsForDisplay()
    return "LEAF processor is not ready"

@app.route('/', methods=['POST'])
def post():
    logging.info(json.dumps(request.json, indent=4, sort_keys=False))
    finalResponse = None
    try:
        intent = request.json["request"]["intent"]['name']
    except:
        finalResponse = utils.return_speech("Error while determining intent.")
        return finalResponse, 200, CONTENT_TYPE

    logging.info("Intent: %s" % intent)
    utils.PrintTimed("Intent: {0}".format(intent))

    finalResponse = ProcessRequest(intent, request)

    #utils.PrintTimed(speech)
    #response = utils.generate_response(output_speech=speech)

    logging.info(json.dumps(json.loads(finalResponse), indent=4, sort_keys=False))
    return finalResponse, 200, CONTENT_TYPE

def ProcessRequest(intent, request):
    response = None
    speech = "No handler found for the intent "+intent
    #Have the LEAF try to process the request
    handler = intent.split('_')[0]
    if (handler == "LEAF"):
        if (LEAF.Ready() or intent == "LEAF_UpdateStatus"): response = LEAF.ProcessIntent(intent, request)
        else: speech = "Sorry, LEAF is not ready to handle requests."
    if (handler == "SERVER"):
        speech = "The server says hello!"
    
    if (response == None):
        response = utils.return_speech(speech)
    return response

#if __name__== '__main__':
#logging.getLogger().setLevel(10)
LEAF = Leaf.LeafHandler()
app.run(host='0.0.0.0', ssl_context=context, port=443)
