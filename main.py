#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import json
import telegram.ext
import telegram
import datetime
import os
import logging
import threading

logging.basicConfig(level=logging.INFO,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
					)

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

CONFIG = json.loads(open(PATH + 'config.json', 'r').read())

LANG = json.loads(open(PATH + 'lang/' + CONFIG['Lang'] + '.json').read())

MESSAGE_LOCK = False

message_list = json.loads(open(PATH + 'data.json', 'r').read())

PREFERENCE_LOCK = False

preference_list = json.loads(open(PATH + 'preference.json','r').read())

def save_data():
	global MESSAGE_LOCK
	while MESSAGE_LOCK:
		time.sleep(0.05)
	MESSAGE_LOCK = True
	with open(PATH + 'data.json', 'w') as f:
		f.write(json.dumps(message_list))
	MESSAGE_LOCK = False

def save_preference():
	global PREFERENCE_LOCK
	while PREFERENCE_LOCK:
		time.sleep(0.05)
	PREFERENCE_LOCK = True
	with open(PATH + 'preference.json', 'w') as f:
		f.write(json.dumps(preference_list))
	PREFERENCE_LOCK = False

def save_config():
	with open(PATH + 'config.json', 'w') as f:
		f.write(json.dumps(CONFIG, indent=4))

def init_user(user):
	global preference_list
	if not preference_list.__contains__(str(user.id)):
		preference_list[str(user.id)]={}
		preference_list[str(user.id)]['receipt']=True
		preference_list[str(user.id)]['conversation']=False
		preference_list[str(user.id)]['name']=user.full_name
		threading.Thread(target=save_preference).start()
		return
	if preference_list[str(user.id)]['name']!=user.full_name:
		preference_list[str(user.id)]['name']=user.full_name
		threading.Thread(target=save_preference).start()

updater = telegram.ext.Updater(token=CONFIG['Token'])
dispatcher = updater.dispatcher

me = updater.bot.get_me()
CONFIG['ID'] = me.id
CONFIG['Username'] = '@' + me.username

print('Starting... (ID: {0}, Username: {1})'.format(CONFIG['ID'],CONFIG['Username']))

def process_msg(bot, update):
	global message_list
	init_user(update.message.from_user)
	if CONFIG['Admin'] == 0:
		bot.send_message(chat_id=update.message.from_user.id,text=LANG['please_setup_first'])
		return
	if update.message.from_user.id == CONFIG['Admin']:
		if update.message.reply_to_message != None:
			if message_list.__contains__(str(update.message.reply_to_message.message_id)):
				sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
				try:
					if update.message.audio != None:
						bot.send_audio(chat_id=sender_id,audio=update.message.audio, caption=update.message.caption)
					elif update.message.document != None:
						bot.send_document(chat_id=sender_id,document=update.message.document,caption=update.message.caption)
					elif update.message.voice != None:
						bot.send_voice(chat_id=sender_id,voice=update.message.voice, caption=update.message.caption)
					elif update.message.video != None:
						bot.send_video(chat_id=sender_id,video=update.message.video, caption=update.message.caption)
					elif update.message.sticker != None:
						bot.send_sticker(chat_id=sender_id, sticker=update.message.sticker)
					elif update.message.photo != None:
						bot.send_photo(chat_id=sender_id,photo=update.message.photo[0], caption=update.message.caption)
					elif update.message.text_markdown != None:
						bot.send_message(chat_id=sender_id,text=update.message.text_markdown,parse_mode=telegram.ParseMode.MARKDOWN)
					else:
						bot.send_message(chat_id=CONFIG['Admin'],text=LANG['reply_type_not_supported'])
						return
				except Exception as e:
					if e.message == "Forbidden: Bot was blocked by the user.":
						bot.send_message(chat_id=CONFIG['Admin'],text=LANG['blocked_alert'])
					else:
						bot.send_message(chat_id=CONFIG['Admin'],text=LANG['reply_message_failed'])
					return
				if preference_list[str(update.message.from_user.id)]['receipt']:
					bot.send_message(chat_id=update.message.chat_id,text=LANG['reply_message_sent'] % (preference_list[str(sender_id)]['name'],str(sender_id)),parse_mode=telegram.ParseMode.MARKDOWN)
			else:
				bot.send_message(chat_id=CONFIG['Admin'],text=LANG['reply_to_message_no_data'])
		else:
			bot.send_message(chat_id=CONFIG['Admin'],text=LANG['reply_to_no_message'])
	else:
		# only when conversation is true
		if preference_list[str(update.message.from_user.id)]['conversation']:
			# forward messege to me
			forward_msg_to_me = bot.forward_message(chat_id=CONFIG['Admin'], from_chat_id=update.message.chat_id, message_id=update.message.message_id)
			# add user-info output to me when content is sticker or photo.
			if update.message.sticker != None or update.message.photo != None :
				bot.send_message(chat_id=update.message.chat_id,text=LANG['info_data'] % (preference_list[str(sender_id)]['name'],str(sender_id)),parse_mode=telegram.ParseMode.MARKDOWN)

			# receipt to the sender
			if preference_list[str(update.message.from_user.id)]['receipt']:
				bot.send_message(chat_id=update.message.from_user.id,text=LANG['message_received_receipt'])
			message_list[str(forward_msg_to_me.message_id)]={}
			message_list[str(forward_msg_to_me.message_id)]['sender_id']=update.message.from_user.id

			# save_data
			threading.Thread(target=save_data).start()

		# when conversation is false
		else:
			# the sender should run /say
			bot.send_message(chat_id=update.message.from_user.id, text=LANG['warning_switch_say'])
	pass


