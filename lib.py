import streamlit as st
from typing import TypeVar, Callable

T = TypeVar("T")


class StateFactory:
    """A factory for creating Streamlit state variables with unique keys."""

    def __init__(self, key: str | None = None):
        self.__key = "" if key is None else key

    def __enter__(self):
        self.__count = 0
        self.__dirty = False
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.__dirty:
            return

        st.rerun()

    def state(self, initial: T) -> tuple[T, Callable[[T], None]]:
        """Define a Streamlit state variable with a unique key.

        Args:
            initial (T, optional): The initial value of the state. Defaults to None.

        Returns:
            tuple[T, Callable[[T], None]]: [value, setter]: A tuple containing the current value of the state and a setter function to update it.
        """

        self.__count += 1
        id = f"{self.__key}-{self.__count}"

        value = initial

        if id in st.session_state:
            value = st.session_state[id]
        else:
            st.session_state[id] = initial

        def setter(new_value: T) -> None:
            st.session_state[id] = new_value
            self.__dirty = True

        return value, setter
