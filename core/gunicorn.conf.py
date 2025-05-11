import multiprocessing

proc_name = "app"

daemon = False

bind = "0.0.0.0:8000"

workers = multiprocessing.cpu_count() * 2 + 1
backlog = 2048
timeout = 30

accesslog = "-"
errorlog = "-"
loglevel = "info"
