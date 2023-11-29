#!/usr/bin/env python3
# This Python file uses the following encoding: utf-8

import os, atexit
import asyncio, io
import pickle, json

from aiogram import Bot, Dispatcher, types
from loguru import logger

# Initialize the bot
TOKEN = os.environ.get('TOKEN','123456789:blablabla') 
YOUR_ADMIN_USER_ID = 6158970328

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Survey Manager class to handle surveys
class SurveyManager:
    global YOUR_ADMIN_USER_ID #= 6158970328
    def __init__(self):
        self.surveys = {}
        
    async def start_survey(self, user_id: int):
        logger.debug(f'starting survey for {user_id}')
        if user_id not in self.surveys:
            self.surveys[user_id] = {'name': None, 'age': None, 'gender': None, 'interests': None}
            await self.request_name(user_id)
        else:
            # Provide options to modify the existing survey
            await self.modify_survey(user_id) #2do: btns for requests

    async def request_name(self, user_id: int):
        logger.debug(f'asking name {user_id}')
        await bot.send_message(user_id, "Please enter your name:")
        self.surveys[user_id]['name'] = None

    async def request_age(self, user_id: int):
        logger.debug(f'age request {user_id}')
        await bot.send_message(user_id, f"Please, {self.surveys[user_id]['name']}, enter your age:")
        self.surveys[user_id]['age'] = None

    async def request_gender(self, user_id: int):
        logger.debug(f'gender requesting {user_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Male", "Female")
        await bot.send_message(user_id, "Please select your gender:", reply_markup=markup)
        self.surveys[user_id]['gender'] = None

    async def request_interests(self, user_id: int):
        logger.debug(f'interests asking {user_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("it-sec", "it-dev", "skip") #2do : accumulate from all to list
        await bot.send_message(user_id, "Please enter your interests (or skip if not interested):", reply_markup=markup)
        self.surveys[user_id]['interests'] = None

    async def modify_survey(self, user_id: int):
        logger.debug(f'review mode {user_id}')
        
        survey_data = (
            f"Name: {survey_manager.surveys[user_id]['name']}\n"
            f"Age: {survey_manager.surveys[user_id]['age']}\n"
            f"Gender: {survey_manager.surveys[user_id]['gender']}\n"
            f"Interests: {survey_manager.surveys[user_id]['interests']}")
        await bot.send_message(user_id, f"Thank you for your time! Here's your data:\n\n{survey_data}\n\nDo you want to save this information?", 
                               reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True).add("Yes", "No"))

    async def admin_mode(self, user_id: int):
        logger.debug(f'admin mode {user_id}')
        if user_id == YOUR_ADMIN_USER_ID: # Provide admin functionality
            await bot.send_message(user_id, "Admin Mode Activated.")
            await bot.send_message(user_id, f"Total Surveys: {len(self.surveys)}")

            if not self.surveys:
                await bot.send_message(user_id, "No surveys found.")
                return

            survey_id = next(iter(self.surveys))
            survey_data = self.surveys[survey_id]

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton(text="Next Survey", callback_data="next_survey"),
                       types.InlineKeyboardButton(text="Delete Entry", callback_data=f"delete_entry_{survey_id}"))
            markup.add(types.InlineKeyboardButton(text="Export as JSON", callback_data="export_json"))

            survey_info = (
                f"User ID: {survey_id}\n"
                f"Name: {survey_data['name']}\n"
                f"Age: {survey_data['age']}\n"
                f"Gender: {survey_data['gender']}\n"
                f"Interests: {survey_data['interests']}"
            )
            await bot.send_message(user_id, f"Survey Data:\n\n{survey_info}", reply_markup=markup)
        else:
            await bot.send_message(user_id, "Access denied. You don't have permission for admin mode.")
    
# Creating an object of SurveyManager
survey_manager = SurveyManager()

# Handling /start, /cancel, /admin commands
@dp.message_handler(commands=['start'])
async def start_survey(message: types.Message):
    logger.debug(f'survey started for user: {message.from_user.id}')
    user_id = message.from_user.id
    await survey_manager.start_survey(user_id)

@dp.message_handler(commands=['cancel'])
async def cancel_survey(message: types.Message):
    logger.debug(f'survey canceled for user: {message.from_user.id}')
    user_id = message.from_user.id
    if user_id in survey_manager.surveys:
        del survey_manager.surveys[user_id]
        await message.answer("Survey process has been canceled. Start over with /start again.")
    else:
        await message.answer("There is no active survey.")

@dp.message_handler(commands=['admin'])
async def admin_mode(message: types.Message):
    user_id = message.from_user.id
    await survey_manager.admin_mode(user_id)

