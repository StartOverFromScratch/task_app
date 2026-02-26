from enum import Enum


class TaskType(str, Enum):
    research = "research"
    decision = "decision"
    execution = "execution"


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    carryover_candidate = "carryover_candidate"
    needs_redefine = "needs_redefine"
    snoozed = "snoozed"


class Priority(str, Enum):
    must = "must"
    should = "should"


class CarryoverAction(str, Enum):
    today = "today"
    plus_2d = "plus_2d"
    plus_7d = "plus_7d"
    needs_redefine = "needs_redefine"
