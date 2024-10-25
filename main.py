import os
import asyncio
import nest_asyncio
import requests
import logging
import http.client
import psutil
import time
import urllib3
import paramiko
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Dictionary to store the bot's message IDs per chat
bot_message_ids_per_chat = {}

# Load environment variables from .env file
load_dotenv('token.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Suppress telegram bot logging to WARNING level to avoid excessive HTTP logs
logging.getLogger("telegram").setLevel(logging.WARNING)

# Suppress urllib3 and requests HTTP requests logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Suppress HTTPConnection debug level
http.client.HTTPConnection.debuglevel = 0


# Logger setup (if not already set up)
import logging
logger = logging.getLogger(__name__)

# Initialize variables for bot metrics
bot_version = "1.2.3"
update_logs = [
    "Fixed response time issues",
    "Added new commands: /info"
]
start_time = datetime.now()  # Track when the bot started
total_commands = 0
successful_responses = 0
error_count = 0
response_times = []
error_logs = []


# Function to record command usage and response time
def log_command(success: bool, response_time: float, error_message: str = None):
    global total_commands, successful_responses, error_count
    total_commands += 1
    response_times.append(response_time)
    if success:
        successful_responses += 1
    else:
        error_count += 1
        error_logs.append((datetime.now().strftime('%Y-%m-%d %H:%M:%S'), error_message))


# Function to calculate average response time
def get_average_response_time():
    if response_times:
        return sum(response_times) / len(response_times)
    return 0.0

# Function to get response success rate
def get_response_success_rate():
    if total_commands == 0:
        return 100.0  # If no commands yet, assume 100% success
    return (successful_responses / total_commands) * 100

# Function to track bot messages
async def track_bot_message(update: Update, message):
    chat_id = update.effective_chat.id
    if chat_id not in bot_message_ids_per_chat:
        bot_message_ids_per_chat[chat_id] = []  # Initialize if chat not in dict
    
    if message:
        bot_message_ids_per_chat[chat_id].append(message.message_id)


# List of commands
Cmds = [
    "1. /test - To Check If Bot Works Properly",
    "2. /start - To Open The Main UI Of The Bot",
    "3. /cmds - To Show All Available Commands",
    "4. /clear - To Clear All Lines in the Chat",
    "5. /info - To Check The Status Of The Bot"
]

ClassMonday = [
     " 11:00 - 13:00 - ճարտասանութիւն եւ վայելչագրութիւն | Ա կուրս ֊ https://jitsi.cyberhayq.am/%d5%83%d5%a1%d6%80%d5%bf%d5%a1%d5%bd%d5%a1%d5%b6%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6%d5%a5%d6%82%d5%be%d5%a1%d5%b5%d5%a5%d5%ac%d5%b9%d5%a1%d5%a3%d6%80%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6 ",
     " 16:00 - 18:00 - կրաւնիմաստասիրութիւն | Գ կուրս ֊ https://jitsi.cyberhayq.am/%D4%BF%D6%80%D5%A1%D6%82%D5%B6%D5%AB%D5%B4%D5%A1%D5%BD%D5%BF%D5%A1%D5%BD%D5%AB%D6%80%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6 "
]

ClassTuesday = [
  " 11:00 - 13:00 - համարողութիւն | Ա կուրս ֊ https://jitsi.cyberhayq.am/%d5%80%d5%a1%d5%b4%d5%a1%d6%80%d5%b8%d5%b2%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6",
  " 16:00 - 18:00 - հայերէնագիտութիւն | Բ կուրս ֊ https://jitsi.cyberhayq.am/%D5%80%D5%A1%D5%B5%D5%A5%D6%80%D5%A7%D5%B6%D5%A1%D5%A3%D5%AB%D5%BF%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6"
]

ClassWednesday = [
   " 11:00 - 13:00 - ճարտասանութիւն եւ վայելչագրութիւն | Ա կուրս ֊ https://jitsi.cyberhayq.am/%d5%83%d5%a1%d6%80%d5%bf%d5%a1%d5%bd%d5%a1%d5%b6%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6%d5%a5%d6%82%d5%be%d5%a1%d5%b5%d5%a5%d5%ac%d5%b9%d5%a1%d5%a3%d6%80%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6",
   " 14:00 - 16:00 - համարողութիւն, բնագիտութիւն | Բ, Գ կուրս ֊ https://jitsi.cyberhayq.am/%D5%80%D5%A1%D5%B4%D5%A1%D6%80%D5%B8%D5%B2%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6%D5%A2%D5%B6%D5%A1%D5%A3%D5%AB%D5%BF%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6",
   " 16:00 - 18:00 - կրաւնիմաստասիրութիւն | Գ կուրս ֊ https://jitsi.cyberhayq.am/%D4%BF%D6%80%D5%A1%D6%82%D5%B6%D5%AB%D5%B4%D5%A1%D5%BD%D5%BF%D5%A1%D5%BD%D5%AB%D6%80%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6"
]

ClassThursday = [
     " 11:00 - 13:00 - դասական լեզուներ, համեմատութիւն | Բ կուրս ֊ https://jitsi.cyberhayq.am/%d4%b4%d5%a1%d5%bd%d5%a1%d5%af%d5%a1%d5%b6%d5%ac%d5%a5%d5%a6%d5%b8%d6%82%d5%b6%d5%a5%d6%80%d5%b0%d5%a1%d5%b4%d5%a5%d5%b4%d5%a1%d5%bf%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6"
     " 16:00 - 18:00 - հայերէնագիտութիւն | Բ կուրս ֊ https://jitsi.cyberhayq.am/%D5%80%D5%A1%D5%B5%D5%A5%D6%80%D5%A7%D5%B6%D5%A1%D5%A3%D5%AB%D5%BF%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6"
]

ClassFriday = [
    " 11:00 - 13:00 - դասական լեզուներ, համեմատութիւն | Ա կուրս ֊ https://jitsi.cyberhayq.am/%d4%b4%d5%a1%d5%bd%d5%a1%d5%af%d5%a1%d5%b6%d5%ac%d5%a5%d5%a6%d5%b8%d6%82%d5%b6%d5%a5%d6%80%d5%b0%d5%a1%d5%b4%d5%a5%d5%b4%d5%a1%d5%bf%d5%b8%d6%82%d5%a9%d5%ab%d6%82%d5%b6",
    " 14:00 - 16:00 - համարողութիւն, բնագիտութիւն | Բ, Գ կուրս ֊ https://jitsi.cyberhayq.am/%D5%80%D5%A1%D5%B4%D5%A1%D6%80%D5%B8%D5%B2%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6%D5%A2%D5%B6%D5%A1%D5%A3%D5%AB%D5%BF%D5%B8%D6%82%D5%A9%D5%AB%D6%82%D5%B6"
]

# All Courses Students 
CourseA = [
    "Աթալյան Տիգրան Սուրենի",
    "Աթայան Արամ Անդրանիկի",
    "Ալեքսանյան Հայկ Սասունի",
    "Ալեքսանյան Ռաֆայել Սամվելի",
    "Ալեքսանյան Սերգեյ Համազասպի", 
    "Աղասյան Գայանե Արտաշեսի",
    "Ամիրխանյան Արմեն Սարգսի",
    "Առաքելյան Արմեն Գագիկի ",
    "Առուստամյան Ռուզաննա Արթուրի", 
    "Ասլանյան Արթուր Գոռի ",
    "Ավետիսյան Ռուբեն Նվերի", 
    "Բաբախանյան Ալեն Արմենի",
    "Բեջանյան Էդուարդ Արմանի", 
    "Գալուստյան Մարկ Միքայելի",
    "Գալստյան Ալեքսանդր Գագիկի", 
    "Գալստյան Արսեն Սուքիասի ",
    "Գալստյան Վիգեն Տիգրանի ",
    "Գերասիմենկո Նարե Նիկոլայի", 
    "Գրիգորյան Արտյոմ Հայկի ",
    "Դաբաղյան Հրաչյա Արծրունի",
    "Եղշատյան Ալյոնա Արարատի ",
    "Իսայան Արման Սարգսի ",
    "Խաչատրյան Ռաֆայել Հրայրի", 
    "Խաչատրյան Սեդրակ Վարուժանի", 
    "Կարապետյան Արմեն Ազատի ",
    "Կոնյան Կարո Սարգսի ",
    "Հակոբյան Ենովք Արամի", 
    "Հակոբյան Հայկ Արամի ",
    "Հակոբյան Սարգիս Գևորգի", 
    "Հակոբյան Վահագն Սամվելի",
    "Հայրապետյան Լևոն Սերգոյի", 
    "Հարությունյան Անդրանիկ Էդգարի", 
    "Հարությունյան Արման Էդուարդի ",
    "Հարությունյան Դավիթ Արտյոմի ",
    "Հարությունյան Հարութ Արտակի ",
    "Հովհաննիսյան Աշոտ Լևոնի ",
    "Հովհաննիսյան Սամվել Սևակի", 
    "Ղազարյան Արման Արամի ",
    "Ղլեչյան Մարի Գնելի ",
    "Մաիլյան Վարդան Տիգրանի", 
    "Մանասյան Արամ Արմենի ",
    "Մանուկյան Նատալի Ստեփանի", 
    "Մանուչարյան Արեգ Գագիկի ",
    "Միրզոյան Էդմոնդ Հովիկի ",
    "Նազարեթյան Էրիկ Հովհաննեսի", 
    "Նավասարդյան Ռաֆայել Հարությունի", 
    "Պետրոսյան Արսեն Ջոնիկի ",
    "Պետրոսյան Գագիկ Էդգարի",
    "Պետրոսյան Հայկ Վարդանի ",
    "Պոդոսյան Գոռ Դավիթի ",
    "Ջերեջյան Արփի Աշոտի ",
    "Սարգսյան Մարիետա Նորայրի", 
    "Սաֆարյան Նորայր Արթուրի ",
    "Սաֆարյան Վահան Հակոբի ",
    "Սեդրակյան Ալեն Մանվելլի ",
    "Սուլթանյան Տաթև Արմանի ",
    "Վարդանյան Անդրանիկ Նշանի", 
    "Տեր-Եղիշյան Լիլիթ Գարիկի ",
    "Փայտյան Մհեր Վարդանի ",
    "Փանոսյան Մարի Արտյոմի"
]


CourseB = [
   "Ալավերդյան Աշոտ Կարոյի" ,
   "Առաքելյան Նորիկ Գրիգորի" ,
   "Բարսեղյան Նարեկ Անդրանիկի",
   "Բոշյան Տաթև Արթուրի ",
   "Գևորգյան Տիգրան Ալենի", 
   "Գեւորգյան Գագիկ Սասունի",  
   "Դանիելյան Արսեն Գևորգի ",
   "Զաքարյան Ալեքսանդր Արշակի", 
   "Թոփալյան Գրիգորի Աշոտի ",
   "Իսպիրյան Արման Մանուկի ",
   "Իվանյան Վահագն Ներսեսի ",
   "Խանյան Վիկտորիա Արթուրի ",
   "Հայրապետյան Ելենա Ռոմանի ",
   "Հարությունյան Տարոն Հայկի ",
   "Հարությունյան Կարինա Գևորգի ",
   "Հովհաննիսյան Շուշանիկ Սևակի ",
   "Ղազարյան Էրիկ Արտակի ",
   "Մաթևոսյան Գուրգեն Սուրենի", 
   "Մաթևոսյան Սոնա Հայկի ",
   "Մաթևոսյան Նարեկ Արամի ",
   "Մակարյան Վլադիկ Կարենի ",
   "Մամուլյան Դավիթ Վալերի ",
   "Մանուկյան Արեգ Համլետի ",
   "Մելքոնյան Մոնթե Արտակի ",
   "Միրզոյան Զարեհ Արթուրի ",
   "Միքայելյան Տիգրան Վարազդատի", 
   "Մկրտչյան Արշակ Էդգարի ",
   "Մկրտչյան Գևորգ Վահրամի ",
   "Մովսեսյան Արսեն Հայկի ",
   "Շամոյան Անդրանիկ Մովսեսի",
   "Շավինյան Դիանա Մարատի ",
   "Ունջյան Տիգրան Էդուարդի ",
   "Պետրոսյան Թագուհի Արտակի ",
   "Սահակյան Անգելինա Մհերի ",
   "Սարգսյան Դավիթ Նորայրի ",
   "Սարգսյան Զավեն Բագրատի ",
   "Սարգսյան Ռոզի Սասունի ",
   "Սեթոյան Լուիզա Վահանի ",
   "Սերոբյան Արտավազդ Սարգսի ",
   "Սերոբյան Վահագն Բենյամինի ",
   "Սիմոնյան Ռուստամ Յաշայի ",
   "Սողոմոնյան Վոլոդյա Արտավազդի ",
   "Վանյան Էլեն Արմենի ",
   "Վարդանյան Միքայել Արեգի", 
   "Տիգրանյան Միլենա Քաջիկի ",
   "Տիգրանյան Տիգրան Անդրանիկի", 
   "Ցուգունյան Հայկ Արմանի ",
   "Օհանյան Մանուկ Արթուրի"

]


CourseG = [
  "Աբգարյան Արփինե Աղվանի", 
  "Աթայան Նարեկ Արտակի ",
  "Անդրեասյան Արամե Արմանի", 
  "Առաքելյան Լյովա Էդգարի  ",
  "Առաքելյան Ֆելիքս Գարիկի ",
  "Ավագյան Տիգրան Շահենի ",
  "Ավետիսյան Մայիս Արմենի  ",
  "Բաբայան Հայկ Վիրաբի ",
  "Բարխուդարյան Միքայել Վահագնի",  
  "Բարսեղյան Մարիա Արթուրի ",
  "Գալստյան Արամե Արտեմի  ",
  "Գասպարյան Խաչիկ Վարդանի ",
  "Թադեւոսյան Հայկ Արայի ",
  "Խաչատրյան Անիտա Արսենի  ",
  "Խաչատրյան Բաբկեն Սամվելի ",
  "Կարապետյան Հայկ Ազատի ",
  "Կիրակոսյան Ներսես Վարուժանի", 
  "Կիրիչենկո Ժասմին Դմիտրիի ",
  "Ղազարյան Էմին Տիգրանի ",
  "Մաթեւոսյան Հայկ Սահակի ",
  "Մաթեւոսյան Նանե Մհերի ",
  "Մանգասարյան Արտյոմ Օսկարի", 
  "Մարգարյան Ավետիք Հարությունի", 
  "Մելքոնյան Անժելա Արտաշեսի ",
  "Միքայելյան Էմիլյա Համլետի ",
  "Մկրտչյան Լիլիթ Սամվելի ",
  "Մկրտչյան Մկրտիչ Սարգսի ",
  "Մուղդուսյան Մանե Վահագնի ",
  "Մուրադյան Հասմիկ Արամի  ",
  "Նադոյան Բորիս Աշոտի ",
  "Նազարյան Շողակաթ Գարիկի ", 
  "Պետրոսյան Արտավազդ Արտակի ",
  "Պողոսյան Անի Վահագնի ",
  "Սամվելյան Զորիկ Արթուրի ",
  "Սարգսյան Մերի Արսենի ",
  "Սարգսյան Ներսես Նազարեթի",  
  "Սարգսյան Սարգիս Արսենի ",
  "Սուլեյմանյան Սվետլանա Վարդանի", 
  "Սուլթանյան Տիգրան Արմանի ",
  "Վարդանյան Գրիգոր Տիգրանի ",
  "Վարդանյան Նարեկ Գարեգինի ",
  "Վարոսյան Անիտա Արթուրի ",
  "Տաթեւյան Միքայել Հրաչյայի ",
  "Տոնոյան Արման Կարենի ",
  "Քոթանջյան Լիլիթ Կարենի ",
  "Օհանյան Արտակ Միսակի"

]


CourseD = [
  "Աբրահամյան Տիգրան Դավթի ",
  "Ալավերդյան Ռաֆայել Շահենի", 
  "Ասատրյան Սիմոն Մանուկի ",
  "Բալոյան Արտյոմ Արթուրի ",
  "Բրուտյան Հրաչյա Կարենի ",
  "Գալստյան Նաթանայել Տիգրանի", 
  "Գասպարյան Ալբերտ Օգսենի ",
  "Գեւորգյան Արեգ Վահեի ",
  "Գյոնջյան Էրիկա Ռուբենի ",
  "Գյուլեյան Տավրոս Ֆիլիպի ",
  "Կարապետյան Սամվել ",
  "Հակոբյան Մարիամ ",
  "Հովհաննիսյան Էդգար Վարուժանի",  
  "Ղազարյան Գայանե Հովհաննեսի ",
  "Մանուկյան Արինա Նորայրի ",
  "Մանվելյան Աստղեր Գեղամի ",
  "Մարոնյան Պետրոս Մանուկի ",
  "Մելիքջանյան Նարեկ Ալեքսանի", 
  "Պետրոսյան Վարդան Վահրամի ",
  "Պետրոսյան Տիգրան Քաջիկի ",
  "Սահակյան Սոնա Հրաչյայի ",
  "Սարգսյան Դերենիկ Տիգրանի ",
  "Սարիբեկյան Արիանա Ռոբերտի ",
  "Սարգսյան Վահե Կարոյի ",
  "Ստեփանյան Աշոտ Գրիգորի ",
  "Վարդազարյան Տիգրան Մաթևոսի", 
  "Քալանթարյան Մաքսիմ Նիկոլայի",
]

# Apply nest_asyncio
nest_asyncio.apply()

# Function for the main menu (start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Courses", callback_data='courses')],
        [InlineKeyboardButton("Classes", callback_data='classes')],
        [InlineKeyboardButton("Laptops", callback_data='laptops')],
        [InlineKeyboardButton("Close", callback_data='close_ui')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Store the original message (the /start command) so it can be deleted later
    message = await update.message.reply_text('Choose a command:', reply_markup=reply_markup)
    
    # Log the command usage
    logger.info(f"{update.message.from_user.username or update.message.from_user.id} used /start")

    # Store the message ID in the user data for later deletion
    context.user_data['start_message_id'] = update.message.message_id
    context.user_data['ui_message_id'] = message.message_id  # Store the UI message ID

# Function for the Courses section with "Course A", "Course B", and "Back"
async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Course A", callback_data='course_a')],
        [InlineKeyboardButton("Course B", callback_data='course_b')],
        [InlineKeyboardButton("Course G", callback_data='course_g')],
        [InlineKeyboardButton("Course D", callback_data='course_d')],
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Choose a course:', reply_markup=reply_markup)


# Function for the Courses section with "Course A", "Course B", and "Back"
async def show_classes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Monday", callback_data='monday')],
        [InlineKeyboardButton("Tuesday", callback_data='tuesday')],
        [InlineKeyboardButton("Wednesday", callback_data='wednesday')],
        [InlineKeyboardButton("Thursday", callback_data='thursday')],
        [InlineKeyboardButton("Friday", callback_data='friday')],
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Choose a Class Day:', reply_markup=reply_markup)

async def show_laptops(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Laptop 1", callback_data='laptop_1')],
        [InlineKeyboardButton("Laptop 2", callback_data='laptop_2')],
        [InlineKeyboardButton("Laptop 3", callback_data='laptop_3')],
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if the update is from a callback query
    if update.callback_query:
        # Acknowledge the callback query
        await update.callback_query.answer()
        
        # Edit the previous message instead of sending a new one
        await update.callback_query.message.edit_text('Choose a laptop to connect:', reply_markup=reply_markup)
    elif update.message:
        # Handle the case where it's a regular message (optional)
        await update.message.reply_text('Choose a laptop to connect:', reply_markup=reply_markup)
    else:
        # Handle unexpected cases, if necessary
        await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred.")

# Function to display Course A list with a delete button
async def show_class_monday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(ClassMonday))

     # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"Monday Classes:\n{response}", reply_markup=reply_markup)

async def show_class_tuesday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(ClassTuesday))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"Tuesday Classes:\n{response}", reply_markup=reply_markup)

