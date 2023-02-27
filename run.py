# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 14:10:00 2023

@author: Renato Henz

Telegram Chatbot server

"""

# Main dependencies
import mysql.connector, logging, os
from datetime import datetime

# Opus package
import opus

# Package to work with emojis
from emoji import emojize

# Tasks scheduler
from apscheduler.schedulers.background import BackgroundScheduler

# Telegram chatbot modules
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler, CallbackQueryHandler, messagequeue
from telegram.utils.request import Request

# Setting up the '.env' file with environment variables
from dotenv import load_dotenv
load_dotenv('.env')

# Defining the scheduler
scheduler = BackgroundScheduler()

# General data
saint_of_the_day = {
    'subtitle': '',
    'img_url': None,
}
daily_meditation = ''
admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
current_liturgical_season = ''

# Enabling logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chat handlers states
SERVICES, PRAYERS, MYSTERIES = range(3)

# Bot subclass that delegates the sending method to the message queue (Message Queue)
# Reference: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits
class MessageQueueBot(Bot):
    # Init method
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        # Initializer
        super(MessageQueueBot, self).__init__(*args, **kwargs)
        # Two attributes must be provided for decorator
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or messagequeue.MessageQueue()

    # Finish method
    def __del__(self):
        # Stopping the message queue
        try: self._msg_queue.stop()
        except: pass

    # Queued messages sending decorator
    @messagequeue.queuedmessage
    def send_message(self, *args, **kwargs):
        # 'Encapsulated' method would accept new optional arguments 'queued' and 'isgroup'
        return super(MessageQueueBot, self).send_message(*args, **kwargs)

# Start message with bot
def start(update, context):
    # Getting the user name
    from_ = update.message.from_user.first_name
    if (update.message.from_user.last_name is not None):
        from_ += f" {update.message.from_user.last_name}"
    # Custom welcome message
    welcome_mesage = "Olá, " + from_ + "!\n" + opus.start()
    update.message.reply_text(welcome_mesage)
    
    # Saving user data, in order to enable services, etc
    register_user(
        update.message.from_user.id,
        update.message.from_user.first_name,
        update.message.from_user.is_bot,
        update.message.from_user.last_name,
        update.message.from_user.language_code,
    )
    
    # Finally, we inform the admin about the new user
    bot.send_message(
        chat_id=admin_chat_id,
        text=f'Novo usuário começou a usar o Bot!\nNome: <b>{from_}</b>\nChat ID: <b>{update.message.from_user.id}</b>',
        parse_mode='html',
    )

# Function to provide help message
def help(update, context):
    update.message.reply_text(opus.show_help())
    
# Function to request the developer's contact
def contact(update, context):
    # Defining message to be sent
    contact_message = emojize(
        f'Em caso de dúvidas ou para enviar sugestões, favor entrar em contato com esse cara aqui embaixo :point_down:\nhttps://t.me/{os.getenv("ADMIN_CHAT_USERNAME")}', 
        language='alias',
    )
    update.message.reply_text(contact_message)
    
# Function to send a broadcast message for all the bot users
def broadcast(update, context):
    # Checking if message was sent by the admin
    if (update.message.chat_id == admin_chat_id):
        # Getting list of users to receive the message
        for user in get_users():
            print ("Chat ID: {}, Nome: {}".format(user['chat_id'], user['name']))
            # Formatting message to include user name (if required) and remove "#BROADCAST: " prefix
            broadcast_message = update.message.text.replace("#BROADCAST: ", "")
            broadcast_message = broadcast_message.replace("[USER]", user['name'])
            # Finally, we send the message to the user
            bot.send_message(
                chat_id=user['chat_id'],
                text=broadcast_message,
                parse_mode='html',
            )
            print (f"Mensagem enviada para o usuário {user['name']} ({user['chat_id']})")
    # Otherwise, we inform about the error
    else:
        update.message.reply_text(
            'Erro: Somente o administrador pode enviar mensagens via broadcast pelo bot.',
            parse_mode='html',
        )

# Function to list users (admin only)
def list_users(update, context):
    # Checking if it was requested by the admin
    if (update.message.chat_id == admin_chat_id):
        users_message = 'Lista de usuários do Bot:\n\n<b>Nome</b> (Chat ID)\n'
        users = get_users()
        for user in users:
            users_message += f"<b>{user['name']}</b> ({user['chat_id']})\n"
        # Finally, we add the total count and send the message
        users_message += f'\nTotal de Usuários: <b>{str(len(users))}</b>'
        update.message.reply_text(users_message, parse_mode='html')
    # Otherwise
    else:
        update.message.reply_text(
            'Erro: Somente o administrador tem acesso a essa função.', 
            parse_mode='html',
        )

# Function to list users count for each service (admin only)
def list_services(update, context):
    # Checking if it was requested by the admin
    if (update.message.chat_id == admin_chat_id):
        count_message = 'Quantidade de Usuários por Serviço:\n\n'
        counts = get_user_services_count()
        for count in counts:
            count_message += f"<b>{counts[count]} - {count}</b>\n"
        # Finally, we add the total count and send the message
        count_message += f'\nTotal de Serviços em Uso: <b>{str(sum(counts.values()))}</b>'
        update.message.reply_text(count_message, parse_mode='html')
    # Otherwise
    else:
        update.message.reply_text(
            'Erro: Somente o administrador tem acesso a essa função.', 
            parse_mode='html',
        )

# Function to send a random aspiration
def send_aspiration(update=None, context=None, chat_id=None):
    # Responding to messages
    if (update is not None):
        update.message.reply_text(
            f'"<i>{opus.get_aspiration(id=None, tag=None)}</i>"', 
            parse_mode='html',
        )
    # Scheduled services
    elif (chat_id is not None):
        bot.send_message(
            chat_id=chat_id, 
            text=f'"<i>{opus.get_aspiration(id=None, tag=None)}</i>"', 
            parse_mode='html',
        )

# Function to send the Rosary to the user
def send_rosary(update=None, context=None, chat_id=None):
    # Getting daily Rosary and the chat ID
    rosary = opus.get_rosary()
    chat_id = update.message.chat_id
    
    # Informing about the mysteries
    if (update is not None):
        # Initial message
        message = opus.format_date(datetime.today()) + '\n'
        message += f"<b>Rosário: <i>Mistérios {rosary['name']}</i></b> :prayer_beads:\n\n"
        message += f"Para ouvir a recitação dos mistérios: {rosary['link_audio']}"
        message = emojize(message, language='alias')
        # Sending message with disabled web page preview
        update.message.reply_text(
            message, 
            parse_mode='html', 
            disable_web_page_preview=True,
        )
    
    # Sending mysteries images, names and descriptions
    for i in range (1, 6):
        message = f"{str(i)}º Mistério {rosary['name'][:-1]}\n"
        message += f"\"<b><i>{rosary['misterios'][str(i)]['nome']}</i></b>\"\n\n"
        message += f"<i>{rosary['misterios'][str(i)]['descricao']}</i>"
        bot.send_photo(
            chat_id=chat_id, 
            photo=rosary['misterios'][str(i)]['img_path'], 
            caption=message, 
            parse_mode='html',
        )
    
    # Sending the final prayer
    bot.send_message(
        chat_id=chat_id, 
        text= f"\"<i>{rosary['final_prayer']}</i>\"", 
        parse_mode='html',
    )
    # Sending the Litany of Our Lady
    message = '<b>Ladainha de Nossa Senhora</b>\n'
    message += f"Para ouvir a recitação da Ladainha de Nossa Senhora: {rosary['litany']['link_audio']}\n\n"
    message += rosary['litany']['oracao']
    # Sending message with disabled web page preview
    bot.send_message(
        chat_id=chat_id, 
        text=message, 
        parse_mode='html', 
        disable_web_page_preview=True,
    )
    # Finally, we send the Hail Holy Queen prayer
    bot.send_message(
        chat_id=chat_id, 
        text= f"\"<i>{rosary['hail_holy_queen']}</i>\"", 
        parse_mode='html',
    )

# Function to start aspirations
def register_aspiration(update, context):
    if (scheduler.get_job('registra_jaculatoria_' + str(update.callback_query.message.chat_id)) is None):
        scheduler.add_job(
            send_aspiration, 'cron', hour="10,16,20", minute="30", 
            id='registra_jaculatoria_' + str(update.callback_query.message.chat_id), 
            kwargs={'chat_id': update.callback_query.message.chat_id},
        )
        update.callback_query.edit_message_text(emojize(':white_check_mark: Serviço de envio de jaculatórias registrado, serão enviadas automaticamente 3 vezes ao dia.', language='alias'))
        # Saving on the database
        register_service(
            'jaculatoria', 
            update.callback_query.message.chat_id, 
        )
    # If it's already registered
    else: update.callback_query.edit_message_text('Serviço já registrado.')

# Function to stop aspirations
def stop_aspiration(update, context):
    if (scheduler.get_job('registra_jaculatoria_' + str(update.callback_query.message.chat_id))):
        scheduler.remove_job('registra_jaculatoria_' + str(update.callback_query.message.chat_id))
        update.callback_query.edit_message_text(emojize(':x: Serviço de envio de jaculatórias interrompido.', language='alias'))
        # Removing from database
        remove_service(
            'jaculatoria', 
            update.callback_query.message.chat_id,
        )

# Function to send the Saint of the Day
def send_saint(update=None, context=None, chat_id=None):
    caption = saint_of_the_day['subtitle']
    photo = saint_of_the_day['img_url']
    # Responding to messages
    if (update is not None):
        update.message.reply_photo(
            photo=photo, 
            caption=caption, 
            parse_mode='html',
        )
    # Scheduled services
    elif (chat_id is not None):
        bot.send_photo(
            chat_id=chat_id, 
            photo=photo, 
            caption=caption, 
            parse_mode='html',
        )

# Function to start Saint of the Day
def register_saint(update, context):
    if (scheduler.get_job('registra_santo_' + str(update.callback_query.message.chat_id)) is None):
        scheduler.add_job(
            send_saint, 'cron', hour="8", 
            id='registra_santo_' + str(update.callback_query.message.chat_id), 
            kwargs={'chat_id': update.callback_query.message.chat_id},
        )
        update.callback_query.edit_message_text(emojize(':white_check_mark: Serviço de envio de Santo do Dia registrado, será enviado automaticamente 1 vez ao dia.', language='alias'))
        # Saving on the database
        register_service(
            'santo', 
            update.callback_query.message.chat_id, 
        )
    # If it's already registered
    else: update.callback_query.edit_message_text('Serviço já registrado.')

# Function to stop Saint of the Day
def stop_saint(update, context):
    if (scheduler.get_job('registra_santo_' + str(update.callback_query.message.chat_id))):
        scheduler.remove_job('registra_santo_' + str(update.callback_query.message.chat_id))
        update.callback_query.edit_message_text(emojize(':x: Serviço de envio do Santo do Dia interrompido.', language='alias'))
        # Removing from database
        remove_service(
            'santo', 
            update.callback_query.message.chat_id,
        )

# Function to send the daily meditation
def send_meditation(update=None, context=None, chat_id=None):
    # Responding to messages
    if (update is not None):
        # We disable the web page preview, to use less space
        update.message.reply_text(
            daily_meditation, 
            parse_mode='html', 
            disable_web_page_preview=True
        )
    # Scheduled services
    elif (chat_id is not None):
        # We disable the web page preview, to use less space
        bot.send_message(
            chat_id=chat_id, 
            text=daily_meditation, 
            parse_mode='html', 
            disable_web_page_preview=True
        )
    
# Function to start daily meditation
def register_meditation(update, context):
    if (scheduler.get_job('registra_meditacao_' + str(update.callback_query.message.chat_id)) is None):
        scheduler.add_job(
            send_meditation, 'cron', hour="5", minute="5", 
            id='registra_meditacao_' + str(update.callback_query.message.chat_id), 
            kwargs={'chat_id': update.callback_query.message.chat_id},
        )
        update.callback_query.edit_message_text(emojize(
            ':white_check_mark: Serviço de envio de Meditação Diária registrado, será enviada automaticamente 1 vez ao dia.',
            language='alias',
        ))
        # Saving on the database
        register_service(
            'meditacao', 
            update.callback_query.message.chat_id, 
        )
    # If it's already registered
    else: update.callback_query.edit_message_text('Serviço já registrado.')

# Function to stop daily meditation
def stop_meditation(update, context):
    if (scheduler.get_job('registra_meditacao_' + str(update.callback_query.message.chat_id))):
        scheduler.remove_job('registra_meditacao_' + str(update.callback_query.message.chat_id))
        update.callback_query.edit_message_text(emojize(':x: Serviço de envio de Meditação Diária interrompido.', language='alias'))
        # Removing from database
        remove_service(
            'meditacao', 
            update.callback_query.message.chat_id,
        )
    
# Function to send Angelus/Regina Caeli
def send_angelus_regina_caeli(update=None, context=None, chat_id=None):
    caption, photo = opus.angelus_regina_caeli(liturgical_season=current_liturgical_season)
    # Responding to messages
    if (update is not None):
        update.message.reply_photo(
            photo=photo,
            caption=caption,
        )
    # Scheduled services
    elif (chat_id is not None):
        bot.send_photo(
            chat_id=chat_id, 
            photo=photo, 
            caption=caption,
        )

# Function to start Angelus/Regina Caeli
def register_angelus_regina_caeli(update, context):
    if (scheduler.get_job('registra_angelus_regina_caeli_' + str(update.callback_query.message.chat_id)) is None):
        scheduler.add_job(
            send_angelus_regina_caeli, 'cron', hour="12", 
            id='registra_angelus_regina_caeli_' + str(update.callback_query.message.chat_id), 
            kwargs={'chat_id': update.callback_query.message.chat_id}
        )
        update.callback_query.edit_message_text(emojize(
            ':white_check_mark: Serviço de envio de Angelus/Regina Caeli registrado, será enviado automaticamente todo dia às 12h.',
            language='alias',
        ))
        # Saving on the database
        register_service(
            'angelus_regina_caeli', 
            update.callback_query.message.chat_id,
        )
    # If it's already registered
    else: update.callback_query.edit_message_text('Serviço já registrado.')

# Function to stop Angelus/Regina Caeli
def stop_angelus_regina_caeli(update, context):
    if (scheduler.get_job('registra_angelus_regina_caeli_' + str(update.callback_query.message.chat_id))):
        scheduler.remove_job('registra_angelus_regina_caeli_' + str(update.callback_query.message.chat_id))
        update.callback_query.edit_message_text(emojize(':x: Serviço de envio do Angelus/Regina Caeli interrompido.', language='alias'))
        # Removing from database
        remove_service(
            'angelus_regina_caeli', 
            update.callback_query.message.chat_id,
        )
    
# Function to show available services
def show_services(update, context):
    # Checking user enabled services
    # For aspirations
    if (scheduler.get_job('registra_jaculatoria_' + str(update.message.chat_id)) is None):
        button1 = emojize(':white_check_mark: Registrar Jaculatórias', language='alias')
        callback1 = 'registrar_jaculatoria'
    else:
        button1 = emojize(':x: Parar Jaculatórias', language='alias')
        callback1 = 'parar_jaculatoria'
    # For the Saint of the Day
    if (scheduler.get_job('registra_santo_' + str(update.message.chat_id)) is None):
        button2 = emojize(':white_check_mark: Registrar Santo do Dia', language='alias')
        callback2 = 'registrar_santo'
    else:
        button2 = emojize(':x: Parar Santo do Dia', language='alias')
        callback2 = 'parar_santo'
    # For daily meditation
    if (scheduler.get_job('registra_meditacao_' + str(update.message.chat_id)) is None):
        button3 = emojize(':white_check_mark: Registrar Meditação Diária', language='alias')
        callback3 = 'registrar_meditacao'
    else:
        button3 = emojize(':x: Parar Meditação Diária', language='alias')
        callback3 = 'parar_meditacao'
    # For Angelus/Regina Caeli
    if (scheduler.get_job('registra_angelus_regina_caeli_' + str(update.message.chat_id)) is None):
        button4 = emojize(':white_check_mark: Registrar Angelus/Regina Caeli', language='alias')
        callback4 = 'registrar_angelus_regina_caeli'
    else:
        button4 = emojize(':x: Parar Angelus/Regina Caeli', language='alias')
        callback4 = 'parar_angelus_regina_caeli'

    # Defining buttons to be shown
    keyboard = [
        [
            InlineKeyboardButton(button1, callback_data=callback1),
            InlineKeyboardButton(button2, callback_data=callback2)
        ],
        [InlineKeyboardButton(button3, callback_data=callback3)],
        [InlineKeyboardButton(button4, callback_data=callback4)]
    ]
    # Formatting buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Replying to message with created buttons
    update.message.reply_text('Serviços disponíveis:', reply_markup=reply_markup)
    return SERVICES

# Function to select a service
def select_service(update, context):
    # Getting clicked button data
    query = update.callback_query
    # For each command, we'll call the appropriate function
    # Registering services
    if (query.data == "registrar_jaculatoria"):
        register_aspiration(update, context)
    elif (query.data == "registrar_santo"):
        register_saint(update, context)
    elif (query.data == "registrar_meditacao"):
        register_meditation(update, context)
    elif (query.data == "registrar_angelus_regina_caeli"):
        register_angelus_regina_caeli(update, context)
    # Registrando servicos
    elif (query.data == "parar_jaculatoria"):
        stop_aspiration(update, context)
    elif (query.data == "parar_santo"):
        stop_saint(update, context)
    elif (query.data == "parar_meditacao"):
        stop_meditation(update, context)
    elif (query.data == "parar_angelus_regina_caeli"):
        stop_angelus_regina_caeli(update, context)
    # We could update the message button here
    #query.edit_message_text(text="Serviço selecionado")
    # Ending the conversation
    return ConversationHandler.END

# Function to show available prayers
def show_prayers(update, context):
    # Defining buttons to be shown
    keyboard = [
        [InlineKeyboardButton("Cântico dos Três Jovens", callback_data='cantico_tres_jovens')],
        [InlineKeyboardButton("Lembrai-vos", callback_data='lembrai-vos')],
        [
            InlineKeyboardButton("Ato de Contrição", callback_data='ato_contricao'),
            InlineKeyboardButton("Alternativo", callback_data='ato_contricao_alt')
        ],
        [
            InlineKeyboardButton("Oferecimento do Dia", callback_data='oferecimento_dia'),
            InlineKeyboardButton("Alternativo", callback_data='oferecimento_dia_alt')
        ],
        [InlineKeyboardButton("Ação de Graças Noite", callback_data='acao_gracas')],
        [InlineKeyboardButton("Intenção para ganhar indulgências", callback_data='intencao_indulgencias')],
        [
            InlineKeyboardButton("Salmo 2", callback_data='salmo_2'),
            InlineKeyboardButton("Adoro-te Devote", callback_data='adoro-te_devote')
        ],
    ]
    # Admin will also have access to other options
    if update.message.chat_id == admin_chat_id:
        keyboard.append(
            [InlineKeyboardButton("Preces", callback_data='preces')]
        )
    # Formatting buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Replying to message with created buttons
    update.message.reply_text('Orações Disponíveis:', reply_markup=reply_markup)
    return PRAYERS

# Function to send a selected prayer
def send_prayer(update, context):
    # Getting clicked button data
    query = update.callback_query
    # Answering with appropriate prayer and ending conversation
    query.edit_message_text(
        text=opus.prayers[query.data],
        parse_mode='html',
    )
    return ConversationHandler.END

# Function to show available mysteries
def show_rosary_mysteries(update, context):
    # Defining buttons to be shown
    keyboard = [
        [InlineKeyboardButton("Mistérios Gozosos", callback_data='gozosos')],
        [InlineKeyboardButton("Mistérios Dolorosos", callback_data='dolorosos')],
        [InlineKeyboardButton("Mistérios Gloriosos", callback_data='gloriosos')],
        [InlineKeyboardButton("Mistérios Luminosos", callback_data='luminosos')],
    ]
    # Formatting buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Replying to message with created buttons
    update.message.reply_text('Escolha os mistérios:', reply_markup=reply_markup)
    return MYSTERIES

# Function to send the selected Rosary mysteries
def send_rosary_mysteries(update, context):
    # Getting clicked button data
    query = update.callback_query
    # Querying the mysteries
    mysteries = opus.get_rosary(mysteries_type=query['data'])
    
    # Setting initial message to be sent
    message = f"<b>Rosário: <i>Mistérios {mysteries['name']}</i></b> :prayer_beads:\n\n"
    message = emojize(message, language='alias')
    query.edit_message_text(message, parse_mode='html')
    
    # Sending messages with mysteries and corresponding images
    for i in range (1, 6):
        message = f"{str(i)}º Mistério {mysteries['name'][:-1]}\n"
        message += f"\"<b><i>{mysteries['misterios'][str(i)]['nome']}'</i></b>\"\n\n"
        message += f"<i>{mysteries['misterios'][str(i)]['descricao']}</i>"
        bot.send_photo(
            chat_id=query['message']['chat']['id'],
            photo=mysteries['misterios'][str(i)]['img_path'],
            caption=message,
            parse_mode='html'
        )
    # Ending current conversation
    return ConversationHandler.END

# Function to handle received files
def file_handler(update, context):
    update.message.reply_text(emojize(
        'Nenhuma mensagem de texto recebida. :white_check_mark:',
        language='alias',
    ))

# Function to answer messages in a generic way
def echo(update, context):
    update.message.reply_text(emojize(
        'Comando não reconhecido :white_check_mark:',
        language='alias',
    ))

# Function to parse a message and respond accordingly
def parse_message(update, context):
    # If it's a broadcast message, we call the broadcast hanlder
    if "#BROADCAST: " in update.message.text:
        broadcast(update, context)
    # Otherwise, we send a default message
    else: echo(update, context)

# Cancel current conversation
def cancel(update, context):
    # Getting user data
    user = update.message.from_user
    logger.info("Usuario %s cancelou a conversa.", user.first_name)
    # Answering to the command
    update.message.reply_text(
        'Operação cancelada.',
        # Removing any avilable custom keyboard
        reply_markup=ReplyKeyboardRemove()
    )
    # Ending corrent conversation
    return ConversationHandler.END

# Aux function to get Saint of the day
def request_saint_of_the_day():
    global saint_of_the_day
    saint_of_the_day['subtitle'], saint_of_the_day['img_url'] = opus.get_saint_of_the_day()

# Aux function to get daily meditation
def request_daily_meditation():
    global daily_meditation
    daily_meditation = opus.get_daily_meditation()

# Aux function to get litrugical season from current date
def request_liturgical_season():
    global current_liturgical_season
    current_liturgical_season = opus.get_liturgical_season()

# Function to log errors
def error(update, context):
    # Updates errors log
    logger.warning('Atualização "%s" causou o erro "%s"', update, context.error)

# Function to schedule registered services when bot is started
def schedule_services():
    # Loading saved services
    services_list = load_services()
    
    # For each service, we'll schedule it
    for service in services_list:
        # Schedulling corresponding task
        if service['service_type'] == 'santo':
            scheduler.add_job(
                send_saint, 'cron', hour="8", 
                id=f"registra_santo_{service['chat_id']}",
                kwargs={'chat_id': service['chat_id']},
            )
        elif service['service_type'] == 'jaculatoria':
            scheduler.add_job(
                send_aspiration, 'cron', hour="10,16,20", minute="30", 
                id=f"registra_jaculatoria_{service['chat_id']}",
                kwargs={'chat_id': service['chat_id']},
            )
        elif service['service_type'] == 'meditacao':
            scheduler.add_job(
                send_meditation, 'cron', hour="5", minute="5", 
                id=f"registra_meditacao_{service['chat_id']}",
                kwargs={'chat_id': service['chat_id']},
            )
        elif service['service_type'] == 'angelus_regina_caeli':
            scheduler.add_job(
                send_angelus_regina_caeli, 'cron', hour="12", 
                id=f"registra_angelus_regina_caeli_{service['chat_id']}",
                kwargs={'chat_id': service['chat_id']},
            )

# Function to register a new user
def register_user(chat_id, first_name, is_bot, last_name, language_code):
    # Inserting data
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        # If no last name waas provided, we'll set as an empty string
        if (last_name is None): last_name = ''
        query = f"""
        INSERT INTO users (chat_id, first_name, is_bot, last_name, language_code)
        VALUES ('{chat_id}', '{first_name}', {is_bot}, '{last_name}', '{language_code}')
        ON DUPLICATE KEY UPDATE
            `chat_id` = '{chat_id}',
            `first_name` = '{first_name}',
            `is_bot` = {is_bot},
            `last_name` = '{last_name}',
            `language_code` = '{language_code}';
        """
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        # Comitting changes
        connection.commit()
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")

# Function to register a service to an user
def register_service(service_type, chat_id):
    # Inserting data
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        query = f"""
        INSERT INTO user_services (chat_id, service_type)
        VALUES ('{chat_id}', '{service_type}')
        ON DUPLICATE KEY UPDATE
            `chat_id` = '{chat_id}',
            `service_type` = '{service_type}';
        """
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        # Comitting query
        connection.commit()
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")

# Function to remove a service from an user
def remove_service(service_type, chat_id):
    # Removing data
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        query = f"""
        DELETE FROM user_services
    	WHERE chat_id = '{chat_id}' AND service_type = '{service_type}';
        """
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        # Comitting query
        connection.commit()
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")

# Function to load registered services
def load_services():
    # Creating services list
    services_list = []

    # Quering data
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        query = "SELECT * FROM user_services;"
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            # Appending item to the list
            services_list.append({
                "chat_id": row[0], 
                "service_type": row[1], 
            })
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")
    
    # Returning data
    return services_list

# Function to load registered users
def get_users():
    # Creating users list
    users_list = []

    # Quering data
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        query = """
            SELECT chat_id, IF(last_name != "", CONCAT(first_name, " ", last_name), first_name) AS "name"
            FROM users
            ORDER BY name;
        """
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            # Appending user to the list
            users_list.append({
                "chat_id": row[0], 
                "name": row[1],
            })
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")
    
    # Returning data
    return users_list

# Function to load number of users for each service
def get_user_services_count():
    # Initializing dict with data
    user_services_count = {}
    # Connecting to the database
    try:
        connection = mysql.connector.connect(**opus.get_mysql_connection_config_dict())
        # Creating query to get data
        query = """
            SELECT service_type AS 'service_code', COUNT(*) AS 'users_count'
            FROM user_services
            GROUP BY service_type;
        """
        
        # Executing query
        cursor = connection.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            user_services_count[row[0]] = row[1]
    
    # If any error occurs
    except mysql.connector.Error as error:
        print(f"There was an error while querying the MySQL server: {error}")
    
    # In the end
    finally:
        # Close connection
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")
    
    # Returning data
    return user_services_count

# Main script function
def main():
    # Starting scheduled tasks
    scheduler.start()
    
    # Getting saint of the day, daily meditation and current liturgical season
    request_saint_of_the_day()
    request_daily_meditation()
    request_liturgical_season()
    
    # Defining daily tasks to request the Saint of the day, the daily meditation and liturgical season
    scheduler.add_job(
        request_saint_of_the_day,
        'cron', hour="7", minute="50",
        id='request_saint_of_the_day',
    )
    scheduler.add_job(
        request_daily_meditation,
        'cron', hour="4", minute="45",
        id='request_daily_meditation',
    )
    scheduler.add_job(
        request_liturgical_season,
        'cron', hour="9", minute="15",
        id='request_liturgical_season',
    )
    
    # Scheduling services saved on database
    schedule_services()
    
    # Global output limits (messages/ms): min - 30 messages/1000 ms
    # Creating messages queue
    q = messagequeue.MessageQueue(all_burst_limit=30, all_time_limit_ms=1000)
    
    # Setting bot's pool connections size (https://github.com/python-telegram-bot/python-telegram-bot/issues/787)
    request = Request(con_pool_size=8)
    
    # Creating bot and messages queue
    global bot
    bot = MessageQueueBot(
        token=os.getenv('TOKEN'), 
        request=request, 
        mqueue=q
    )
    
    # Creating updater from bot token and dispatcher to register handlers
    # 'use_context=True' allows new context based callbacks
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher

    # Adding handlers to the bot
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ajuda", help))
    dp.add_handler(CommandHandler("contato", contact))
    dp.add_handler(CommandHandler("terco", send_rosary))
    dp.add_handler(CommandHandler("jaculatoria", send_aspiration))
    dp.add_handler(CommandHandler("santo", send_saint))
    dp.add_handler(CommandHandler("meditacao_diaria", send_meditation))
    dp.add_handler(CommandHandler("angelus_regina_caeli", send_angelus_regina_caeli))
    # Admin handlers
    dp.add_handler(CommandHandler("lista_usuarios", list_users))
    dp.add_handler(CommandHandler("lista_servicos", list_services))
    
    # Conversation handlers for different services
    conv_handler = ConversationHandler(
        # Defining handlers entry points
        entry_points=[CommandHandler('oracoes', show_prayers),
                      CommandHandler('registrar_servicos', show_services),
                      CommandHandler('rosario', show_rosary_mysteries)],
        # Defining handlers states
        states={SERVICES: [CallbackQueryHandler(select_service)],
                PRAYERS: [CallbackQueryHandler(send_prayer)],
                MYSTERIES: [CallbackQueryHandler(send_rosary_mysteries)]},
        # If user wants to cancel the conversation
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Adding conversation handler to the dispatcher
    dp.add_handler(conv_handler)
    
    # For media messages
    dp.add_handler(MessageHandler(
        Filters.video | 
        Filters.photo | 
        Filters.document | 
        Filters.sticker | 
        Filters.voice | 
        Filters.audio, 
        file_handler
    ))
    # For default text messages (no commands provided), we parse and return
    dp.add_handler(MessageHandler(
        Filters.text, 
        parse_message
    ))

    # Logging all errors
    dp.add_error_handler(error)

    # Starting the bot
    updater.start_polling()

    # Running bot until it receives a 'Ctrl+C' command or a signal like 'SIGINT', 'SIGTERM' or 'SIGABRT'
    # 'start_polling()' is non-blocking, so we use it
    updater.idle()

# Executing main script
if __name__ == '__main__':
    main()
