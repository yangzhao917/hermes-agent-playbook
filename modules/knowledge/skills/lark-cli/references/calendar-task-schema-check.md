=== task.tasks.list schema ===
=== task.tasks.list 参数 ===
  agent_task_status: type=integer, required=False, desc=智能体任务状态，优先使用completed字段，如果要查细分状态，再使用agent_task_status
  completed: type=boolean, required=False, desc=是否按任务完成进行过滤。填写true表示只列出已完成任务；填写false表示只列出未完成任务。不填写表示不过滤。
  page_size: type=integer, required=False, desc=每页的任务数量
  page_token: type=string, required=False, desc=分页标记。第一次请求不填该参数，表示从头开始查询；查询结果若还有更多数据时会同时返回新的 page_token。使用pa
  type: type=string, required=False, desc=列取任务的类型，目前只支持"my_tasks"，即“我负责的”。
  user_id_type: type=string, required=False, desc=表示user的ID的类型，支持open_id, user_id, union_id

=== task +get-my-tasks schema ===
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

=== task +complete schema ===
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

=== calendar events instance_view schema ===
=== calendar.events.instance_view 参数 ===
  calendar_id: type=string, required=True, desc=日历 ID。关于日历 ID 可参见[日历 ID 说明](https://open.feishu.cn/document/
  end_time: type=string, required=True, desc=结束时间，Unix 时间戳，单位为秒。该参数与 start_time 用于设置查询的时间范围。;;**注意**：star
  start_time: type=string, required=True, desc=开始时间，Unix 时间戳，单位为秒。该参数与 end_time 用于设置查询的时间范围。;;**注意**：start_
  user_id_type: type=string, required=False, desc=此次调用中使用的用户ID的类型

=== calendar +agenda schema ===
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
