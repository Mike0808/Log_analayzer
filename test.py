import unittest
import gzip
import main
import types
import os


class LogTest(unittest.TestCase):

    def test_get_latest_ui_log(self):
        self.assertEqual(main.get_latest_ui_log("./test_dir"), ('./test_dir/nginx-access-ui.log-20190630.gz', '20190630'))

    def test_get_requests_gzip(self):
        with gzip.open("./test_dir/nginx-access-ui.log-20190630.gz", mode="rb") as testfile:
            line = testfile.readline()
            self.assertIsInstance(main.get_requests_gzip(line), list)

    def test_get_requests_plain(self):
        with open("./test_dir/nginx-access-ui.log-20190629", mode="r") as testfile:
            line = testfile.readline()
            self.assertIsInstance(main.get_requests_plain(line), list)

    def test_find(self):
        with open("./test_dir/nginx-access-ui.log-20190629", mode="r") as testfile:
            line = testfile.readline()
            self.assertEqual(main.find("^(\d+.\d+.\d+.\d+).+\[", line), ["1.196.116.32"])

    def test_process_logs(self):
        self.assertIsInstance(main.process_logs("./test_dir/nginx-access-ui.log-20190629"), types.GeneratorType)
        tr = main.process_logs("./test_dir/nginx-access-ui.log-20190629")
        tv = [x[1] for x in tr]
        for idx in range(len(tv)):
            self.assertEqual(tv[idx], idx+1)

    def test_compute_log(self):
        self.assertIsInstance(main.compute_log("./test_dir/nginx-access-ui.log-20190629", 10, 10), list)
        len_list = len(main.compute_log("./test_dir/nginx-access-ui.log-20190629", 10, 10))
        self.assertEqual(len_list, 10)

    def test_create_output_report(self):
        path = "./test"
        self.assertEqual(os.path.exists(path), False)
        date = "20170723"
        file_name = path + '/report-' + "2017.07.23" + '.html'
        self.assertEqual(os.path.isfile(file_name), False)
        main.create_output_report(path, date, "sdasdasd")
        self.assertEqual(os.path.isfile(file_name), True)

    def test_get_config(self):
        test_dict = main.get_config("./test_dir/config.conf")
        self.assertIsInstance(test_dict, dict)
        self.assertEqual(len(test_dict), 4)
        self.assertEqual(int(test_dict["report_size"]), 100)

    def test_arg_switcher(self):
        switcher = [
            "--report_size",
            200,
            "--report_dir",
            "./test_dir",
            "--log_dir",
            "./test_dir",
            "--fail_size",
            10,
            "--config",
            "./test_dir/config.conf"
        ]
        test_dict = {
            "--report_size": 100,
            "--report_dir": "./test_dir",
            "--log_dir": "./test_dir",
            "--fail_size": 10,
            "--config": "./test_dir/config.conf"
        }
        self.assertEqual(main.arg_switcher(switcher), ('"./test_dir"\n', '"./test_dir"\n', '100\n', '10'))

