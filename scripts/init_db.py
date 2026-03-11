"""初始化数据库结构。"""

from app.db.base import Base
from app.db.session import engine


def main():
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")


if __name__ == "__main__":
    main()
