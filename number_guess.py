import os, sys
from random import randrange
import boto3

def lambda_handler(event, context):
    try:
        #FORCED TO HAVE PROGRAM FLOW witih Try & Catch BECAUSE OF A GLITCH IN AMAZON ECHO DEVICE vs Alexa Service Simulator
        try:
            response_session_attributes = event["session"]["attributes"]
        except:
            response_session_attributes = {'debug':'problem'}
            
        is_playing = get_session_value(event,'playing')
        is_game_over = get_session_value(event,'game_over')
        is_playing = int(is_playing) if is_playing is not None else 0
        is_game_over = int(is_game_over) if is_game_over is not None else 0
        
        one_second_break = '<break time="1000ms"/>'
        half_second_break = '<break time="500ms"/>'
  
        # s3 = boto3.client("s3")
        
        #AUDIO FILES#
        audio_1 = ('bd_countdown','1_game_bd_countdown_48k.mp3','https://a.clyp.it/hzvpcfai.mp3')
        audio_2 = ('bd_intro','2_game_bd_intro_48k.mp3','https://a.clyp.it/berksyah.mp3')
        audio_3 = ('bd_win_1','3_game_bd_win1_48k.mp3','https://a.clyp.it/dmno3wxu.mp3')
        audio_4 = ('bd_hard','4_game_bd_hard_48k.mp3','https://a.clyp.it/itskfkr3.mp3')
        audio_5 = ('bd_medium','5_game_bd_medium_48k.mp3','https://a.clyp.it/hmmoie01.mp3')
        audio_6 = ('bd_win_2','6_game_bd_win_48k.mp3','https://a.clyp.it/1eozk1qj.mp3')
        audio_7 = ('bd_instructions','7_game_bd_instructions_48k.mp3','https://a.clyp.it/sstiscoz.mp3')
        audio_8 = ('bd_easy','8_game_bd_easy_48k.mp3','https://a.clyp.it/2dw3nt21.mp3')
        audio_9 = ('bd_lose','9_game_bd_lose_48k.mp3','https://a.clyp.it/odikfqdd.mp3')
        #END AUDIO FILES#
        
        
        #PLAY AGAIN#
        #
        #   Note: Reason for a state design pattern is for things just like this!
        #
        
        #END PLAY AGAIN#

        if event["request"]["type"] == "LaunchRequest":
            response_session_attributes['playing'] = 0
            return build_ssml_response(generate_audio_tag(audio_2[2]), 0, response_session_attributes)
        elif event["request"]["type"] == "IntentRequest":
            intent_name = event["request"]["intent"]["name"]
            #SATISFIES #2 of Amazon requirements (2017-03-23)
            if intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
                return build_ssml_response('Thank you for using Bomb Defuse. See you next time!', 1)
            #menu
            if is_playing == 0:
                #choose level section
                if intent_name == "ChooseLevelIntent":
                    if is_playing == 1:
                        return build_ssml_response("You are already playing", 0, response_session_attributes)
                    chosen_level = get_slot_value(event,'level')
                    tries_left = 0
                    
                    if chosen_level is not False:
                        if chosen_level == 'easy':
                            tries_left = 10
                            response = generate_audio_tag(audio_8[2])+ one_second_break
                        elif chosen_level == 'medium':
                            tries_left = 9
                            response = generate_audio_tag(audio_5[2])+ one_second_break
                        elif chosen_level == 'hard':
                            tries_left = 8
                            response = generate_audio_tag(audio_4[2])+ one_second_break
                        elif chosen_level == 'testing':
                            tries_left = 1
                            response = "testing" + one_second_break
                        else:
                            return build_ssml_response("Please Choose Level between Easy, Medium or Hard", 0, response_session_attributes)
                    #this is where the game really starts. It starts when level is chosen (so far)
                    response_session_attributes['tries_left'] = tries_left
                    response_session_attributes['playing'] = 1
                    maximum_number = 1000
                    response_session_attributes['maximum_number'] = maximum_number
                    response_session_attributes['correct_number'] = randrange(1,maximum_number + 1)
                    response += "Guess a number between 1 and 1000. You have %s chances" % tries_left
                    return build_ssml_response(response, 0,response_session_attributes)
                else:
                    return build_ssml_response("Please choose level among Easy, Medium or Hard!", 0,response_session_attributes)
            #we are currently playing now
            elif is_playing == 1:
                #power up section
                if intent_name == "PowerUpIntent":
                    maximum_number = get_session_value(event,'maximum_number')
                    chosen_powerup = get_slot_value(event,'powerup_type')
                    if chosen_powerup is not False:
                        if chosen_powerup == 'yellow':
                            maximum_number -= 10
                        if chosen_powerup == 'blue':
                            maximum_number -= 50
                        if chosen_powerup == 'red':
                            maximum_number -= 100
                        if chosen_powerup == 'ultimate':
                            maximum_number -= 500
                        response_session_attributes['maximum_number'] = maximum_number
                        #the "correct number" changes when there is a powerup
                        response_session_attributes['correct_number'] = randrange(1,maximum_number + 1)
                    response = "%s %s" % (maximum_number, chosen_powerup)
                    return build_ssml_response(response, 0, response_session_attributes)
                elif intent_name == "TryIntent":
                    correct_number = get_session_value(event,'correct_number')
                    correct_number = int(correct_number) if correct_number is not None else -1
                    tries_left = get_session_value(event,'tries_left')
                    chosen_number = int(get_slot_value(event,'chosen_number'))
                    #between 1 and 1000?
                    if int(chosen_number) >= 0 and int(chosen_number) <= 1000:
                        tries_left -= 1
                        word = "tries" if tries_left != 1 else "try"
                        response_session_attributes['tries_left'] = tries_left
                    else:
                        return build_ssml_response("You said %s. Please pick a number between 1 and 1000" % chosen_number,0,response_session_attributes)
                    
                    if int(correct_number) == int(chosen_number):
                        response = generate_audio_tag(audio_6[2])+ half_second_break + "Do you want to play again?"
                        card_text = "Congratulations! You won! The correct number was %s" % correct_number
                        response_session_attributes['game_over'] = 1
                        return build_ssml_response(response,0,response_session_attributes, card_text=card_text)
                    elif int(tries_left) <= 0:
                        response = generate_audio_tag(audio_9[2])+ "The correct number is %s" % correct_number + half_second_break + "Do you want to play again?"
                        card_text = "Game over. The correct number was %s" % correct_number
                        response_session_attributes['game_over'] = 1
                        return build_ssml_response(response,0,response_session_attributes, card_text=card_text)
                    elif int(correct_number) > int(chosen_number):
                        response = "Higher. You have %s %s left." % (tries_left,word)
                        #response = "%s is incorrect. Guess a higher number. You have %s %s left" % (chosen_number,tries_left,word)
                        #debug
                        # response = "Guess a higher number. You have %s %s left. Hint: %s" % (tries_left,word,correct_number)
                        return build_ssml_response(response,0,response_session_attributes)
                    elif int(correct_number) < int(chosen_number):
                        response = "Lower. You have %s %s left." % (tries_left,word)
                        #response = "%s is incorrect. Guess a lower number. You have %s %s left" % (chosen_number,tries_left,word)
                        return build_ssml_response(response,0,response_session_attributes)
                    else:
                        return build_ssml_response("Unknown Error",0,response_session_attributes)
                elif intent_name == "PlayAgainIntent" and is_game_over == 1:
                    chosen_play_again_yn = get_slot_value(event,'play_again')
                    if chosen_play_again_yn == 'yes':
                        response_session_attributes['playing'] = 0
                        response_session_attributes['game_over'] = 0
                        return build_ssml_response("Choose A Level Between Easy, Medium, or Hard",0,response_session_attributes)
                    elif chosen_play_again_yn == 'no':
                        return build_ssml_response("Thank You For playing Bomb Defuse",1,response_session_attributes)
                    else:
                        return build_ssml_response("Unknown Error",0,response_session_attributes, card_text="PlayAgainIntent called")
                else:
                     return build_ssml_response(intent + ' I did not understand. Can you say it again?', 0,response_session_attributes)
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        card_text = str(exc_type) + ' ' + str(fname) + ' ' + str(exc_tb.tb_lineno)
        response_session_attributes['card_text'] = card_text
        return build_ssml_response("I did not understand you. Can you please say it again?",0,response_session_attributes)

