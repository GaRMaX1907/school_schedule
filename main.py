from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(token)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"
def cansel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)
  
def no_schedules(message):
    bot.send_message(message.chat.id, 'Бот пока что не имеет расписания')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
        markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_schedules = {'Название расписания' : ["Введите название расписания", "schedule_name"],
                          "Описание" : ["Введите рассписание", "description"],
                          "Фото" : ["Добавьте фото", "image"],
                          "Статус" : ["Выберите статус расписания", "status_id"]}

def info_schedule(message, schedule_name):
    info = manager.get_schedule_info(schedule_name)[0]
    groups = manager.get_schedule_groups(schedule_name)
    if not groups:
        groups = 'Группа не добавлена'
    bot.send_message(message.chat.id, f"""Schedule name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Groups: {groups}
""")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """Привет! Я бот-менеджер расписания
Помогу тебе вспомнить, какие прдметы нужно готовить на завтра! Чтобы узнать доступные команды - введите /info
""")
    info(message)
    
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""Вы можете узнать о расписании и изменениях в нём. Для этого вам помогут команды:
    """)
    
@bot.message_handler(commands=['/new_group', ])
def groups(message):
    bot.send_message(message.chat.id, "Введите называние группы")
    bot.register_next_step_handler(message, name_group)

def name_group(message):
    name = message.text
    groups = [([name])]
    bot.send_message(message.chat.id, "Группа успешно добавлена")

@bot.message_handler(commands=['new_schedule'])
def addtask_command(message):
    bot.send_message(message.chat.id, "Введите называние расписания")
    bot.register_next_step_handler(message, name_schedule)

def name_schedule(message):
    name = message.text
    data = [name]
    bot.send_message(message.chat.id, "Прикрепите фото расписания")
    bot.register_next_step_handler(message, image_schedule, data=data)

def image_schedule(message, data):
    data.append(message.img)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "Введите текущий статус расписания", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_schedule, data=data, statuses=statuses)

def callback_schedule(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "Вы выбрали статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_schedule, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_schedule([tuple(data)])
    bot.send_message(message.chat.id, "Расписание сохранено")


@bot.message_handler(commands=['groups'])
def group_handler(message):
    schedules = manager.get_schedules
    if schedules:
        schedules = [x[2] for x in schedules]
        bot.send_message(message.chat.id, 'Выберите расписание, для которого нужно поменять группу', reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, group_schedule, schedules=schedules)
    else:
        no_schedules(message)


def group_schedule(message, schedules):
    schedule_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if schedule_name not in schedules:
        bot.send_message(message.chat.id, 'На данный момент такого расписания нет', reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, group_schedule, schedules=schedules)
    else:
        groups = [x[1] for x in manager.get_groups()]
        bot.send_message(message.chat.id, 'Выберите группу', reply_markup=gen_markup(groups))
        bot.register_next_step_handler(message, set_group, schedule_name=schedule_name, groups=groups)

def set_group(message, schedule_name, groups):
    group = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if group not in groups:
        bot.send_message(message.chat.id, 'Видимо, вы выбрали группу не из списка - попробуйте еще раз!) Выберите группу', reply_markup=gen_markup(groups))
        bot.register_next_step_handler(message, set_group, schedule_name=schedule_name, groups=groups)
        return
    manager.insert_group(schedule_name, group )
    bot.send_message(message.chat.id, f'Группа {group} добавлена расписанию {schedule_name}')


@bot.message_handler(commands=['schedules'])
def get_schedules(message):
    schedules = manager.get_schedules
    if schedules:
        text = "\n".join([f"Schedule name:{x[2]} \nLink:{x[4]}\n" for x in schedules])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in schedules]))
    else:
        no_schedules(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    schedule_name = call.data
    info_schedule(call.message, schedule_name)


@bot.message_handler(commands=['delete'])
def delete_handler(message):
    schedules = manager.get_schedules
    if schedules:
        text = "\n".join([f"Schedule name:{x[2]} \nLink:{x[4]}\n" for x in schedules])
        schedules = [x[2] for x in schedules]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, delete_schedule, schedules=schedules)
    else:
        no_schedules(message)

def delete_schedule(message, schedules):
    schedule = message.text

    if message.text == cancel_button:
        cansel(message)
        return
    if schedule not in schedules:
        bot.send_message(message.chat.id, 'На данный момент такого расписания нет', reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, delete_schedule, schedules=schedules)
        return
    schedule_id = manager.get_schedule_id(schedule)
    manager.delete_schedule(schedule_id)
    bot.send_message(message.chat.id, f'Расписание {schedule} удалено!')


@bot.message_handler(commands=['update_schedules'])
def update_schedule(message):
    schedules = manager.get_schedules
    if schedules:
        schedules = [x[2] for x in schedules]
        bot.send_message(message.chat.id, "Выберите расписание, которое хотите удалить", reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, update_schedule_step_2, schedules=schedules )
    else:
        no_schedules(message)

def update_schedule_step_2(message, schedules):
    schedule_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if schedule_name not in schedules:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выберите расписаие, которое хотите изменить еще раз:", reply_markup=gen_markup(schedules))
        bot.register_next_step_handler(message, update_schedule_step_2, schedules=schedules )
        return
    bot.send_message(message.chat.id, "Выберите, что требуется изменить в расписании", reply_markup=gen_markup(attributes_of_schedules.keys()))
    bot.register_next_step_handler(message, update_schedule_step_3, schedule_name=schedule_name)

def update_schedule_step_3(message, schedule_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_schedules.keys():
        bot.send_message(message.chat.id, "Кажется, вы ошибся, попробуйте еще раз!", reply_markup=gen_markup(attributes_of_schedules.keys()))
        bot.register_next_step_handler(message, update_schedule_step_3, schedule_name=schedule_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_schedules[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_schedule_step_4, schedule_name=schedule_name, attribute=attributes_of_schedules[attribute][1])

def update_schedule_step_4(message, schedule_name, attribute): 
    update_info = message.text
    if attribute== "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_schedule_step_4, schedule_name=schedule_name, attribute=attribute)
            return
    data = (update_info, schedule_name)
    manager.update_schedules(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены!)")


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    schedules =[ x[2] for x in manager.get_schedules]
    schedule = message.text
    if schedule in schedules:
        info_schedule(message, schedule)
        return
    bot.reply_to(message, "Вам  нужна помощь?")
    info(message)

    
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()