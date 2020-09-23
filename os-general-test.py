#!/usr/bin/env python3

from datetime import datetime
import csv
import subprocess
import threading
import time
import tempfile
import os
import shutil
import pprint


class GithubRepo:
    def __init__(
        self, user, repo_name, install_command, build_command, project_path=None
    ):
        self.user = user
        self.repo_name = repo_name
        self.project_path = project_path
        self.install_command = install_command
        self.build_command = build_command

    def repo_path(self):
        return f"https://github.com/{self.user}/{self.repo_name}.git"


repos = [
    GithubRepo("oldboyxx", "jira_clone", ["yarn"], ["yarn", "build"], "client"),
    GithubRepo(
        "gothinkster", "react-redux-realworld-example-app", ["yarn"], ["yarn", "build"]
    ),
    GithubRepo("bbc", "simorgh", ["npm", "install"], ["npm", "run", "build"]),
]

subprocess.call(["git", "clone", "https://github.com/gothinkster/react-redux-realworld-example-app.git"])

# make and change to temp dir
initial_dir = os.getcwd()
temp_dir = tempfile.mkdtemp()
print("temp_dir", temp_dir)  # DEBUG
os.chdir(temp_dir)

test_results = []
for repo in repos:
    print(f"testing repo: {repo.repo_name}...")

    # clone repo
    start_time = time.time()
    subprocess.call(["git", "clone", repo.repo_path()])
    clone_duration = time.time() - start_time
    print("clone_duration", clone_duration)

    # cd into project
    os.chdir(repo.repo_name)
    if repo.project_path:
        os.chdir(repo.project_path)

    # install deps
    start_time = time.time()
    subprocess.call(repo.install_command)
    install_1_duration = time.time() - start_time
    print("install_1_duration", install_1_duration)

    # remove node_modules
    start_time = time.time()
    shutil.rmtree("node_modules")
    rm_node_modules_duration = time.time() - start_time
    print("rm_node_modules_duration", rm_node_modules_duration)

    # re-install deps
    start_time = time.time()
    subprocess.call(repo.install_command)
    install_2_duration = time.time() - start_time
    print("install_2_duration", install_2_duration)

    # build project
    start_time = time.time()
    subprocess.call(repo.build_command)
    build_duration = time.time() - start_time
    print("build_duration", build_duration)

    # remove project
    os.chdir(temp_dir)
    start_time = time.time()
    shutil.rmtree(repo.repo_name)
    rm_project_duration = time.time() - start_time
    print("rm_project_duration", rm_project_duration)

    # save results
    test_results.append(
        {
            "repo_name": repo.repo_name,
            "clone_duration": clone_duration,
            "install_1_duration": install_1_duration,
            "rm_node_modules_duration": rm_node_modules_duration,
            "install_2_duration": install_2_duration,
            "build_duration": build_duration,
            "rm_project_duration": rm_project_duration,
        }
    )

# clean up remaining temp file
os.chdir(initial_dir)
shutil.rmtree(temp_dir)

# write results to csv
file_date_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_file_name = f"os-general-test_{file_date_stamp}.csv"

with open(results_file_name, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=test_results[0].keys())
    writer.writeheader()
    for result in test_results:
        writer.writerow(result)
