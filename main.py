from db import db
from dnevniklib.student import Student
from dnevniklib.homeworks import Homeworks
from dnevniklib.errors import DnevnikTokenError

import asyncio

from datetime import timedelta, datetime
import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Update, Message
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import BaseMiddleware

class NewTask(StatesGroup):
    title = State() #название
    description = State() #описание
    deadline = State() #день дедлайна

class NewActivity(StatesGroup):
    title = State() #название
    description = State() #описание
    date_start_time = State() #время начала
    length = State() #время конца

class Timetable(StatesGroup):
    active = State()

class Token(StatesGroup):
    active = State()

class CommandCancelMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        if event.message:
            message: Message = event.message
            state: FSMContext = data.get("state")
            current_state = await state.get_state()

            state_command_map = {
            "NewTask:title": "/addTask",
            "NewTask:description": "/addTask",
            "NewTask:deadline": "/addTask",

            "NewActivity:title": "/addActivity",
            "NewActivity:description": "/addActivity",
            "NewActivity:date_start_time": "/addActivity",
            "NewActivity:length": "/addActivity",

            "Timetable:active": "/timetable",

            "Token:active": "/newToken",
            }


            if current_state and isCommand(message.text):

                expected_command = state_command_map.get(current_state)

                if message.text != expected_command:
                    await state.clear()
                    await message.answer("Отмена текущего действия, так как вызвана другая команда.")
                    return

        return await handler(event, data)

def isCommand(text:str):
    if text in COMMANDS:
        return True
    return False

COMMANDS = ["/start", "/help", "/newToken", "/homework", "/addTask", "/viewTasks", "/addActivity", "/timetable", "/cancel"]

with open("config.txt", "r") as f:
    bot_token = f.readline()

TOKEN = bot_token

dp = Dispatcher()
bot = Bot(TOKEN)

@dp.message(Command('start'))
async def commandStart(message: Message):
  db.addUser(message.from_user.id)
  await message.answer("""Привет, я бот для отслеживания заданий, занятий и получения ДЗ из электронного дневника МЭШ!
Для использования всего функционала данного бота тебе понадобится получить токен для авторизации в сервисах МЭШ.
Инструкция:
1) Открыть https://school.mos.ru/diary
2) После авторизации на экране с вашим расписанием нажать F12 (или ПКМ и после этого последний пункт в открывшемся меню)
3) В правом окне откройте Application
4) У вас появится список в левой части. Найдите Cookies и нажмите на стрелочку около данной строки. Вам откроется ячейка с названием https://school.mos.ru/diary
5) В открывшейся таблице найдите aupd_token, скопируйте и нажмите на данную команду: /newToken
Для просмотра списка команд и их назвачение напишите или нажмите: /help    
""", reply_markup=createKb())

