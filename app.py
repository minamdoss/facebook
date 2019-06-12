#Python libraries that we need to import for our bot
import random
from flask import Flask, request
from pymessenger.bot import Bot
import pyodbc as db
import io
import json
import re
# import pandas as pd
# import snips_nlu_en
from snips_nlu import SnipsNLUEngine, load_resources
from snips_nlu.default_configs import CONFIG_EN
# from googletrans import Translator

from DBConnection import Database
from DB_Interaction import interaction

import os

app = Flask(__name__)
ACCESS_TOKEN = 'EAAGGGCVi2rcBALuP2tFhFnyWbu10RF7CHWpFwfvfyeZC1hfzpR1N9ZAShQqgeqDPZCGFk1o3POMCnDtVXaByFJlV46K1TT1saiuGel70cpeqPTbpIF033DQgSPoozDA9zjZARZAJ9CbUfXrXFeHIKZCmroNKfAtFDCcKZBmcGh0UwZDZD'
VERIFY_TOKEN = 'VERIFY_TOKEN'
bot = Bot(ACCESS_TOKEN)

# dbconn = db.connect("Driver={SQL SERVER};Server=tcp:madyfa.database.windows.net,1433;Database=CBT;User Id={mohamed};Password={3Oss199755};Encrypt=True;Trusted_Connection=yes;")
# dbconn = db.connect("Driver={ODBC Driver 13 for SQL Server};Server=tcp:madyfa.database.windows.net,1433;Database=CBT;Uid=mohamed@madyfa;Pwd={3Oss199755};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")

#We will receive messages that Facebook sends our bot at this endpoint
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    response_sent_text = get_message()
                    nlu.setQuery(message['message'].get('text'),recipient_id)
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = get_message()
                    # send_message(recipient_id, response_sent_nontext)
                    nlu.setQuery(message['message'].get('attachments'),recipient_id)
    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


#chooses a random message to send to the user
def get_message():
    sample_responses = ["You are stunning!", "We're proud of you.", "Keep on being you!", "We're greatful to know you :)"]
    # return selected item to the user
    return random.choice(sample_responses)

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

