from aiogram.fsm.state import StatesGroup, State


class Captcha_users(StatesGroup):
    status = State()


class UserStats(StatesGroup):
    user_id = State()
    
class WithdrawBalance(StatesGroup):
    amount = State()

class AddBalanceCasino(StatesGroup):
    amount = State()


class NewKefGame(StatesGroup):
    value = State()


class AdminText(StatesGroup):
    text = State()
    send = State()


class AdminPhotoText(StatesGroup):
    text = State()
    photo = State()
    send_photo = State()


class NewUrlAdmin(StatesGroup):
    url = State()

class AddBalanceUser(StatesGroup):
    amount = State()

class FakeDeposit(StatesGroup):
    user_id = State()
    amount = State()

class GameDice(StatesGroup):
    amount = State()

class GameSlots(StatesGroup):
    amount = State()

class GameFootball(StatesGroup):
    amount = State()

class GameKNB(StatesGroup):
    amount = State()
    choice = State()  # Добавлено для выбора камень/ножницы/бумага