def createKb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="/start"), KeyboardButton(text="/help"), KeyboardButton(text="/cancel")],
        [KeyboardButton(text="/homework")],
        [KeyboardButton(text="/addTask"), KeyboardButton(text="/viewTasks"), KeyboardButton(text="/deleteTasks")],
        [KeyboardButton(text="/addActivity"), KeyboardButton(text="/timetable")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard

async def run():
    # db.clearData()
    db.create()
    dp.update.middleware(CommandCancelMiddleware())
    await dp.start_polling(bot)
    await FSMContext.clear()

@dp.message(Command('help'))
async def commandHelp(message):
    await message.answer("""
Вот чем я могу тебе помочь:
/start - о боте
/newToken - изменение токена для входа в дневник
/homework - актуальные домашние задания
/cancel - отмена действия команды
/addTask - добавить новое задание
/viewTasks - актуальные дополнительные задания
/deleteTasks - удалить прошедшие задания
/addActivity - добавить новое событие
/timetable - расписание
""")
    
@dp.message(Command("cancel"))
async def cancelCommand(message: Message, state: FSMContext):
    await message.answer("Отмена действия всех команд")
    await state.clear
    
@dp.message(Command("newToken"))
async def activateToken(message: Message, state: FSMContext):
    await state.set_state(Token.active)
    await message.answer("""Отправьте ваш токен. 
Если вы случайно нажали команду напишите: Ошибка (регистр такой же)""")

@dp.message(Token.active)
async def newToken(message: Message, state: FSMContext):
    if message.text=="Ошибка":
        await message.answer("Токен не был изменен")
    else:
        token = message.text
        db.addToken(message.from_user.id, token)
        await message.answer("Токен успешно обновлен")
    await state.clear()

@dp.message(Command('homework'))
async def commandHomework(message: Message):
    auth_token = db.getToken(message.from_user.id)
    try:
        stud = Student(auth_token)
    except DnevnikTokenError as e:
        await message.answer("У вас нерабочий токен авторизации в МЭШ. Попробуйте добавить еще раз по команде /newToken. Инструкция получения /start")
    hm = Homeworks(stud)
    res = hm.get_homework_by_date()
    output = ""
    for i in res:
        output = output + i.subject_name + ": " + i.description + "\nДедлайн: " + i.created_at + "\n" + "\n"
    if output =="":
        output = "На следующие 7 дней нет заданий"
    await message.answer(output)

@dp.message(Command('addTask'))
async def commandAddTask(message, state: FSMContext):
    await state.set_state(NewTask.title)
    await message.answer('Введите название задания')

@dp.message(NewTask.title)
async def registerTaskTitle(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewTask.description)
    await message.answer('Введите описание задания')

@dp.message(NewTask.description)
async def registerTaskDescription(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(NewTask.deadline)
    await message.answer("Введите дату дедлайна. Формат: YYYY-MM-DD")

@dp.message(NewTask.deadline)
async def registerTaskDeadline(message: Message, state: FSMContext):
    inp = message.text
    try:
        date = datetime.date(year = int(inp[:4]), month = int(inp[5:7]), day = int(inp[8:]))
        await state.update_data(deadline = message.text)
        data = await state.get_data()
        await message.answer(f'Ваше задание: {data["title"]}\nОписание: {data["description"]}\nДедлайн: {data["deadline"]}')
        db.addTask(data, message.from_user.id)
        await state.clear()
    except ValueError as e:
        await message.answer("Неправильный формат даты, попробуйте еще раз")


@dp.message(Command('addActivity'))
async def commandAddActivity(message, state: FSMContext):
    await state.set_state(NewActivity.title)
    await message.answer('Введите название занятия')

@dp.message(NewActivity.title)
async def registerActivityTitle(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewActivity.description)
    await message.answer('Введите описание занятия')

@dp.message(NewActivity.description)
async def registerActivityDescription(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(NewActivity.date_start_time)
    await message.answer("Введите дату занятия. Формат: YYYY-MM-DD HH:MM")

@dp.message(NewActivity.date_start_time)
async def registerActivityDateStart(message: Message, state: FSMContext):
    date_start_time = message.text
    try:
        dat = datetime.datetime(int(date_start_time[:4]), int(date_start_time[5:7]), int(date_start_time[8:10]), int(date_start_time[11:13]), int(date_start_time[14:16]))
        await state.update_data(date_start_time = message.text)
        await state.set_state(NewActivity.length)
        await message.answer('Введите продолжительность занятия. Формат: HH:MM')
    except Exception as e:
        await message.answer("Неправильный формат даты, попробуйте еще раз")

@dp.message(NewActivity.length)
async def registerActivityLength(message: Message, state: FSMContext):
    length = message.text
    try:
        time_split = [int(x) for x in length.split(":")]
        time = datetime.time(time_split[0], time_split[1])
        await state.update_data(length = message.text)
        data = await state.get_data()
        date = data["date_start_time"]
        date = datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10]), int(date[11:13]), int(date[14:16]))
        end_time = date + timedelta(hours=time.hour, minutes=time.minute)
        await message.answer(f'Ваше занятие: {data["title"]}\nОписание: {data["description"]}\nДата и время начала: {data["date_start_time"]}\nВремя окончания: {str(end_time)[:-3]}')
        data["date_end_time"] = str(end_time)[:-3]
        db.addActivity(data, message.from_user.id)
        await state.clear()
    except Exception as e:
        await message.answer(f"Неправильный формат времени, попробуйте еще раз {e}")

@dp.message(Command('viewTasks'))
async def commandViewTasks(message: Message):
    result = db.getTasks(message.from_user.id)
    output = ""
    for i in range(len(result)):
        row = result[i]
        output = output + "Название: " + row[0] + "\n"
        output = output + "Описание: " + row[1] + "\n"
        output = output + "Дата дедлайна: " + row[2] + "\n"
        if i!=len(result)-1:
            output += "\n"
    if output=="":
        output = "У вас нет заданий"
    await message.answer(output)

@dp.message(Command("deleteTasks"))
async def cancel(message: Message):
    db.clearTasks()
    await message.answer("Прошедшие задания успешно удалены")

@dp.message(Command('timetable'))
async def commandViewTimetable(message: Message, state: FSMContext):
    await state.set_state(Timetable.active)
    await message.answer('Введите день, за который вы хотите увидеть ваше расписание. Формат YYYY-MM-DD')

@dp.message(Timetable.active)
async def timetable(message: Message, state: FSMContext):
    inp = message.text
    try:
        dat = datetime.date(year = int(inp[:4]), month = int(inp[5:7]), day = int(inp[8:]))
        output = ""
        result = db.viewActivities(message.from_user.id, inp)
        if len(result)!=0:
            for i in range(len(result)):
                row = result[i]
                output = output + "Название: " + row[0] + "\n"
                output = output + "Описание: " + row[1] + "\n"
                output = output + "Время начала: " + row[2] + "\n"
                output = output + "Время окончания: " + row[3] + "\n"
                if i!=len(result)-1:
                    output += "\n"
        else:
            output = "У вас нет занятий в данный день"
        await message.answer(output)
        await state.clear()
    except ValueError as e:
        await message.answer("Неправильный формат даты, попробуйте еще раз")

asyncio.run(run())