async def show_class_wednesday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(ClassWednesday))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"Wednesday Classes:\n{response}", reply_markup=reply_markup)

async def show_class_thursday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(ClassThursday))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"Thursday Classes:\n{response}", reply_markup=reply_markup)

async def show_class_friday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(ClassFriday))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"Friday Classes:\n{response}", reply_markup=reply_markup)

# Function to display Course A list with a delete button
async def show_course_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(CourseA))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"List of Course A:\n{response}", reply_markup=reply_markup)

# Function to display Course B list with a delete button
async def show_course_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(CourseB))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"List of Course B:\n{response}", reply_markup=reply_markup)

# Function to display Course G list with a delete button
async def show_course_g(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(CourseG))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"List of Course G:\n{response}", reply_markup=reply_markup)

# Function to display Course D list with a delete button
async def show_course_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(f"{i + 1}) {name}" for i, name in enumerate(CourseD))
    
    # Add a "Delete" button after the list
    keyboard = [[InlineKeyboardButton("Delete", callback_data='delete_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=f"List of Course D:\n{response}", reply_markup=reply_markup)

   # SSH command function
async def connect_and_run_command(laptop_number: str, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    ssh_details = {
        'laptop_1': {
            'host': '192.168.1.100',
            'username': os.getenv('LAPTOP_1_USER'),
            'password': os.getenv('LAPTOP_1_PASS'),
            'command': 'start notepad'
        },
        'laptop_2': {
            'host': '192.168.1.101',
            'username': os.getenv('LAPTOP_2_USER'),
            'password': os.getenv('LAPTOP_2_PASS'),
            'command': 'start calc'
        },
        'laptop_3': {
            'host': '192.168.50.145',
            'username': os.getenv('LAPTOP_3_USER'),
            'password': os.getenv('LAPTOP_3_PASS'),
            'command': 'flatpak run com.github.vkohaupt.vokoscreenNG'
        },
    }

    details = ssh_details.get(laptop_number)

    if details:
        try:
            # Create SSH client and connect
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(details['host'], username=details['username'], password=details['password'])

            # Execute the command
            logger.info(f"Executing command on {laptop_number}: {details['command']}")
            stdin, stdout, stderr = ssh.exec_command(details['command'])
            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh.close()

            response = ''
            if output:
                response += f"Output: {output}\n"
            if error:
                response += f"Error: {error}"

            await context.bot.send_message(chat_id=chat_id, text=response or "Command executed successfully with no output.")
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"SSH connection error for {laptop_number}: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Failed to connect to {laptop_number}. Error: {e}")

# Function to display all commands from Cmds list
async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "\n".join(Cmds)

    # Add a "Close" button after the list
    keyboard = [[InlineKeyboardButton("Close", callback_data='close_cmd_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store the original message (the /cmds command) so it can be deleted later
    message = await update.message.reply_text(text=f"List of Commands:\n{response}", reply_markup=reply_markup)

    # Log the command usage
    logger.info(f"{update.message.from_user.username or update.message.from_user.id} used /cmds")

    # Store the message ID in the user data for later deletion
    context.user_data['cmd_list_message_id'] = message.message_id  # Store the command list message ID

# Command to clear the chat by deleting all tracked messages
async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    count_deleted = 0
    
    if chat_id in bot_message_ids_per_chat:
        # Loop through all message IDs and delete them
        for message_id in bot_message_ids_per_chat[chat_id]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                count_deleted += 1
            except Exception as e:
                print(f"Failed to delete message {message_id}: {e}")
        
        # Clear the stored message IDs for this chat
        bot_message_ids_per_chat[chat_id].clear()

    # Send a confirmation message saying how many messages were deleted
    confirmation_message = await context.bot.send_message(chat_id=chat_id, text=f"Chat is cleared: {count_deleted} lines")

    # Track the confirmation message so it can also be deleted later
    await track_bot_message(update, confirmation_message)

# Example of a tracked message sent by the bot in other commands
async def some_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text="This is a test message.")
    await track_bot_message(update, message)

# Another example for testing
async def another_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Another test message.")
    await track_bot_message(update, message)


# Button handling function
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    laptop_number = query.data  # Retrieves the laptop number from button press (e.g. 'laptop_1')
    await connect_and_run_command(laptop_number, query.message.chat.id, context)  # Pass context and chat_id

    if query.data == 'courses':  # If "Courses" button is clicked
        await show_courses(update, context)

    elif query.data == 'classes':  # If "Course A" button is clicked
        await show_classes(update, context)

    elif query.data == 'laptops':  # If "Course A" button is clicked
        await show_laptops(update, context)

    elif query.data == 'monday':  # If "Course A" button is clicked
        await show_class_monday(update, context)
    
    elif query.data == 'tuesday':  # If "Course A" button is clicked
        await show_class_tuesday(update, context)
    
    elif query.data == 'wednesday':  # If "Course A" button is clicked
        await show_class_wednesday(update, context)

    elif query.data == 'thursday':  # If "Course A" button is clicked
        await show_class_thursday(update, context)

    elif query.data == 'friday':  # If "Course A" button is clicked
        await show_class_friday(update, context)

    elif query.data == 'course_a':  # If "Course A" button is clicked
        await show_course_a(update, context)

    elif query.data == 'course_b':  # If "Course B" button is clicked (you can add logic for Course B later)
         await show_course_b(update, context)

    elif query.data == 'course_g':  # If "Course G" button is clicked
        await show_course_g(update, context)

    elif query.data == 'course_d':  # If "Course D" button is clicked
        await show_course_d(update, context)
    
    elif query.data == 'back_to_main':  # If "Back" button is clicked, go back to the main menu
        await start(update, context)

    elif query.data == 'delete_list':  # If "Delete" button is clicked
        # Delete the current message (the list)
        await query.delete_message()

   
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    # Close UI button handling
    if query.data == 'close_ui':  # If "Close" button is clicked in the main UI
        chat_id = query.message.chat.id  # Corrected here

        # Delete the /start message if it exists
        if 'start_message_id' in context.user_data:
            start_message_id = context.user_data['start_message_id']
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=start_message_id)
                del context.user_data['start_message_id']  # Optionally remove from user data
            except Exception as e:
                print(f"Failed to delete /start message: {e}")

        # Delete the UI message if it exists
        if 'ui_message_id' in context.user_data:
            ui_message_id = context.user_data['ui_message_id']
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=ui_message_id)
                del context.user_data['ui_message_id']  # Optionally remove from user data
            except Exception as e:
                print(f"Failed to delete UI message: {e}")

    # Close command list button handling
    elif query.data == 'close_cmd_list':  # If "Close" button is clicked in the command list
        chat_id = query.message.chat.id  # Corrected here
        
        # Delete the command list message if it exists
        if 'cmd_list_message_id' in context.user_data:
            cmd_list_message_id = context.user_data['cmd_list_message_id']
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=cmd_list_message_id)
                del context.user_data['cmd_list_message_id']  # Optionally remove from user data
            except Exception as e:
                print(f"Failed to delete command list message: {e}")

# Test message function to ensure the bot is working
async def test_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot is working/active!")
    logger.info(f"{update.message.from_user.username or update.message.from_user.id} used /test")

# Info message function to ensure the bot is working
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Active Status
    active_status = "Yes" if (datetime.now() - start_time).seconds < 86400 else "No"
    
    # Ping (simulated, as real ping may need network request)
    ping_time = 90  # ms, replace with actual measurement if needed

    # Uptime
    uptime_duration = datetime.now() - start_time
    uptime_str = str(timedelta(seconds=uptime_duration.seconds))

    # CPU and Memory Load
    cpu_load = psutil.cpu_percent()
    memory_load = psutil.virtual_memory().percent

    # Success Rate and Average Response Time
    success_rate = get_response_success_rate()
    avg_response_time = get_average_response_time()

    # Last Restart Time
    last_restart = start_time.strftime('%Y-%m-%d %H:%M:%S')

    # Error Log Summary
    error_log_summary = "\n".join([f"{log[0]} - {log[1]}" for log in error_logs[-5:]])

    # Build Info Message
    info_message = (
     "📊 *Bot Information*\n\n"
        f"🔹 Active: {active_status}\n"
        f"🔹 Ping: {ping_time}ms (Good)\n"
        f"🔹 Uptime: {uptime_str}\n\n"
        
        "🛠️ *Bot Version & Updates*\n"
        f"🔹 Version: {bot_version}\n"
        f"🔹 Updates:\n" + "\n".join([f"  - {update}" for update in update_logs]) + "\n\n"
        
        "⚙️ *Server Load*\n"
        f"🔹 CPU Load: {cpu_load}%\n"
        f"🔹 Memory Usage: {memory_load}%\n\n"
        
        "📈 *Performance Metrics*\n"
        f"🔹 Success Rate: {success_rate:.2f}%\n"
        f"🔹 Avg Response Time: {avg_response_time:.2f}ms\n\n"
        
        "📅 *Last Restart*\n"
        f"🔹 Last Restart Time: {last_restart}\n\n"
        
        "🚨 *Error Logs*\n"
        + (error_log_summary if error_logs else "🔹 No recent errors.")
    
)

    await update.message.reply_text(info_message, parse_mode='Markdown')
    logger.info(f"{update.message.from_user.username or update.message.from_user.id} used /info")
# Main function to initialize the bot
async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("No token found! Please set the TELEGRAM_BOT_TOKEN environment variable.")

    app = ApplicationBuilder().token(token).build()

# Function to connect to a laptop and run a command
# SSH command function

# Register handlers
if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Register handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cmds', show_commands))  # Add the /cmds handler
    app.add_handler(CommandHandler('clear', clear_chat))  # Add the /clear handler
    app.add_handler(CommandHandler('test', test_message))
    app.add_handler(CommandHandler('laptops', show_laptops))  # New command handler for /laptops
    app.add_handler(CommandHandler('info', info))
    app.add_handler(CallbackQueryHandler(button))

    # Start the bot
    app.run_polling()  # This is the main event loop for the bot
