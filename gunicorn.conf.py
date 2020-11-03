import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 3
threads = multiprocessing.cpu_count() * 3
timeout = 3600
