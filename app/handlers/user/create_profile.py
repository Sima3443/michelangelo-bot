from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp

from database.service.profile import create_profile, edit_profile_photo, edit_profile_description

from app.handlers.msg_text import msg_text
from app.keyboards.default import gender_kb, find_gender_kb, del_kb
from app.states.profile_create_state import ProfileEdit, ProfileCreate
from app.handlers.user.profile import profile_command
import app.filters.create_profile_filtres as filters


@dp.message_handler(text="🔄")
async def _retry_create_profile_command(message: types.Message):
    """Запускает создания профиля заново"""
    await _create_profile_command(message)


# create profile
@dp.message_handler(filters.IsCreate())
async def _create_profile_command(message: types.Message):
    """Начало создание профиля"""
    await message.answer(msg_text.GENDER, reply_markup=gender_kb())
    
    await ProfileCreate.gender.set()


# gender
@dp.message_handler(filters.IsGender(), state=ProfileCreate.gender)
async def _gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.conf['gender'])
    await message.reply(msg_text.FIND_GENDER, reply_markup=find_gender_kb())
    await ProfileCreate.find_gender.set()
    
@dp.message_handler(state=ProfileCreate.gender)
async def _incorrect_gender(message: types.Message):
    """Ошибка фильтра гендера"""
    await message.answer(msg_text.INVALID_RESPONSE)


# gender of interest
@dp.message_handler(filters.IsFindGender(), state=ProfileCreate.find_gender)
async def _find_gender(message: types.Message, state: FSMContext):
    await state.update_data(find_gender=message.conf['find_gender'])
    await message.reply(msg_text.PHOTO, reply_markup=del_kb)
    await ProfileCreate.next()

@dp.message_handler(state=ProfileCreate.find_gender)
async def _incorrect_find_gender(message: types.Message):
    """Ошибка фильтра гендера"""
    await message.answer(msg_text.INVALID_RESPONSE)


# photo
@dp.message_handler(filters.IsPhoto(), content_types=["photo"], state=[ProfileEdit.photo, ProfileCreate.photo])
async def _photo(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    if await state.get_state() == ProfileEdit.photo.state:
        await edit_profile_photo(message.from_user.id, photo)
        await profile_command(message)
        await state.finish()
        return
    
    await state.update_data(photo=photo)
    await message.reply(msg_text.NAME)
    await ProfileCreate.next()
    
@dp.message_handler(state=[ProfileEdit.photo, ProfileCreate.photo])
async def _incorrect_photo(message: types.Message):
    """Ошибка фильтра фотографии"""
    await message.answer(msg_text.INVALID_PHOTO)


# name
@dp.message_handler(filters.IsName(), state=ProfileCreate.name)
async def _name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply(msg_text.AGE)
    await ProfileCreate.next()
    
@dp.message_handler(state=ProfileCreate.name)
async def _incorrect_name(message: types.Message):
    """Ошибка фильтра имени"""
    await message.answer(msg_text.INVALID_LONG_RESPONSE)


# age
@dp.message_handler(filters.IsAge(), state=ProfileCreate.age)
async def _age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply(msg_text.CITY)
    await ProfileCreate.next()
        
@dp.message_handler(state=ProfileCreate.age)
async def _incorrect_age(message: types.Message):
    """Ошибка фильтра возраста"""
    await message.answer(msg_text.INVALID_AGE)


# city
@dp.message_handler(filters.IsCity(), state=ProfileCreate.city)
async def _city(message: types.Message, state: FSMContext):
    """Устанавливает город пользователю сохрання кординаты"""
    async with state.proxy() as data:
        coordinates = (message.conf['coordinates'])
        data["city"] = message.text
        data['latitude'], data['longitude'] = coordinates
    
    await message.reply(msg_text.DESCRIPTION)
    await ProfileCreate.next()
    
@dp.message_handler(state=ProfileCreate.city,)
async def _incorrect_city(message: types.Message):
    """Ошибка фильтра города"""
    await message.answer(msg_text.INVALID_LONG_RESPONSE)


# description
@dp.message_handler(filters.IsDescription(), state=[ProfileCreate.desc, ProfileEdit.desc])
async def _description(message: types.Message, state=FSMContext):
    """Устанавливает описание пользователю"""
    if await state.get_state() == ProfileEdit.desc.state:
        await edit_profile_description(message.from_user.id, message.text)
    else:
        await state.update_data(desc=message.text)
        await create_profile(state, user_id=message.from_user.id)
    
    await state.finish()
    await profile_command(message)
    
@dp.message_handler(state=[ProfileCreate.desc, ProfileEdit.desc])
async def _incorrect_description(message: types.Message):
    """Ошибка фильтра описания"""
    await message.answer(msg_text.INVALID_LONG_RESPONSE)