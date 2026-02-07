from collections import OrderedDict
from typing import Callable, Iterable, Any
from enum import IntEnum
import copy
import re

from PackWrapper.Logger import Logger


class Task:
    def __init__(self, func: Callable[..., Any], args: Iterable[Any]):
        self.func = func
        self.args = args

        self.task = (func, args)

    def __call__(self):
        return self.task

    def __str__(self):
        return f"Task(func={self.func}, args={self.args})"

    def __repr__(self):
        return f"Task(func={self.func}, args={self.args})"

    def __iter__(self):
        yield self.func
        yield self.args

    def __getitem__(self, index):
        if index == 0:
            return self.func
        elif index == 1:
            return self.args
        else:
            raise IndexError("Task index out of range")

    def __len__(self):
        return 2

    def __hash__(self):
        return hash(self.task)

    def __eq__(self, other):
        if isinstance(other, Task):
            return self.func == other.func and self.args == other.args
        return False


class TaskID:
    def __init__(self, task_id: str):

        pattern = r"[^A-Za-z0-9_-]"

        if "." in task_id:
            self.task_id = task_id

        elif re.search(pattern, task_id):
            illegal_chars = re.findall(pattern, task_id)
            raise ValueError(f"illegal chars: {illegal_chars}")

        elif task_id == "":
            raise ValueError("Task ID is not empty!")

        else:
            self.task_id = task_id

    def __call__(self):
        return self.task_id

    def __str__(self):
        return self.task_id

    def __repr__(self):
        return f"TaskID('{self.task_id}')"

    def __eq__(self, other):
        if isinstance(other, TaskID):
            return self.task_id == other.task_id
        return False

    def __hash__(self):
        return hash(self.task_id)


class TaskArgs:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __iter__(self):
        yield from self.args
        yield from self.kwargs


class TaskPos(IntEnum):
    BEFORE = 0
    AFTER = 1
    REDIRECT = 2


class TaskSystem:
    tasks: OrderedDict[TaskID, Task] = OrderedDict()

    @classmethod
    def get_tasks(cls):
        return copy.deepcopy(cls.tasks)

    @classmethod
    def insert_task(
        cls, target_id: TaskID, task_id: TaskID, task: Task, position: TaskPos
    ):

        if target_id not in cls.tasks.keys():
            raise KeyError(f"Key '{target_id}' not found in dictionary")

        items = list(cls.tasks.items())
        target_index = next(i for i, (k, _) in enumerate(items) if k == target_id)

        match position:
            case TaskPos.BEFORE:
                insert_index = target_index

            case TaskPos.AFTER:
                insert_index = target_index + 1

            case TaskPos.REDIRECT:
                insert_index = target_index
                del items[target_index]

            case _:
                raise ValueError("Invalid position")

        items.insert(insert_index, (task_id, task))

        cls.tasks = OrderedDict(items)

        return insert_index

    @classmethod
    def add_task(
        cls,
        func: Callable,
        args: Iterable[Any] = [],
        insert_pos: tuple[TaskID, TaskPos] | None = None,
        task_id: TaskID | None = None,
    ):

        task_id = task_id if task_id is not None else TaskID(func.__qualname__)

        if insert_pos is not None:
            cls.insert_task(insert_pos[0], task_id, Task(func, args), insert_pos[1])
        else:
            cls.tasks[task_id] = Task(func, args)

    @classmethod
    @Logger.ID("TaskSystem")
    def run(cls):

        for task_name, task in cls.tasks.items():
            Logger.debug(f"Running task, ID: {task_name}")

            if isinstance(task.args, dict):
                task.func(**task.args)
            else:
                task.func(*task.args)