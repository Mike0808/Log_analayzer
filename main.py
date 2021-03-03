#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bz2
import datetime
import gzip
import logging
import fnmatch
from statistics import median
from collections import defaultdict, Counter
from optparse import OptionParser
import os
import re
from datetime import datetime

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 2,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "FAIL_SIZE": 10,
}


def file_find(filepat, top):
    '''
    Find all filenames in a directory tree that match a shell wildcard pattern
    '''
    pfile = set()
    match = re.compile(r'\d+')
    for path, _, filelist in os.walk(top):
        break
    for name in fnmatch.filter(filelist, filepat):
        pfile.add(os.path.join(path, name))
    fmax = max(pfile, key=lambda x: match.findall(x))
    date = match.findall(fmax)
    return fmax, date


def gen_opener(filename):
    '''
    Open a sequence of filenames one at a time producing a file object.
    The file is closed immediately when proceeding to the next iteration.
    '''
    if filename.endswith('.gz'):
        f = gzip.open(filename, 'rt')
    elif filename.endswith('.bz2'):
        f = bz2.open(filename, 'rt')
    else:
        f = open(filename, 'rt')
    yield f
    f.close()


# Finder for function above
def find(pat, line):
    '''
    Find all matched pattern in line of text string
    '''
    match = pat.findall(line)
    if match:
        return match
    else:
        logging.error("Error with parsing log file")
        return False


# pattern finder in line of log file
def get_requests_plain(line):
    '''
    Consume and produce all matched string of text
    '''
    pat = (r''
           '^(\d+.\d+.\d+.\d+).+\['
           '(.+)\]\s'
           '"\w+\s(.+?)\s'
           '(\w+/\d.\d)'
           '("\s\d*\s)'
           '(\d*\s)'
           '"(.*?)"\s'
           '"(.*?)"\s'
           '"(.*?)"\s'
           '"(.*?)"\s'
           '(\d.\d+)')
    pat_cp = re.compile(pat)
    requests = find(pat_cp, line)
    if requests:
        res = requests
        return res
    return False


# Log processor. Load log file
def gen_process_logs(gen_file_name):
    '''
    Starter processing on log file.
    Starter pattern find func and count some values of text,
    like total and processed lines in a text and counter same url.
    '''
    processed = 0
    api_counter = Counter()
    for f in gen_file_name:
        for total, line in enumerate(f, 1):
            parsed_line = get_requests_plain(line)
            if parsed_line:
                processed += 1
                api_counter[parsed_line[0][2]] += 1
                pr = parsed_line[0]
                yield [pr, processed, total, api_counter[pr[2]]]


# sort addon
def keyfunc(tup):
    '''
    Func add-on for sorting dict method sorted().
    '''
    key, value = tup
    return value["Time_sum"]


def gen_param_former(file_name, fail_size):
    '''
    Calc func for some parameters of report and former a dict with certain keys.
    '''
    d = {}
    time_req = defaultdict(list)
    gr = gen_process_logs(file_name)
    sum_req_time = 0.0
    for it in gr:
        api = it[0][2]
        proc_count = it[1]
        total_line = it[2]
        api_count = it[3]
        sum_req_time += float(it[0][-1])
        time_req[api].append(float(it[0][-1]))
        time_sum = sum(time_req[api])
        time_max = max(time_req[api])
        time_avg = (time_sum/len(time_req[api]))
        time_med = median(time_req[api])
        fault_total = total_line - proc_count
        perc_fault = (fault_total * 100) / total_line
        if perc_fault > fail_size:
            logging.error("Exceeded bound of log parsing fail... Exit")
            exit()
        d[api] = {'Url': api,
                  'Count': api_count,
                  'Time_sum': time_sum,
                  'Time_max': time_max,
                  'Time_perc': 0,
                  'Count_perc': 0,
                  'Time_med': time_med,
                  'Time_avg': time_avg}
        yield d, sum_req_time, total_line


def sort_dict(unsorted_dict, report_size_count):
    '''
    Endind calculation and sorting dict from previous step.
    :param unsorted_dict:
    :param report_size_count:
    :return:
    '''
    total_lines = 0
    sum_req_time = 0.0
    for items in unsorted_dict:
        out = items[0]
        total_lines = items[2]
        sum_req_time = items[1]
    for k, v in out.items():
        v['Time_perc'] = round((v['Time_sum'] * 100) / sum_req_time, 3)
        v['Count_perc'] = round((v['Count'] * 100) / total_lines, 3)
    d_outer = sorted(out.items(), key=keyfunc, reverse=True)
    if len(d_outer) < report_size_count:
        logging.error("Line count of log less then your request...", exc_info=True)
        return False
    d_outer = d_outer[:report_size_count]
    logging.info("Compute and sort log finished...")
    return d_outer


# create prepared report
def create_output_report(path, date, input_data):
    '''
    Creating output report with defined struct.
    :param path:
    :param date:
    :param input_data:
    :return:
    '''
    logging.info("Creating output log...")
    date = datetime.strptime(date, "%Y%m%d")
    date = str(date).replace("-", ".").split(" ")[0]
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.isfile(path + '/report-' + date + '.html'):
        os.system('touch ' + path + '/report-' + date + '.html')
        with open('./report.html', encoding='utf-8', mode='r') as template:
            data = template.read()
        with open(path + '/report-' + date + '.html', encoding='utf-8', mode='w') as output_report:
            logging.info("Generating output file..")
            output_report.write(data.replace('$table_json', str(input_data)))
    else:
        print("The latest log file is computed and report made.")


def main():
    op = OptionParser()
    op.add_option("-r", "--reportsize", action="store", type=str, help="Max report size",
                  default=config['REPORT_SIZE'])
    op.add_option("-d", "--reportdir", action="store", type=str, help="Where will be saved processed reports",
                  default=config['REPORT_DIR'])
    op.add_option("-g", "--logdir", action="store", type=str, help="From where will be processed logs",
                  default=config['LOG_DIR'])
    op.add_option("-f", "--failsize", action="store", type=str, help="Max allowable fail in processing",
                  default=config['FAIL_SIZE'])
    op.add_option("-l", "--log", action="store", type=str, help="Log filename.", default="app.log")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log,
                        filemode='w',
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    try:
        ffile = file_find("nginx-access-ui.log-*", opts.logdir)
        filename = ffile[0]
        date = ffile[1][0]
        fopen = gen_opener(filename)
        gendict = gen_param_former(fopen, opts.failsize)
        sorted_dict = sort_dict(gendict, opts.reportsize)
        create_output_report(opts.reportdir, date, sorted_dict)
    except Exception as e:
        logging.exception("Exception occurred", exc_info=True)


if __name__ == "__main__":
    main()
