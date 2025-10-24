#!/usr/bin/env python3
from src.stage1.models import String

from typing import Dict

from sqlmodel import Session, select


class Database:
    """Handles database operations for String records.

    This class provides static methods to add, retrieve, and delete
    string entries in the database using SQLModel sessions.
    """

    @staticmethod
    def add_string(value: str) -> String | None:
        """Adds a new string to the database if it does not already exist.

        Args:
            value (str): The string value to be added to the database.

        Returns:
            String | None: Returns the newly added String object if successful,
            otherwise returns None if the string already exists.
        """
        from src import engine

        if Database.get_string(value) is None:
            new_string = String(name=value)
            with Session(engine) as session:
                session.add(new_string)
                session.commit()
                return new_string
        return None

    @staticmethod
    def get_string(value: str) -> String | None:
        """Retrieves a string record from the database.

        Args:
            value (str): The string value to look up in the database.

        Returns:
            String | None: Returns the String object if found, otherwise None.
        """
        from src import engine

        with Session(engine) as session:
            statement = select(String).where(String.name == value)
            results = session.exec(statement).first()
            return results if results else None
        return None

    @staticmethod
    def delete_string(value: str) -> bool:
        """Deletes a string record from the database.

        Args:
            value (str): The string value to be deleted.

        Returns:
            bool: Returns True if the record was successfully deleted,
            otherwise False.
        """
        from src import engine

        with Session(engine) as session:
            statement = select(String).where(String.name == value)
            results = session.exec(statement).first()
            if results:
                session.delete(results)
                session.commit()
                # session.refresh(results)
                return True
        return False

    @staticmethod
    def query_string(query: Dict[str, str | int | bool]) -> list[String]:
        """
        Dynamically builds and executes a query against the String table based on
        key-value filters provided in the 'query' dictionary.

        Args:
            query: A dictionary where keys are filter names and values are strings
                from the request query parameters.

        Returns:
            List[String]: A list of String model instances matching the criteria.
        """
        from src import engine

        with Session(engine) as session:
            statement = select(String)
            if val := query.get("is_palindrome"):
                lower_val = str(val).lower()
                if lower_val not in ["true", "false", "1", "0"]:
                    raise ValueError(
                        f"Invalid value for 'is_palindrome': '{val}'. Must be true/false/1/0."
                    )
                is_pali = lower_val in ["true", "1"]
                statement = statement.where(String.is_palindrome == is_pali)
            if val := query.get("max_length"):
                try:
                    statement = statement.where(String.length <= int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'max_length': '{val}'. Must be an integer."
                    )
            if val := query.get("min_length"):
                try:
                    statement = statement.where(String.length >= int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'min_length': '{val}'. Must be an integer."
                    )
            if val := query.get("word_count"):
                try:
                    statement = statement.where(String.word_count == int(val))
                except ValueError:
                    raise ValueError(
                        f"Invalid value for 'word_count': '{val}'. Must be an integer."
                    )

            if val := query.get("contains_character"):
                if not isinstance(val, str) or len(val) != 1:
                    raise ValueError(
                        "The 'contains_character' filter requires exactly one character."
                    )
                statement = statement.where(
                    String.character_frequency_map[val].as_integer() >= 1
                )
            results = session.exec(statement).all()
            return list(results)
