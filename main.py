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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'



# loading config files
CONFIG = json.loads(open(PATH + 'config.json', 'r', encoding='utf-8').read())
LANG   = json.loads(open(PATH + 'lang/' + CONFIG['Lang'] + '.json', 'r', encoding='utf-8').read())
# def save_config
def save_config():
	with open(PATH + 'config.json', 'w', encoding='utf-8') as f:
		f.write(json.dumps(CONFIG, indent=4))


# messege lock
MESSAGE_LOCK = False
message_list = json.loads(open(PATH + 'data.json', 'r', encoding='utf-8').read())
# def save_data
def save_data():
	global MESSAGE_LOCK
	while MESSAGE_LOCK:
		time.sleep(0.1)
	MESSAGE_LOCK = True
	with open(PATH + 'data.json', 'w', encoding='utf-8') as f:
		f.write(json.dumps(message_list))
	MESSAGE_LOCK = False


# preference lock
PREFERENCE_LOCK = False
preference_list = json.loads(open(PATH + 'preference.json', 'r', encoding='utf-8').read())
# def save_preference
def save_preference():
	global PREFERENCE_LOCK
	while PREFERENCE_LOCK:
		time.sleep(0.1)
	PREFERENCE_LOCK = True
	with open(PATH + 'preference.json', 'w', encoding='utf-8') as f:
		f.write(json.dumps(preference_list))
	PREFERENCE_LOCK = False


# def init_user
def init_user(user):
	global preference_list
	if not preference_list.__contains__(str(user.id)):
		preference_list[str(user.id)] = {}

		# /receipt_switch
		preference_list[str(user.id)]['receipt'] = True

		# /say and /done
		preference_list[str(user.id)]['conversation'] = False

		# /block and /unblock
		preference_list[str(user.id)]['blacklist'] = False
		##create 'blacklist' for old json data
		if not 'blacklist' in preference_list[str(user.id)]:
			preference_list[str(user.id)]['blacklist'] = False

		preference_list[str(user.id)]['name'] = user.full_name
		threading.Thread(target=save_preference).start()
		return
	if preference_list[str(user.id)]['name'] != user.full_name:
		preference_list[str(user.id)]['name'] = user.full_name
		threading.Thread(target=save_preference).start()


# def messege handled
def process_msg(bot, update):
	global message_list
	init_user(update.message.from_user)
	if CONFIG['Admin'] == 0:
		bot.send_message(chat_id=update.message.from_user.id, text=LANG['please_setup_first'])
		return
	if update.message.from_user.id == CONFIG['Admin']:
		if update.message.reply_to_message:
			if message_list.__contains__(str(update.message.reply_to_message.message_id)):
				sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
				try:
					if update.message.audio:
						bot.send_audio(chat_id=sender_id, audio=update.message.audio, caption=update.message.caption)
					elif update.message.document:
						bot.send_document(chat_id=sender_id, document=update.message.document, caption=update.message.caption)
					elif update.message.voice:
						bot.send_voice(chat_id=sender_id, voice=update.message.voice, caption=update.message.caption)
					elif update.message.video:
						bot.send_video(chat_id=sender_id, video=update.message.video, caption=update.message.caption)
					elif update.message.sticker:
						bot.send_sticker(chat_id=sender_id, sticker=update.message.sticker)
					elif update.message.photo:
						bot.send_photo(chat_id=sender_id, photo=update.message.photo[0], caption=update.message.caption)
					elif update.message.text_markdown:
						bot.send_message(chat_id=sender_id, text=update.message.text_markdown, parse_mode=telegram.ParseMode.MARKDOWN)
					else:
						bot.send_message(chat_id=CONFIG['Admin'], text=LANG['reply_type_not_supported'])
						return
				except Exception as e:
					if e.message == "Forbidden: bot was blocked by the user.":
						bot.send_message(chat_id=CONFIG['Admin'], text=LANG['blocked_alert'])
					else:
						bot.send_message(chat_id=CONFIG['Admin'], text=LANG['reply_message_failed'])
					return
				if preference_list[str(update.message.from_user.id)]['receipt']:
					bot.send_message(chat_id=update.message.chat_id, text=LANG['reply_message_sent'] % (preference_list[str(sender_id)]['name'], str(sender_id)), parse_mode=telegram.ParseMode.MARKDOWN)
			else:
				bot.send_message(chat_id=CONFIG['Admin'], text=LANG['reply_to_message_no_data'])
		else:
			bot.send_message(chat_id=CONFIG['Admin'], text=LANG['reply_to_no_message'])
	else:
		# only when 'conversation' is true
		if preference_list[str(update.message.from_user.id)]['conversation'] :
			# forward messege to me
			msg_forward_to_me = bot.forward_message(chat_id=CONFIG['Admin'], from_chat_id=update.message.chat_id, message_id=update.message.message_id)
			# add user-info output to me when content is sticker or photo.
			if msg_forward_to_me.sticker :
			bot.send_message(chat_id=CONFIG['Admin'], text=LANG['info_data'] % (update.message.from_user.full_name, str(update.message.from_user.id)), parse_mode=telegram.ParseMode.MARKDOWN, reply_to_message_id=msg_forward_to_me.message_id)
			# receipt to the sender
			if preference_list[str(update.message.from_user.id)]['receipt']:
				bot.send_message(chat_id=update.message.from_user.id, text=LANG['message_received_receipt'])
			message_list[str(msg_forward_to_me.message_id)] = {}
			message_list[str(msg_forward_to_me.message_id)]['sender_id'] = update.message.from_user.id
			# save_data
			threading.Thread(target=save_data).start()
		# when conversation is false
		else:
			# the sender should run /say
			bot.send_message(chat_id=update.message.from_user.id, text=LANG['warning_start_conversation'])
	pass