def process_command(bot, update):
	init_user(update.message.from_user)
	global CONFIG
	command = update.message.text[1:].replace(CONFIG['Username'], '').lower().split()
	if command[0] == 'start':
		bot.send_message(chat_id=update.message.chat_id,
						 text=LANG['start'])
		return
	elif command[0] == 'version':
		bot.send_message(chat_id=update.message.chat_id,
						 text='Telegram PM Bot to concatnate your conversation between the bot and the sender.\n'
						 + 'https://github.com/NewBugger/telegram-pm-bot'
						 )
		return
	elif command[0] == 'set_admin':
		if CONFIG['Admin']==0:
			CONFIG['Admin']=int(update.message.from_user.id)
			save_config()
			bot.send_message(chat_id=update.message.chat_id,text=LANG['set_admin_successful'])
		else:
			bot.send_message(chat_id=update.message.chat_id,text=LANG['set_admin_failed'])
		return
	elif command[0] == 'receipt_switch':
		global preference_list
		preference_list[str(update.message.from_user.id)]['receipt']=(preference_list[str(update.message.from_user.id)]['receipt'] == False)
		threading.Thread(target=save_preference).start()
		if preference_list[str(update.message.from_user.id)]['receipt']:
			bot.send_message(chat_id=update.message.chat_id,text=LANG['receipt_on'])
		else:
			bot.send_message(chat_id=update.message.chat_id,text=LANG['receipt_off'])
	elif command[0] == 'messege_info':
		if (update.message.from_user.id == CONFIG['Admin']) and (update.message.chat_id == CONFIG['Admin']):
			if update.message.reply_to_message != None:
				if message_list.__contains__(str(update.message.reply_to_message.message_id)):
					sender_id=message_list[str(update.message.reply_to_message.message_id)]['sender_id']
					bot.send_message(chat_id=update.message.chat_id,text=LANG['info_data'] % (preference_list[str(sender_id)]['name'],str(sender_id)),parse_mode=telegram.ParseMode.MARKDOWN)
				else:
					bot.send_message(chat_id=update.message.chat_id,text=LANG['reply_to_message_no_data'])
	# start conversation
	elif command[0] == 'say':
		global preference_list
		preference_list[str(update.message.from_user.id)]['conversation'] = True
	# end conversation
	elif command[0] == 'done':
		global preference_list
		preference_list[str(update.message.from_user.id)]['conversation'] = False

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.all & telegram.ext.Filters.private & (~ telegram.ext.Filters.command) & (~ telegram.ext.Filters.status_update), process_msg))

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command & telegram.ext.Filters.private,
												   process_command))

updater.start_polling()
print('Started')
updater.idle()
print('Stopping...')
save_data()
save_preference()
print('Data Saved.')
print('Stopped.')
