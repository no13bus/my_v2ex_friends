my_v2ex_friends
===============

在v2ex上面找到你的好基友
##开发记录

- sqlalchemy 数据库迁移的时候 是先要生成一个迁移文件，然后使用`alembic upgrade head`或者`alembic upgrade 版本前几个字串`进行升级数据库，如果数据库的字段的属性变化，比如string(50)变为了string(30)。这个要自己写升级句子:
```python
from sqlalchemy.dialects import mysql
op.alter_column('users', 'name',
               existing_type=mysql.VARCHAR(length=20),
               nullable=False)
```
- `alembic revision --autogenerate -m "start"` 这种写着自动迁移的其实是说自动给你把迁移的内容写为了py程序，然后你自己还得要`alembic upgrade head`. 觉得这种迁移方式和ruby和laravel很像(没django的south好用)
- 