# def bot command
def process_command(bot, update):
	# init user
	init_user(update.message.from_user)
	# load global 'CONFIG'
	global CONFIG
	# load global 'preference_list'
	global preference_list
	# define 'bot command'
	command = update.message.text[1:].replace(CONFIG['Username'], '').lower().split()

	if not preference_list[str(update.message.from_user.id)]['blacklist'] :
		# bot directives independent to 'conversation' :
		##bot start
		if command[0] == 'start' :
			bot.send_message(chat_id=update.message.chat_id, text=LANG['start'])
			return
		##start conversation
		elif command[0] == 'say' :
			preference_list[str(update.message.from_user.id)]['conversation'] = True
			bot.send_message(chat_id=update.message.chat_id, text=LANG['notify_conversation_start'])
		##end conversation
		elif command[0] == 'done' :
			preference_list[str(update.message.from_user.id)]['conversation'] = False
			bot.send_message(chat_id=update.message.chat_id, text=LANG['notify_conversation_end'])
		##messege-info you point
		elif command[0] == 'messege_info' :
			if (update.message.from_user.id == CONFIG['Admin']) and (update.message.chat_id == CONFIG['Admin']):
				if update.message.reply_to_message:
					if message_list.__contains__(str(update.message.reply_to_message.message_id)):
						sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
						bot.send_message(chat_id=update.message.chat_id, text=LANG['info_data'] % (preference_list[str(sender_id)]['name'], str(sender_id)), parse_mode=telegram.ParseMode.MARKDOWN)
					else:
						bot.send_message(chat_id=update.message.chat_id, text=LANG['reply_to_message_no_data'])
			else:
				bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_admin_only'])
		##blacklist function to block user
		elif command[0] == 'block' :
			if (update.message.from_user.id == CONFIG['Admin']) and (update.message.chat_id == CONFIG['Admin']):
				if update.message.reply_to_message:
					if message_list.__contains__(str(update.message.reply_to_message.message_id)):
						preference_list[str(update.message.from_user.id)]['blacklist'] = True
						bot.send_message(chat_id=update.message.chat_id, text=LANG['operation_block'])
					else:
						bot.send_message(chat_id=update.message.chat_id, text=LANG['reply_to_message_no_data'])
			else:
				bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_admin_only'])
		##blacklist function to unblock user
		elif command[0] == 'unblock' :
			if (update.message.from_user.id == CONFIG['Admin']) and (update.message.chat_id == CONFIG['Admin']):
				if update.message.reply_to_message:
					if message_list.__contains__(str(update.message.reply_to_message.message_id)):
						preference_list[str(update.message.from_user.id)]['blacklist'] = False
						bot.send_message(chat_id=update.message.chat_id, text=LANG['operation_unblock'])
					else:
						bot.send_message(chat_id=update.message.chat_id, text=LANG['reply_to_message_no_data'])
			else:
				bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_admin_only'])
		# only when 'conversation' false, can operate other bot directives, as to make /done useful
		elif not preference_list[str(update.message.from_user.id)]['conversation'] :
			##receipt switch
			if command[0] == 'receipt_switch' :
				preference_list[str(update.message.from_user.id)]['receipt'] = (preference_list[str(update.message.from_user.id)]['receipt'] == False)
				threading.Thread(target=save_preference).start()
				if preference_list[str(update.message.from_user.id)]['receipt']:
					bot.send_message(chat_id=update.message.chat_id, text=LANG['receipt_on'])
				else:
					bot.send_message(chat_id=update.message.chat_id, text=LANG['receipt_off'])
			##bot version
			elif command[0] == 'version' :
				bot.send_message(chat_id=update.message.chat_id, text='Telegram PM Bot to concatnate your conversation between the bot and the sender.\n\nhttps://github.com/NewBugger/telegram-pm-bot')
			else:
				##when received not existed command
				bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_command_notfound'])
		# ask user to /done
		else:
			bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_end_conversation'])
	else:
		bot.send_message(chat_id=update.message.chat_id, text=LANG['warning_blocked'])



# define name 'updaterf'
updaterf = telegram.ext.Updater(token=CONFIG['Token'])

# handle defined
dispatcherf = updaterf.dispatcher
# receive command
dispatcherf.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command & telegram.ext.Filters.private, process_command))
# receive messege
dispatcherf.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.all & telegram.ext.Filters.private & (~ telegram.ext.Filters.command) & (~ telegram.ext.Filters.status_update), process_msg))

# generate user-info
mef = updaterf.bot.get_me()
CONFIG['ID'] = mef.id
CONFIG['Username'] = '@' + mef.username
# print user-info in server
print("Starting... (ID: {0}, Username: {1})".format(CONFIG['ID'], CONFIG['Username']))

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# To start the bot, run
##polling query for the tg center periodically
updaterf.start_polling()
print("Started")

# you probably want to stop the Bot by pressing Ctrl+C or sending a signal to the Bot process
updaterf.idle()
print("Stopping...")
save_data()
save_preference()
print("Data Saved.")
print("Stopped.")
