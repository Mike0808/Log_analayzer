#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import gzip
import logging
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import os
import re
import sys
from datetime import datetime

config = {
    "REPORT_SIZE": 2,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "FAIL_SIZE": 10,
}


# find latest log file
def get_latest_ui_log(path):
    file_dict = {}
    for file in os.listdir(path):
        if file.startswith("nginx-access-ui.log-"):
            if not file.endswith('bz2'):
                file_dict[re.split('\W', file)[4]] = file
    file_dict = dict(sorted(file_dict.items(), reverse=True))
    res = path + "/" + (list(file_dict.values())[0])
    date = list(file_dict.keys())[0]
    return res, date


# pattern finder in line of log file
def get_requests_plain(line):
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
    requests = find(pat, line)
    if requests:
        res = list(*requests)
        return res
    return requests


# Finder for function above
def find(pat, line):
    match = re.findall(pat, line)
    if match:
        return match
    else:
        logging.error("Error with parsing log file")
        return False


# Log processor. Load log file
def process_logs(file_name):
    param_list = []
    total = processed = 0
    if file_name.endswith(".gz"):
        with gzip.open(file_name, mode='rb') as log_file:
            logging.info("Log gzip file opened for reading...")
            for line in log_file:
                line = str(line, 'utf-8')
                parsed_line = get_requests_plain(line)
                print(parsed_line)
                total += 1
                if parsed_line:
                    processed += 1
                    yield parsed_line, processed, total
    else:
        with open(file_name, encoding='utf-8', mode='r') as log_file:
            logging.info("Log pure file opened for reading...")
            for line in log_file:
                parsed_line = get_requests_plain(line)
                total += 1
                if parsed_line:
                    processed += 1
                    yield parsed_line, processed, total


# sort addon
def keyfunc(tup):
    key, d = tup
    return d["time_sum"]


def param_former(file_name, fail_size):
    gr = process_logs(file_name)
    param_list = [*gr]
    distinct_set = {x[0][2]: [x[0], x[1], x[2]] for x in param_list}
    distinct_list = list(distinct_set.keys())
    distinct_length = len(distinct_set.keys())
    lp = list(distinct_set.values())
    total_lines = lp[-1][-1]
    processed_lines = lp[-1][-2]
    fault_total = total_lines - processed_lines
    perc_fault = (fault_total * 100) / total_lines
    if perc_fault > fail_size:
        logging.error("Exceeded bound of log parsing fail... Exit")
        exit()
    return \
        param_list, \
        distinct_list, \
        distinct_length, \
        total_lines, \
        processed_lines


# Big function for prepare report file
def compute_log(param_list, distinct_list, distinct_length, total_lines):
    url = 2
    request_time = -1
    count = sum_request_time = max_time = all_sum_request_time = tmp_max_time = time_med = 0.0
    d = {}
    temp_time_list = []
    logging.info("Starting compute logs data...", exc_info=True)
    for idi in range(distinct_length):
        all_sum_request_time += float(param_list[idi][0][request_time])
        for idj in range(total_lines):
            if distinct_list[idi] in param_list[idj][0]:
                count += 1
                sum_request_time += float(param_list[idj][0][request_time])
                if max_time < float(param_list[idj][0][request_time]):
                    max_time = float(param_list[idj][0][request_time])
                temp_time_list.append(str(param_list[idj][0][request_time]))
        if count % 2:
            time_med = round(float(temp_time_list[round(count / 2)]), 3)
        else:
            time_med = round((float(temp_time_list[round(count / 2)]) +
                              float(temp_time_list[round(count / 2) - 1])) / 2, 3)
        d[distinct_list[idi]] = {'url': param_list[idi][0][url], 'count_perc': (count * 100) / total_lines,
                                 'count': count, 'time_sum': sum_request_time,
                                 'time_max': max_time, 'time_perc': (max_time * 100) / all_sum_request_time,
                                 'time_avg': sum_request_time / count, 'time_med': time_med}
        sum_request_time = 0.0
        max_time = 0.0
        time_med = 0.0
        count = 0
        temp_time_list.clear()
    return d


def sort_dict(unsorted_dict, report_size_count):
    d_out = []
    report_size_count = int(report_size_count)
    d_sorted = sorted(unsorted_dict.items(), key=keyfunc, reverse=True)
    if report_size_count > len(d_sorted):
        report_size_count = len(d_sorted)
        print("Line count of log less then your request... Taked max count is {}".format(report_size_count))
        logging.error("Line count of log less then your request...", exc_info=True)
    for idx in range(report_size_count):
        d_out.append(d_sorted[idx][1])
    logging.info("Compute and sort log finished...")
    return d_out


# create prepared report
def create_output_report(path, date, input_data):
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


# Config file parser
def get_config(path):
    config_dict = {}
    flag_config = False
    with open(path, encoding='utf-8', mode='r') as template:
        for line in template:
            if line:
                if line.startswith("[config]"):
                    flag_config = True
                    continue
                if flag_config:
                    if line.startswith("report_size"):
                        config_dict[line.split("=")[0]] = line.split("=")[1].strip()
                    elif line.startswith("report_dir"):
                        config_dict[line.split("=")[0]] = line.split("=")[1].strip()
                    elif line.startswith("log_dir"):
                        config_dict[line.split("=")[0]] = line.split("=")[1].strip()
                    elif line.startswith("fail_size"):
                        config_dict[line.split("=")[0]] = line.split("=")[1].strip()
                else:
                    return False
        return config_dict


# Choiser parameters
def arg_switcher(args_list):
    switcher = {
        1: "--report_size",
        2: "--report_dir",
        3: "--log_dir",
        4: "--fail_size",
        5: "--config"
    }
    d = {}
    report_dir = config["REPORT_DIR"]
    log_dir = config["LOG_DIR"]
    report_size = config["REPORT_SIZE"]
    fail_size = config["FAIL_SIZE"]
    nargs = len(args_list)
    for idx in range(nargs):
        arg = args_list[idx]
        if arg in switcher.values():
            d[arg.split("--")[1]] = args_list[idx + 1]
    if "config" in d.keys():
        config_file = d["config"]
        d.update(get_config(config_file))
    if "report_dir" in d.keys():
        report_dir = d["report_dir"]
    if "log_dir" in d.keys():
        log_dir = d["log_dir"]
    if "report_size" in d.keys():
        report_size = d["report_size"]
    if "fail_size" in d.keys():
        fail_size = d["fail_size"]
    return report_dir, log_dir, report_size, fail_size


def main():
    d = {}
    report_dir = None
    log_dir = None
    report_size_count = None
    fail_size = None
    nargs = len(sys.argv)
    usage = 'usage: {} --log_dir --report_dir --report_size, --fail_size, --config'.format(os.path.basename(sys.argv[0]))
    logging.basicConfig(filename='app.log',
                        filemode='w',
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    print(usage)
    try:
        report_dir, log_dir, report_size, fail_size = arg_switcher(sys.argv)
        file_name, date = get_latest_ui_log(log_dir)
        param_list, distinct_list, distinct_length, total_lines, processed_lines = \
            param_former(file_name, fail_size)
        computed_log = compute_log(param_list, distinct_list, distinct_length, total_lines)
        sorted_dict = sort_dict(computed_log, report_size)
        create_output_report(report_dir, date, sorted_dict)
    except Exception as e:
        logging.exception("Exception occurred", exc_info=True)


if __name__ == "__main__":
    main()
