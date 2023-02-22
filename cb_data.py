from aiogram.filters.callback_data import CallbackData


class CallbackAutoFarm(CallbackData, prefix="auto_farm"):
    value: str


class CallbackTimerTest(CallbackData, prefix="timer_test"):
    value: str
    rnd: int


class CallbackGuildRace(CallbackData, prefix="guild_race"):
    race: str


class CallbackGuildList(CallbackData, prefix="guild_list"):
    guild_id: int
    guild_name: str


class CallbackGuildUserActivityRace(CallbackData, prefix="guild_user_activity_race"):
    race: str


class CallbackGuildUserActivitySelect(CallbackData, prefix="guild_activity_select"):
    user_id: int
    action: str
    guild_id: int
    guild_name: str
    pagenum: int


class CallbackTopRace(CallbackData, prefix="top_race"):
    race: str

