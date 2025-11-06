from dataclasses import dataclass

import pytest
from sqlalchemy import Engine, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from timothy import DBCluster, exceptions as exc


EMPLOYEES = {
    "Michael": "Scott",
    "Jim": "Halpert",
    "Pam": "Beesly",
    "Dwight": "Schrute",
}


@dataclass
class Settings:
    username: str
    password: str
    db: str
    port: int


@dataclass
class DBScope:
    settings: Settings
    engine: Engine
    session: Session


class Base(DeclarativeBase): ...


class Employee(Base):
    __tablename__ = "employee"

    firstname: Mapped[str] = mapped_column(String, primary_key=True)
    lastname: Mapped[str]


def create_session_scope(cfg: Settings):
    conn = f"postgresql+psycopg2://{cfg.username}:{cfg.password}@localhost:{cfg.port}/{cfg.db}"
    engine = create_engine(conn)
    return DBScope(settings=cfg, engine=engine, session=sessionmaker(engine))


@pytest.fixture(scope="session")
def michael_scope() -> DBScope:
    return create_session_scope(
        Settings(
            username="michael_scott",
            password="thatswhatshesaid",
            db="dunder_mifflin",
            port=5432,
        )
    )


@pytest.fixture(scope="session")
def initial_db(michael_scope: DBScope) -> None:
    DBCluster(
        username=(msttngs := michael_scope.settings).username,
        password=msttngs.password,
        host="localhost",
        db=msttngs.db,
    ).ensure_db()
    Base.metadata.create_all(michael_scope.engine)
    with michael_scope.session.begin() as s:
        employees = [
            Employee(firstname=first, lastname=last)
            for first, last in EMPLOYEES.items()
        ]
        s.add_all(employees)


@pytest.fixture(scope="session")
def jim_scope() -> DBScope:
    return create_session_scope(
        Settings(
            username="jim_halpert",
            password="bearseatbeetsbearbeetsbattlestargalactica",
            db="dunder_mifflin",
            port=5433,
        )
    )


def test_e2e(initial_db, michael_scope: DBScope, jim_scope: DBScope) -> None:
    DBCluster(
        username=(msttngs := michael_scope.settings).username,
        password=msttngs.password,
        host="localhost",
        db=msttngs.db,
    ).clone_to(
        DBCluster(
            username=(jsttngs := jim_scope.settings).username,
            password=jsttngs.password,
            host="localhost",
            db=jsttngs.db,
            port=5433,
        )
    )

    with jim_scope.session.begin() as s:
        for first, last in EMPLOYEES.items():
            query = select(Employee).where(Employee.firstname == first)
            assert (emp := s.execute(query).scalar_one())
            assert emp.lastname == last


def test_prevent_already_exists(
    initial_db,
    michael_scope: DBScope,
    jim_scope: DBScope,
) -> None:
    with pytest.raises(exc.AlreadyExists):
        DBCluster(
            username=(msttngs := michael_scope.settings).username,
            password=msttngs.password,
            host="localhost",
            db=msttngs.db,
        ).clone_to(
            DBCluster(
                username=(jsttngs := jim_scope.settings).username,
                password=jsttngs.password,
                host="localhost",
                # postgres exists by default
                db="postgres",
                port=5433,
            )
        )

