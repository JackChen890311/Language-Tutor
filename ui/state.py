import streamlit as st
from data_store.data_store import DataStore
from model_manager import ModelManager
from services.prompt_builder import PromptBuilder
from services.language_service import LanguageService
from services.memory_service import MemoryService
from services.chat_service import ChatService
from services.word_list_service import WordListService
from services.lesson_service import LessonService
from services.level_test_service import LevelTestService


def init_services() -> None:
    if st.session_state.get("_initialized"):
        return

    store = DataStore()
    mm = ModelManager()
    pb = PromptBuilder()
    memory_svc = MemoryService(store, mm, pb)

    st.session_state.store = store
    st.session_state.mm = mm
    st.session_state.pb = pb
    st.session_state.language_svc = LanguageService(store)
    st.session_state.memory_svc = memory_svc
    st.session_state.chat_svc = ChatService(store, mm, pb, memory_svc)
    st.session_state.word_svc = WordListService(store, mm, pb)
    st.session_state.lesson_svc = LessonService(store, mm, pb)
    st.session_state.level_test_svc = LevelTestService(store, mm, pb)
    st.session_state._initialized = True


def get(key: str):
    return st.session_state[key]
