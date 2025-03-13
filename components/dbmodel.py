from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, PrimaryKeyConstraint
import datetime

__all__ = ['Base', 'HolidayCalendar', 'Duty', 'TaskId', "SpecialCalendar"]

class Base(DeclarativeBase):
    pass


class HolidayCalendar(Base):
    __tablename__ = 'holiday_calendar'

    date: Mapped[datetime.date] = mapped_column(primary_key=True, comment='日期')
    holiday: Mapped[int] = mapped_column(comment='假日类型：0-工作日，1-周末，2-春节，3-国庆, 4-劳动节, 5-其他法定假')
    comefrom: Mapped[str] = mapped_column(String(20), comment="数据来源：系统，人工维护", default="系统")


class Duty(Base):
    __tablename__ = 'duty'

    date: Mapped[datetime.date] = mapped_column(comment='日期')
    employee: Mapped[str] = mapped_column(String(20), nullable=True, comment='员工姓名')
    type: Mapped[str] = mapped_column(String(20), comment='值班类型')
    taskid: Mapped[str]  = mapped_column(String(20), comment="任务ID编号")

    __table_args__ = (
        PrimaryKeyConstraint('date', 'employee', 'type'),
    )


class TaskId(Base):
    __tablename__ = "task"

    uuid: Mapped[str] = mapped_column(String(32), primary_key=True, comment="任务uuid编号")
    created_timestamp: Mapped[datetime.datetime] = mapped_column(comment="任务创建时间")
    status: Mapped[str] = mapped_column(comment="排班结果")

class SpecialCalendar(Base):
    __tablename__ = "special_calendar"

    date: Mapped[datetime.date] = mapped_column(primary_key=True, comment="日期")
    type: Mapped[str] = mapped_column(String(20), comment="值班类型")
    action: Mapped[str] = mapped_column(String(20), comment="执行操作，ignore, insert")
    maintainer: Mapped[str] = mapped_column(String(20), comment="维护人员")
