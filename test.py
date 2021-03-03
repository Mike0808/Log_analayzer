import unittest
import gzip
import main
import types
import os


class LogTest(unittest.TestCase):

    def test_file_find(self):
        self.assertEqual(main.file_find("nginx-access-ui.log-*", "./test_dir"), ('./test_dir/nginx-access-ui.log-20190630.gz', ['20190630']))

    def test_get_requests_plain(self):
        with open("./test_dir/nginx-access-ui.log-20190629", mode="r") as testfile:
            line = testfile.readline()
            self.assertIsInstance(main.get_requests_plain(line), list)
            self.assertEqual(main.get_requests_plain(line), [('1.196.116.32', '29/Jun/2017:03:50:22 +0300', '/api/v2/banner/25019354', 'HTTP/1.1', '" 200 ', '927 ', '-', 'Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5', '-', '1498697422-2190034393-4708-9752759" "dc7161be3', '0.390')])

    def test_process_logs(self):
        ffile = main.file_find("nginx-access-ui.log-*", "./test_dir")
        filename = ffile[0]
        date = ffile[1][0]
        fopen = main.gen_opener(filename)
        self.assertIsInstance(main.gen_process_logs(fopen), types.GeneratorType)
        tr = main.gen_process_logs(fopen)
        tv = [x[1] for x in tr]
        for idx in range(len(tv)):
            self.assertEqual(tv[idx], idx+1)

    def test_gen_param_former(self):
        ffile = main.file_find("nginx-access-ui.log-*", "./test_dir")
        filename = ffile[0]
        date = ffile[1][0]
        fopen = main.gen_opener(filename)
        self.assertIsInstance(main.gen_param_former(filename, 3), types.GeneratorType)
        gen = main.gen_param_former(fopen, 3)
        tv = [x for x in gen]
        self.assertIsInstance(tv, list)
        self.assertEqual(len(tv[0]), 3)
        self.assertIsInstance(tv[1][0], dict)
        self.assertEqual(tv[1][0].get('/api/v2/banner/25019354')['Url'], '/api/v2/banner/25019354')
        self.assertIsInstance(tv[1][1], float)
        self.assertIsInstance(tv[1][2], int)

    def test_create_output_report(self):
        path = "./test"
        self.assertEqual(os.path.exists(path), True)
        date = "20170723"
        file_name = path + '/report-' + "2017.07.23" + '.html'
        self.assertEqual(os.path.isfile(file_name), False)
        main.create_output_report(path, date, "sdasdasd")
        self.assertEqual(os.path.isfile(file_name), True)