def generate_audio_tag(url):
    #
    #url = 'https://s3.amazonaws.com/alexagamefilesbucket/' + filename
    #
    #IF PRIVATE
    #
    # url = s3.generate_presigned_url('get_object', Params = {'Bucket': 'alexagamefilesbucket', 'Key': filename}, ExpiresIn = 3600)
    # url = url.replace("&","%26")
    return '<audio src="%s"/>' % url

def put_in_audio_tag(url):
    return '<audio src="%s"/>' % url

def get_session_value(event,key):
    try:
        value = event.get('session').get('attributes').get(key)
        return value
    except TypeError:
        return False
    except:
        return False

def get_slot_value(event,key):
    try:
        attribute = event.get('request').get('intent').get('slots').get(key).get('value')
        return attribute
    except TypeError:
        return False
    except:
        return False

def build_ssml_response(speech_output, should_end_session, session_attributes = {}, **kwargs):
    response = {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml":"<speak>" + str(speech_output)[:7999] + "</speak>"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "SSML",
                    "ssml": "<speak>" + str(speech_output)[:7999] + "</speak>"
                }
            },
            "shouldEndSession": should_end_session
        }
    }
    #if problem playing on amazon echo device
    try:
        if kwargs['card_text'] is not False:
            response['response']['card'] = {"type": "Simple", "title": 'Defuse', "content": kwargs['card_text']}
    #except is GOOD in this case & normal
    except:
        pass
    return response
