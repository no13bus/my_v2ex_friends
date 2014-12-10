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
- redis cache implement: (it just should be used in the hot data, not all mysql data)
`读: 读redis->没有，读mysql->把mysql数据写回redis
写: 写mysql->成功，写redis`
`使用mysql的udf`

- alembic检测数据表的字段属性变化的时候，需要在run_migrations_online这个函数里面要加上这个变量`compare_type=True` 这样才能检测出来数据表的变化
```
context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True
                )
```

- 目前爬虫代理还是不够用，时间爬不完呀。这样不管什么代理直接用，错了就错了。到时候看看有哪些用户没有爬下来，再重新爬一次就得了。重要的是以后稳定了之后，保证爬虫可用即可。
- 今天看了看ruby-china的api就做的不错，一个用户发布的帖子和回复以及follow的帖子都有记录，竟然还有post帖子的api, 但是实验了下，不知道为什么查看帖子和follow的帖子出错了。如果可行的话，其实ruby-china的API不错，直接用就好了，这样就能分析了。v2ex上面的还是不行。必须得爬下来才能完整的分析。因为没有用户发布的帖子这个api
- webhook是什么东西？
