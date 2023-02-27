# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 18:40:00 2023

@author: Renato Henz

Functions to get Opus data amongst others

"""

# Main dependencies
import mysql.connector, json, requests
import os
from datetime import datetime
from random import randint

# Package to parse HTML pages
from bs4 import BeautifulSoup

# Package to work with emojis
from emoji import emojize

# AWS S3 communication
import boto3

# Setting up the '.env' file with environment variables
from dotenv import load_dotenv
load_dotenv('.env')

# Aspirations class
class Aspiration():
    # Init func
    def __init__(self, id, text, tags=None):
        self.id = id
        self.text = text
        # Tags list
        self.tags = tags

# Function to get list of objects from the S3 bucket
def get_s3_bucket_keys():
    # Initializing S3 instance and getting bucket object
    s3 = session.resource('s3')
    bucket = s3.Bucket(os.getenv('AWS_BUCKET'))
    # Getting the files URLs from specified bucket
    bucket_objects = []
    for bucket_object in bucket.objects.all():
        bucket_objects.append(img_path_base + bucket_object.key)
    
    # Returning resulting list
    return bucket_objects

# Function to get prayers and data from DynamoDN table
def get_dynamodb_table_prayers():
    # Initializing DynamoDB instance and getting table
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('opus-bot')
    scan = table.scan()
    # Getting prayers formatted as dict
    prayers = {
        item['field']: item['value'] for item in scan['Items']
    }
    
    # Returning resulting dict
    return prayers

# Function to format a complete date (pt-br)
def format_date(date):
    WEEK_DAYS = {
            '0': 'Domingo',
            '1': 'Segunda-feira',
            '2': 'Terça-feira',
            '3': 'Quarta-feira',
            '4': 'Quinta-feira',
            '5': 'Sexta-feira',
            '6': 'Sábado'}
    MONTHS = {
            '01': 'Janeiro',
            '02': 'Fevereiro',
            '03': 'Março',
            '04': 'Abril',
            '05': 'Maio',
            '06': 'Junho',
            '07': 'Julho',
            '08': 'Agosto',
            '09': 'Setembro',
            '10': 'Outubro',
            '11': 'Novembro',
            '12': 'Dezembro'
            }

    # Formatting date and returning
    return WEEK_DAYS[date.strftime("%w")] + ", " + date.strftime("%d") + " de " + \
                        MONTHS[date.strftime("%m")] + " de " + date.strftime("%Y")

# Function to read MySQL credentials from environment
def get_mysql_connection_config_dict():
    connection_config_dict = {
        'user': os.getenv('SQL_USER'),
        'password': os.getenv('SQL_PASS'),
        'host': os.getenv('SQL_HOST'),
        'database': os.getenv('SQL_DB'),
        'port': os.getenv('SQL_PORT'),
        'raise_on_warnings': True
        }
    return connection_config_dict

# Function to query aspirations from the database
def query_aspirations():
    # Trying to connect to MySQL server
    try:
        # Opening the connection
        connection = mysql.connector.connect(**connection_config_dict)
        # Creating query string
        mysql_query = "SELECT * FROM aspirations;"
        
        # Getting cursor and executing query
        cursor = connection.cursor()
        cursor.execute(mysql_query)
        # Reading the returned data and populating aspirations list
        for row in cursor.fetchall():
            aspirations.append(Aspiration(row[0], row[1], row[2]))
    
    # If an error occurs, we inform the user
    except mysql.connector.Error as error:
        print(f"Error while querying MySQL server: {error}")
    
    # Finally, we close the connection
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection to MySQL server has been closed")

# Function to start the chat
def start():
    # Setting welcome message to help the users
    welcome_message = emojize(u'Bem-vindo ao Opus Bot! :pray::sunglasses::call_me_hand:\n', language='alias')
    welcome_message += show_help()
    return welcome_message

# Function to show available commands for the bot
def show_help():
    # Defining list of commands and descriptions
    commands_list = {
        '/jaculatoria': 'Fornece uma jaculatória aleatória obtida do banco de dados',
        '/terco': 'Fornece os mistérios do terço do dia, junto a imagens de cada mistério e a Ladainha de Nossa Senhora ao final',
        '/rosario': 'Fornece os mistérios do terço especificados pelo usuário',
        '/santo': 'Obtém informações sobre o Santo do Dia a partir do site da Canção Nova',
        '/meditacao_diaria': 'Obtém informações sobre a Meditação Diária do site "Hablar con Dios"',
        '/angelus_regina_caeli': 'Fornece a oração do Angelus ou Regina Caeli (de acordo com o tempo litúrgico) junto a uma imagem de Nossa Senhora',
        '/oracoes': 'Apresenta uma lista de orações que podem ser enviadas pelo bot',
        '/registrar_servicos': 'Registre ou interrompa serviços como o envio de jaculatórias, Meditação Diária, Santo do Dia e Angelus/Regina Caeli',
        '/help ou /ajuda': 'Mostra a lista de comandos disponíveis',
        '/contato': 'Fornece o contato do desenvolvedor para dúvidas ou sugestões',
    }
    # Setting help message
    help_message = emojize(u'Abaixo estão as opções oferecidas por esse bot :point_down::point_down:\n\n', language='alias')
    # Appending commands to the message
    for command, description in commands_list.items():
        help_message += f"{command}: {description} ;\n"
    return help_message

# Function to retrieve an aspiration
def get_aspiration(id=None, tag=None):
    # If no specification was set, returns a random one
    if (id is None and tag is None):
        # Getting a random value
        index = randint(1, len(aspirations))
        return aspirations[index].text
    # If the aspiration ID was provided
    elif id:
        # Getting the aspiration by its ID
        aspiration = next((a for a in aspirations if a.id == id), None)
        return aspiration
    # If the tag was specified
    elif tag is not None:
        # Filtering aspirations which contain the selected tag
        f_aspirations = [a for a in aspirations if tag.lower() in a.tags.lower()]
        # Getting a random value
        index = randint(1, len(f_aspirations))
        return f_aspirations[index].text

# Function to retrieve the Saint of the Day info from 'Canção Nova' website
def get_saint_of_the_day():
    # URL for the Saint of the Day webpage
    page_url = 'https://santo.cancaonova.com/'
    
    # Initializing subtitle with formatted current date (https://stackabuse.com/how-to-format-dates-in-python/)
    subtitle = format_date(datetime.today())
    
    # Requesting the page and formatting with Beautiful Soup
    r = requests.get(page_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    #print(soup.prettify())
    
    # Looking for required instances from TAGs, classes IDs and other identifiers
    # Getting saint's name by TAG and partial class name
    saint_name = soup.select('h1[class="entry-title"]')[0].select('span')[0].text
    subtitle += f"\n\n<b>{saint_name}</b>"
    
    # If there's a brief introdution
    try:
        briefing = soup.select('h2[style*="text-align"]')[0].text
        if (briefing != ""): subtitle += f"\n\n<i>{briefing}</i>"
    # Otherwise, we just continue the script
    except: pass
    
    # Getting the introdution text about the Saint
    text = soup.select('p')[0].text
    subtitle += f"\n\n{text}"
    
    # Getting the image by TAG and partial class name
    img_element = soup.select('img[class*="wp-image"]')
    if len(img_element) == 0: img_element = soup.select('img[class*="alignleft"]')
    elif len(img_element) == 0: img_element = soup.select('img[class*="aligncenter')
    
    # If an image element was found
    if len(img_element) != 0:
        # We'll try to get the image URL
        try: img_url = img_element[0]['src']
        except: img_url = img_element[0]['src']
    # Otherwise, we just set it as None
    else: img_url = None
    
    # Finally, we define the link for the webpage
    subtitle += f"\n\nAcesse e saiba mais em: {page_url}"
    
    # Returning subtitle and image URL
    return subtitle, img_url

# Function to get data about daily meditation from the "Hablar con Dios" website
def get_daily_meditation():
    # URL for the webpage
    PAGE_URL = 'https://www.hablarcondios.org/pt/meditacaodiaria.aspx'
    
    # Requesting the page and formatting with Beautiful Soup
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    #print(soup.prettify())
    
    # Trying to get the liturgial date and check if page was correctly returned
    try: liturgical_day = soup.select('p[class="DiaLiturgico"]')[0].text
    # If it's not possible, we inform and return the link for the page
    except:
        print("Daily meditation: there was a problem while loading the page")
        return f"Não foi possível requisitar os dados via HTTP-GET devido a uma configuração de segurança do site. Favor acessar diretamente a página: {PAGE_URL}"
    
    # Initializing data to be returned
    meditation_data = f"<i>{liturgical_day}</i>"
    
    # Looking for required instances from TAGs, classes IDs and other identifiers
    # Getting title by TAG and class name
    meditation_title = soup.select('p[class="Titulo"]')[0].text
    meditation_data += f"\n\n<b>{meditation_title}</b>"

    # Getting subtitles by TAG and class name
    meditation_subtitle = soup.select('p[class="Subtitulo"]')
    meditation_data += f"\n\n<i>{meditation_subtitle[0].text}</i>"
    meditation_data += f"\n\n<i>{meditation_subtitle[1].text}</i>"
    meditation_data += f"\n\n<i>{meditation_subtitle[2].text}</i>"
    
    # Finally, we append the webpage link
    meditation_data += f"\n\nAcesse o texto completo em: {PAGE_URL}"
    
    # And the link for the Castbox podcast
    meditation_data += "\n\nOu a versão em áudio em:\nhttps://castbox.fm/va/1363038"
    
    # Returning the text
    return meditation_data

# Function to return the Angelus/Regina Caeli (during Easter) prayer and an image of Our Lady
def angelus_regina_caeli(prayer_type=None, liturgical_season=None):
    # Getting a random image of Our Lady
    file_path = get_image_path(image_type="nossa-senhora")
    
    # If no type was specified, we'll send according to the liturgical season
    if prayer_type is None:
        # If no liturgical season was provided, we'll get the current one
        if liturgical_season is None: liturgical_season = get_liturgical_season()
        # During Easter, we'll return the Regina Caeli
        if liturgical_season == 'easter': return prayers['regina_caeli'], file_path
        # On other seasons, we'll return the Angelus
        return prayers['angelus'], file_path
    # Otherwise, we return the specified prayer
    elif prayer_type == 'angelus': return prayers['angelus'], file_path
    elif prayer_type == 'regina_caeli': return prayers['regina_caeli'], file_path

# Function to get the Rosary mysteries of the day (or a specific one)
def get_rosary(mysteries_type=None):
    # If no mysteries were provided, we return the daily ones
    if mysteries_type is None:
        # Defining mysteries to be returned according to the weekday
        week_day = datetime.today().weekday()
        # * Glorious: wednesdays and sundays (2, 6);
        if week_day in [2, 6]: mysteries_type = 'gloriosos'
        # * Joyful: mondays and saturdays (0, 5);
        if week_day in [0, 5]: mysteries_type = 'gozosos'
        # * Sorrowful: tuesdays and fridays (1, 4);
        if week_day in [1, 4]: mysteries_type = 'dolorosos'
        # * Luminous: thursdays (3);
        if week_day in [3]: mysteries_type = 'luminosos'
    
    # Defining the mysteries path string
    if mysteries_type == 'gloriosos': mysteries_path_str = 'glorious'
    elif mysteries_type == 'gozosos': mysteries_path_str = 'joyful'
    elif mysteries_type == 'dolorosos': mysteries_path_str = 'sorrowful'
    elif mysteries_type == 'luminosos': mysteries_path_str = 'luminous'

    # Getting the required mysteries
    mysteries = rosary[mysteries_type]
    
    # Adding final prayer, Hail Holy Queen and litany
    mysteries['final_prayer'] = rosary['oracao_final']
    mysteries['hail_holy_queen'] = rosary['salve']
    mysteries['litany'] = rosary['ladainha']
    
    # Adding the mysteries name
    mysteries['name'] = mysteries_type.capitalize()
    
    # For each mystery, we'll get a random image
    for index in range(1, 6):
        # Defining the base path for the mysteries images
        rosary_img_path = rosary_img_path_base.\
            replace("[name]", mysteries_path_str).\
            replace("[number]", str(index))
        # Filtering the list of S3 bucket images
        filtered_img_list = [il for il in img_list if rosary_img_path in il]
        # Getting a random number to get the image
        value = randint(0, len(filtered_img_list)-1)
        # Getting the image URL for the mystery
        mysteries['misterios'][str(index)]['img_path'] = filtered_img_list[value]
    
    # Returning defined mysteries
    return mysteries

# Function to get an image from a category (directory) of available images
def get_image_path(image_type=None):
    # If an image type was provided, we'll include it on the file path
    if image_type != None:
        # Filtering images by image type
        filtered_img_list = [il for il in img_list if image_type in il]
        # If no image is available, we return a null object
        if len(filtered_img_list) == 0: return None
        # Getting a random number to get the image
        value = randint(0, len(filtered_img_list)-1)
        # Returning the random image URL
        return filtered_img_list[value]
    # If no image type was provided
    else:
        # Getting a random number to get the image
        value = randint(0, len(img_list)-1)
        # Returning the random image URL
        return img_list[value]

# Function to get liturgical season
# The request is taking a long time, so we better do it once by day
def get_liturgical_season(date=None):
    # Defining API base URL
    api_url = "http://calapi.inadiutorium.cz/api/v0/en/calendars/default/"
    
    # If no date was provided, we'll use the current one
    if (date is None): api_url += "today/"
    # If a date was provided, we'll get the date's liturgical season
    else: api_url += date.strftime("%Y/%m/%d")
    
    # Making the API request
    r = requests.get(api_url)
    liturgical_calendar = json.loads(r.text)
    
    # Returning the liturgical season
    # 'ordinary', 'lent', 'easter', 'advent' or 'christmas'
    return liturgical_calendar['season']

# MySQL connection config dict
connection_config_dict = get_mysql_connection_config_dict()

# Aspirations list
aspirations = []

# Initializing the boto3 (AWS) session
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

# S3 bucket root paths
img_path_base = "https://{0}.s3.{1}.amazonaws.com/".\
    format(
        os.getenv('AWS_BUCKET'),
        os.getenv('AWS_REGION'),
    )
rosary_img_path_base = "https://{0}.s3.{1}.amazonaws.com/rosary/[name]-mysteries/[number]/".\
    format(
        os.getenv('AWS_BUCKET'), 
        os.getenv('AWS_REGION'),
    )

# Getting S3 bucket files
img_list = get_s3_bucket_keys()
# Removing folders (keys which end with '/')
img_list = [item for item in img_list if item[-1] != '/']

# Getting prayers from DynamoDB table
prayers = get_dynamodb_table_prayers()

# Defining rosary mysteries
# Reference: https://opusdei.org/pt-pt/article/audios-terco-em-portugues/
rosary = prayers['rosario']

# Main script executing
if __name__ == '__main__':
    # Getting formatted current date
    print(format_date(datetime.today()))
    
    # Filling aspirations list
    query_aspirations()
    
    # Testing functions to get data
    aspiration = get_aspiration(id=None, tag=None)
    saint_caption, saint_image = get_saint_of_the_day()
    daily_meditation = get_daily_meditation()
    angules_text, angeuls_image = angelus_regina_caeli()
    liturgical_season = get_liturgical_season(datetime(2020, 5, 31))
    daily_rosary = get_rosary()

# If it's not the main file
else:
    # Filling aspirations list
    query_aspirations()
