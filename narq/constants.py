"""Constant values used across the app.  Mostly used for redis key prefixes."""
default_queue_name = 'narq:queue'
job_key_prefix = 'narq:job:'
in_progress_key_prefix = 'narq:in-progress:'
result_key_prefix = 'narq:result:'
retry_key_prefix = 'narq:retry:'
health_check_key_suffix = ':health-check'