class NLU:
    __connection = Database()
    __interaction = interaction()
    __answers = {
            "NA": "Please Ask your department administrator for this"
        }
    # def __Translate_Text (question,x='en'):
    #     translator = Translator()
    #     translated = translator.        translate(question , dest=x)
    #     print("Source Language : " + translated.src)
    #     print("Destination Language : " + translated.dest)
    #     print("Origin Text : " + translated.origin)
    #     print("Translated Text : " + translated.text)
    #     return translated.text

    def __int__(self):
        self._query = ''
        self.__result = ''
        self._intent = ''
        self._probability = 0
        self._slots = {}
        self.__engine=''
        self.__dataset=''
        self.__nluSlots=''
        self.language=''
        self.UserID=''

    def EngineMode(self, mode):
        """
        Saving the engine to use the model for every question (Training Part)
        or Use the model if it already exists (Testing Part)

        :param mode: Test or Train string
        :return:  Fitted Engine
        """


        if mode =="Train":
            load_resources('snips_nlu_en')

            self.__engine = SnipsNLUEngine(config=CONFIG_EN)
            with io.open("dataset.json") as f:
               self.__dataset = json.load(f)

            self.__engine.fit(self.__dataset)

            #UnComment to save the model
            #self.__engine.persist("Z:\FCIS-ASU\Semester 8\ChatbotModel")

        elif mode =="Test":
            with io.open("dataset.json") as f:
               self.__dataset = json.load(f)
            self.__engine = SnipsNLUEngine.from_path("Z:\FCIS-ASU\Semester 8\ChatbotModel")



    def setQuery(self, query , user):
        # self._query , self.language = query
        self._query  = query
        self.UserID = user
        self.__excute()
        self.answer()



    def __excute(self):
        parsing = self.__engine.parse(self._query)
        self.__result = json.loads(json.dumps(parsing,indent=2))
        print( self.__result )

    def _getIntent(self):
        try:
            self._intent = self.__result['intent']['intentName']
            return self._intent
        except Exception as e:
            return 'None'


    def _getProbability(self):
        self._probability = self.__result['intent']['probability']
        return self._probability

    #need Handling Exception
    def _getSlots(self):
        dic = {}
        if len(self.__result['slots']) != 0:
            for x in range(len(self.__result['slots'])):
                if not re.search("Val",self.__result['slots'][x]['entity']):
                    if str(self.__result['slots'][x]['entity']).__contains__("snips"):
                        dic[self.__result['slots'][x]['slotName']] = self.__result['slots'][x]['value']['value']
                    else:
                        dic[self.__result['slots'][x]['entity']] = self.__result['slots'][x]['value']['value']
        else:
            return "No Slots"

        self._slots = dic
        return self._slots


    def checkIntent(self):
        if self._getIntent() == 'None':
            self.__interaction.UnAnsweredFactory().__noIntent_insert__(self._query)
            return False
        else:
            return True


    def answer(self):
        """
             Check if the question has intent or None

        :return: Answer
        """


        if self.checkIntent():
            # if str(self.CheckJsonEntities()).__contains__("Has No Entities"):
            #     print("Chatbot : Get Answer From Json Answers")
            # else:
                self.return_original()
        else:
            send_message(self.UserID,"not available due to intent")
            # print('ChatBot : not available due to intent')

    def checkSlots(self):
        self.__nluSlots = self._getSlots()
        if str(self.__nluSlots).__contains__("No Slots") :
            return "No"
        datasetSlots = []
        for i in range(len(self.__dataset['intents'][self._getIntent()]['utterances'])):
            for j in range(len(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'])):
                check = json.dumps(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'][j])
                if 'entity' in check:
                    if str(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'][j]['entity']).__contains__("snips"):
                        datasetSlots.append(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'][j]['slot_name'])
                    else:
                        datasetSlots.append(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'][j]['entity'])
                    datasetSlots = list(dict.fromkeys(datasetSlots))
        for x in datasetSlots:
            if 'Val' in x:
                datasetSlots.remove(x)
        ret = []
        for i in range(len(datasetSlots)):
            found = False
            for j in self.__nluSlots.keys():
                if datasetSlots[i] == j:
                    found = True
                    break
            if not found:
                ret.append(datasetSlots[i])
        print("Slots Not Available in Question : ", ret)  # el mafroud btalla3 el slots ely mesh mwgooda
        return ret


    def askForunenteredEntities(self):
        slots_needed = self._getSlots()
        # print(slots_needed)
        slots_missing = self.checkSlots()
        if str(slots_missing).__contains__("No"):
            return
        loopflagi = True
        # print(temp3[1]);
        for i in range(len(slots_missing)):
            loopflagi = False
            while not loopflagi:

                chatbotques = "Please Enter "+slots_missing[i]
                # g = Translator().translate(chatbotques , dest = self.language).text
                # print("Chatbot: ",g)
                send_message(self.UserID,chatbotques)
                # print ("Chatbot : ",chatbotques)
                if slots_missing[i] == "ID":
                    try:
                        reply = int(input("User: "))
                    except:
                        print("Chatbot: Please Enter a valid ID")
                        continue
                else:
                    values=[]
                    # print("Chatbot: Possible Values for", slots_missing[i], "are:")
                    for k in range(len(self.__dataset['entities'][slots_missing[i]]['data'])):
                            values.append(self.__dataset['entities'][slots_missing[i]]['data'][k]['value'])
                    # print(values)
                    send_message(self.UserID , values)
                    reply = input("User: ")

                if reply == 'q':
                    break
                if str(slots_missing[i]).__contains__("ID"):
                    self.__nluSlots[slots_missing[i]] = reply
                    break
                for j in range(len(self.__dataset['entities'][slots_missing[i]]['data'])):
                    try:
                        check = json.dumps(self.__dataset['entities'][slots_missing[i]]['data'][j])
                        # print(check)
                    except:
                        continue
                    if reply in check:
                        # e3ml 7aga
                        self.__nluSlots[slots_missing[i]] = reply
                        loopflagi = True
                        break
        return self.__nluSlots

    def return_original(self):
        slots_needed = self.askForunenteredEntities()
        if slots_needed is None:
            self.__interaction.UnAnsweredFactory().__noIntent_insert__(self._query)
            send_message(self.UserID , "I don't have answer for this")
            # print("ChatBot : I don't have answer for this")
            return

        key_list = list(slots_needed.keys())

        # print(key_list)
        finaldic = dict()
        for key in range(len(key_list)):
            # print(key_list[key] + "here")
            # print(slots_needed[key_list[key]])
            # do something
            if key_list[key] == "ID":
                continue
            # print("Key :",key_list[key])

            try:
                for i in range(len(self.__dataset['entities'][key_list[key]]["data"])):
                    check = json.dumps(self.__dataset['entities'][key_list[key]]["data"][i])
                    if slots_needed[key_list[key]] in check:
                        self.__nluSlots[key_list[key]] = self.__dataset['entities'][key_list[key]]["data"][i]["value"]
                        # print(self.__dataset['entities'][key_list[key]]["data"][i]["value"])
            except:
                print("Error")
        send_message(self.UserID , "Done")
        # print("Values to get from Database" , self.__nluSlots)  # original values of entities used in question
        # return List or dictionary??



    # def CheckJsonEntities(self):
    #      for i in range(len(self.__dataset['intents'][self._getIntent()]['utterances'])):
    #             for j in range(len(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'])):
    #                 check = json.dumps(self.__dataset['intents'][self._getIntent()]['utterances'][i]['data'][j])
    #                 # print(check)
    #                 if 'entity' in check:
    #                     # print("Entities")
    #                     return "Has Entities"
    #
    #             # print("-----------")
    #      # print("Exit with No Entities")
    #      if self._getProbability() >= 0.5:
    #          return "Has No Entities"
    #      else:
    #          return "Has Entities"

nlu = NLU()
nlu.EngineMode("Train")
if __name__ == "__main__":
    app.run()