# Handling incoming messages
@dp.message_handler()
async def process_messages(message: types.Message):
    logger.debug(f'process_messages @ {message.from_user.id} : {message.text}')
    user_id = message.from_user.id
    if user_id in survey_manager.surveys:
        if survey_manager.surveys[user_id]['name'] is None:
            survey_manager.surveys[user_id]['name'] = message.text
            await survey_manager.request_age(user_id)
        elif survey_manager.surveys[user_id]['age'] is None:
            try: # Validate the age input
                age = int(message.text)
                if 18 <= age <= 80:
                    survey_manager.surveys[user_id]['age'] = age
                    await survey_manager.request_gender(user_id) 
                else:
                    await bot.send_message(user_id, "Please enter a valid age between 18 and 80:")
            except ValueError:
                await bot.send_message(user_id, "Please enter a valid age as a number:")
        elif survey_manager.surveys[user_id].get('gender', None) is None: #fixed to get(,none)
            if message.text.lower() in ['male', 'female']:
                survey_manager.surveys[user_id]['gender'] = message.text.capitalize()
                await survey_manager.request_interests(user_id)
            else:
                markup = types.ReplyKeyboardRemove()
                await bot.send_message(user_id, "Please select your gender from the options provided.", reply_markup=markup)
        elif survey_manager.surveys[user_id]['interests'] is None:
            survey_manager.surveys[user_id]['interests'] = message.text
            await survey_manager.modify_survey(user_id)
        else:
            markup = types.ReplyKeyboardRemove()
            if message.text.lower() == 'yes':
                # Save survey results
                save_data()     # Add code to save the survey data
                await bot.send_message(user_id, "Your survey data has been saved. Thank you!", reply_markup=markup)
                #del survey_manager.surveys[user_id]  # Optionally, clear the survey data for this user
            elif message.text.lower() == 'no':
                await bot.send_message(user_id, "Your survey data has not been saved. Thank you!", reply_markup=markup)
                del survey_manager.surveys[user_id]  # Optionally, clear the survey data for this user
            else:
                await bot.send_message(user_id, "Please select 'Yes' or 'No' to save or discard the information.")
        
#
# Callback handler for "Next Survey" button
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'next_survey')
async def next_survey(callback_query: types.CallbackQuery):
    logger.debug(f'admin next entry')
    user_id = callback_query.from_user.id
    if user_id == YOUR_ADMIN_USER_ID:  # Replace YOUR_ADMIN_USER_ID with the actual admin user ID
        current_survey_id = int(callback_query.message.text.split('\n')[2].split(': ')[1])  # Extract current survey ID
        survey_ids = list(survey_manager.surveys.keys())

        if current_survey_id in survey_ids:
            current_index = survey_ids.index(current_survey_id)
            next_index = (current_index + 1) % len(survey_ids)
            next_survey_id = survey_ids[next_index]

            next_survey_data = survey_manager.surveys[next_survey_id]

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton(text="Next Survey", callback_data="next_survey"),
                       types.InlineKeyboardButton(text="Delete Entry", callback_data=f"delete_entry_{next_survey_id}"))
            markup.add(types.InlineKeyboardButton(text="Export as JSON", callback_data="export_json"))

            next_survey_info = (
                f"User ID: {next_survey_id}\n"
                f"Name: {next_survey_data['name']}\n"
                f"Age: {next_survey_data['age']}\n"
                f"Gender: {next_survey_data['gender']}\n"
                f"Interests: {next_survey_data['interests']}"
            )
            await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id,
                                        text=f"Survey Data:\n\n{next_survey_info}", reply_markup=markup)
        else:
            await bot.answer_callback_query(callback_query.id, text="Error: Survey not found.", show_alert=True)
    else:
        await bot.answer_callback_query(callback_query.id, text="Access denied. You don't have permission for this action.", show_alert=True)

# Callback handler for "Delete Entry" button
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('delete_entry_'))
async def delete_entry(callback_query: types.CallbackQuery):
    logger.debug(f'admin deleting entry: {callback_query.data}')
    user_id = callback_query.from_user.id
    if user_id == YOUR_ADMIN_USER_ID:  # 2do : Replace YOUR_ADMIN_USER_ID with the list of admin user IDs[] so one could add another
        survey_id = int(callback_query.data.split('_')[-1])

        if survey_id in survey_manager.surveys:
            del survey_manager.surveys[survey_id]
            await bot.answer_callback_query(callback_query.id, text="Survey entry deleted.", show_alert=True)
            await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        else:
            await bot.answer_callback_query(callback_query.id, text="Entry not found.", show_alert=True)
    else:
        await bot.answer_callback_query(callback_query.id, text="Access denied. You don't have permission for this action.", show_alert=True)

# Callback handler for "Export as JSON" button
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'export_json')
async def export_json(callback_query: types.CallbackQuery):
    logger.debug('admin exporting json')
    user_id = callback_query.from_user.id
    if user_id == YOUR_ADMIN_USER_ID:
        if survey_manager.surveys:
            # Convert survey data to ASCII-encoded JSON
            json_data = json.dumps(survey_manager.surveys, indent=4, ensure_ascii=False)
            json_bytes = io.BytesIO(json_data.encode('ascii'))
            
            # Send JSON data as a file
            await bot.send_document(user_id, json_bytes, caption="survey_data.json")
        else:
            await bot.send_message(user_id, "No surveys found.")
    else:
        await bot.answer_callback_query(callback_query.id, text="Access denied. You don't have permission for this action.", show_alert=True)

@atexit.register
def save_data():
    with open("surveys.pickle", "wb") as file:
        pickle.dump(survey_manager.surveys, file)
        logger.success("brains're saved")
        
# Initializing the bot
if __name__ == '__main__':
    logger.add("bot.log", format="{time} {level} {message}", level="TRACE", rotation="00:00", compression="zip", backtrace=True, diagnose=True)
    logger.info('loading bot')

    try:
        with open("surveys.pickle", "rb") as file:
            survey_manager.surveys = pickle.load(file)
    except FileNotFoundError:
        pass

    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()
