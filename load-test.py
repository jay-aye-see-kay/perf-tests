#!/usr/bin/env python3

from datetime import datetime
import csv
import subprocess
import threading
import time


# - open chrome and devtools
# - log into preprod as sk
# - enter the url in this curl command
# - right click on the request it makes in the network tab and `copy as curl`
# - paste here into `curl_cmd` so it has all the right headers and an auth token
curl_cmd = """curl 'https://preprod.cultureamp.com/api/pdf-renderer?path=/surveys/5e73052ca8c5400027a27bb0/activity' \
  -H 'authority: preprod.cultureamp.com' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-user: ?1' \
  -H 'sec-fetch-dest: document' \
  -H 'referer: https://preprod.cultureamp.com/surveys/5e73052ca8c5400027a27bb0/activity' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'cookie: __td_signed=false; amplitude_id_6cfe80b109d58db414efa2dbae828525cultureamp.com=eyJkZXZpY2VJZCI6IjIzZmI2ZTMxLTZhYTctNDkxOC05ZWEzLTBiYWVkNDEzMWUyMFIiLCJ1c2VySWQiOiIzZTY5NzgzMi02NzViLTQxMzMtYjkyZS01NmM4NWUzOTY0MzgiLCJvcHRPdXQiOmZhbHNlLCJzZXNzaW9uSWQiOjE1OTQ3OTcwMDE0NTUsImxhc3RFdmVudFRpbWUiOjE1OTQ3OTcwMDE0NTUsImV2ZW50SWQiOjgsImlkZW50aWZ5SWQiOjEwLCJzZXF1ZW5jZU51bWJlciI6MTh9; intercom-session-38afd9dceaebb66280bb1e276f21286862b6727a=MkFyM2REUDV3ODJlNVNyR1ZlejVSYUdLRm9YZC92eE5SS0xnTGNDTlR0emc2WHNqdXFVRFhhN3lsUXBkRk9wZi0tRjZPZmNENFhQMGw1elJjQ093UzJFZz09--004703234219c36fa112e8a0793b12878d9917d2; _murmur_session_staging=fc860e246544d18a728d6843b1a59910; amplitude_id_ebe34b05f57a2a074057e1c18183de28cultureamp.com=eyJkZXZpY2VJZCI6IjZhNTcyOWZiLTc1OTgtNGRkNC1hMWNiLTUyYTJhOTYwNDQyYVIiLCJ1c2VySWQiOiI3YTQzNDMxNC0xNzY4LTRlZmQtYTcyNC1jYjc1OGRiYTEwYjUiLCJvcHRPdXQiOmZhbHNlLCJzZXNzaW9uSWQiOjE1OTUyMjA5NTI3NzksImxhc3RFdmVudFRpbWUiOjE1OTUyMjA5NTc1NTIsImV2ZW50SWQiOjYsImlkZW50aWZ5SWQiOjE4LCJzZXF1ZW5jZU51bWJlciI6MjR9; _td=7a434314-1768-4efd-a724-cb758dba10b5; intercom-session-efqodl01=Z3U2cW1LVG40QThBQ3AyNktFVGI3dUdRdlk1Uis0QncraTdOMVFaM3VIUDRKZlJBeEJ1aXVlcmQzU1VxVzN0NC0tMmtnNTJSKzBuek1QaFBIRmVtSUNiUT09--efd97e553c2611eb7b83fe2e4f473fe25676143e' \
  -H 'if-none-match: W/"6517-tPVquu5DXBYkIyZY2enkF+iPUm0"' \
  --compressed"""


# list of all completed requests (shared between threads)
test_results = []

class CurlAPdfInAThread (threading.Thread):
   def __init__(self, thread_id, min_duration_sec, num_threads):
      threading.Thread.__init__(self)
      self.thread_id = thread_id
      self.min_duration_sec = min_duration_sec
      self.num_threads = num_threads

   def run(self):
      thread_start_time = time.time()
      thread_duration = 0
      while thread_duration < self.min_duration_sec:
          request_start_time = time.time()

          exit_code = subprocess.call(curl_cmd + " --silent > /dev/null", shell=True)
          if exit_code != 0:
              print(f'curl returned non-zero in {self.name}, exiting thread')
              break

          end_time = time.time()
          request_duration = end_time - request_start_time
          thread_duration = end_time - thread_start_time
          test_results.append({
              'num_threads': self.num_threads,
              'request_duration_sec': request_duration,
              'thread_id': self.thread_id,
              'request_start_time': request_start_time,
              'request_end_time': end_time,
          })


# {{{ run tests
class TestPlan:
    def __init__(self, min_duration_sec, num_threads):
        self.min_duration_sec = min_duration_sec
        self.num_threads = num_threads

test_plans = [
    TestPlan(180, 1),
    TestPlan(180, 3),
    TestPlan(180, 10),
    TestPlan(180, 30),
    TestPlan(180, 50),
    TestPlan(180, 100),
]

for plan_index, test_plan in enumerate(test_plans):
    threads = []
    for thread_index in range(test_plan.num_threads):
        t = CurlAPdfInAThread(thread_index, test_plan.min_duration_sec, test_plan.num_threads)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
# }}}


# {{{ write results to csv
file_date_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_file_name = f'pdf-load-test_{file_date_stamp}.csv'

with open(results_file_name, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=test_results[0].keys())
    writer.writeheader()
    for result in test_results:
        writer.writerow(result)
# }}}
