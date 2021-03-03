# Log_analayzer

Utility for Nginx log parser and reporting.

The formatted report contain:

* count - how much URL occur in log, absolute value
* count_perc - how much URL occur in log, in %  about total count queries
* time_sum - summery \$request_time for URL, absolute value
* time_perc - summery \$request_time for URL, in %  about total count $request_time
* time_avg - average \$request_time for URL
* time_max - maximum \$request_time for URL
* time_med - median \$request_time for URL


Examples for run in prod:

after git clone this project to the your favorite directory, you can run utility.

  python3 main.py

after running you will see different variants parameters for work this utility
<usage: main.py --logdir --reportdir --reportsize, --failsize --log>

in this text you may see how usage utility:
1) You run utility with parameters or with config file
  In parameters you can specify log directory where nginx log saved. Default ./log
                        specify report directory where report will be saved. Default ./reports
                        specify report size - how much log lines will be viewed in report. Default 2
                        specify fail size - this is a parse fail in % following which program will stop with error. Default 3
                        and log - you can specify log file for save logs.

Config file must be like:  

[config]
log_dir= 
report_dir=
report_size=
fail_size=

When parsing and computing log file will accomplished you can open report in html.


RUN EXAMPLES:
1. main.py --logdir ./test --reportdir ./reports --reportsize 10 --failsize 3 --log app.log
