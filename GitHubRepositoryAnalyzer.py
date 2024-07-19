import datetime
import math
import requests

import zipfile
import os
from io import BytesIO


class GitHubRepositoryAnalyzer:

    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo
        self.headers = {
            'Authorization': f'token {"TOKEN"}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def basic_info_present(self, repository_data):
        score = 0
        if repository_data.get('description'):
            score += 1
        if repository_data.get('homepage'):
            score += 1
        if repository_data.get('topics'):
            score += 1
        return score

    def license_present(self, repository_data):
        return int(bool(repository_data.get('license')))
    
    def not_brand_new(self, repository_data):
        creation_date = datetime.datetime.strptime(repository_data.get('created_at'), "%Y-%m-%dT%H:%M:%SZ")
        six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)


        return int(creation_date < six_months_ago), creation_date


    def stars_clear(self, repository_data):
        return repository_data.get('stargazers_count', 0)

    def forks_count(self, repository_data):
        return repository_data.get('forks_count', 0)

    def issues_count(self, repository_data):
        return repository_data.get('open_issues', 0)

    def size(self, repository_data):
        return repository_data.get('size', 0)
        


    def stars(self, repository_data):
        stargazers_count = repository_data.get('stargazers_count', 0)
        if stargazers_count > 0:
            return int(max(0, int(round(math.log(stargazers_count, 10)))))
        else:
            return 0
    
    def contributors(self, repository_data):
        contributors_url = repository_data.get('contributors_url')
        response = requests.get(contributors_url, headers=self.headers)

        if response.status_code == 200:
            contributors_data = response.json()
            num_contributors = len(contributors_data)
            total_contributions = sum(contributor.get('contributions', 0) for contributor in contributors_data)
            contributors_log = int(max(0, round(math.log(total_contributions, 10) / 2.0)))
            return contributors_log, num_contributors , total_contributions
        else:
            print(f"Не удалось получить информацию о контрибьюторах. Статус код: {response.status_code}")
            return 0

    def subscribers(self, repository_data):
        return int(max(0, round(math.log(repository_data.get('subscribers_count', 1), 10) / 2.0)))
    
    def readme_present(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/readme"
        response = requests.get(url, headers=self.headers)
        return int(response.status_code == 200)
    
    def has_multiple_versions(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases"
        response = requests.get(url, headers=self.headers)
        releases = response.json()
        return int(len(releases) > 1)
    
    def has_one_point_oh_version(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"
        response = requests.get(url, headers=self.headers)
        latest_release = response.json()
        
        tag_name = latest_release.get("tag_name", "")
        return int(tag_name.startswith(("v1.", "1", "v2", "2")))
    
    def recent_release_last_six_months(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            latest_release = response.json()
            if latest_release:
                last_release_date = datetime.datetime.strptime(latest_release['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                return int(last_release_date > six_months_ago)
            else:
                return 0
        else:
            return 0
    
    def recently_pushed_last_six_months(self, repository_data):
        pushed_at = repository_data.get('pushed_at', None)
        if pushed_at:
            last_pushed_date = datetime.datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
            six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
            
            return int(last_pushed_date > six_months_ago), last_pushed_date
        else:
            return 0
    
    def test_folders_exist(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            contents = response.json()
            test_found = False
            tests_found = False
            for item in contents:
                if item.get("type") == "dir" and item.get("name") == "test":
                    test_found = True
                elif item.get("type") == "dir" and item.get("name") == "tests":
                    tests_found = True
            
            return int(test_found or tests_found)
        else:
            print("Ошибка при запросе:", response.status_code)
            return 0
    
    def tutorial_folders_exist(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            contents = response.json()
            tut_found = False

            for item in contents:
                if item.get("type") == "dir" and item.get("name") in ["tutorials", "examples", "notebooks"]:
                    tut_found = True
            
            return int(tut_found)
        else:
            print("Ошибка при запросе:", response.status_code)
            return 0
    
    def community_score(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/community/profile"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            repository_data = response.json()
            score = 0
            files = repository_data.get("files", {})
            
            if files.get("code_of_conduct") is not None:
                score += 1
            
            if files.get("contributing") is not None:
                score += 1
            
            if files.get("issue_template") is not None:
                score += 1
            
            if files.get("pull_request_template") is not None:
                score += 1
            
            return score
        else:
            print("Ошибка при запросе:", response.status_code)
            return 0
        
    def code_value(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/zipball"
        response = requests.get(url, headers=self.headers)

        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(f"{self.repo}_repo")


            py_files_count = 0
            total_lines_count = 0

            for root, dirs, files in os.walk(f"{self.repo}_repo"):
                for file in files:
                    if (file.endswith(".py") | file.endswith(".kts")):
                        py_files_count += 1
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            total_lines_count += len(lines)

        return (py_files_count, total_lines_count)

    def analyze_repository(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        response = requests.get(url, headers=self.headers)
        repository_data = response.json()
        
        score_contr, num_contributors , total_contributions = self.contributors(repository_data)
        score_not_br_new, created_date= self.not_brand_new(repository_data)
        score_pushed, last_pushed_date= self.recently_pushed_last_six_months(repository_data)
        stars = self.stars_clear(repository_data)
        issues=self.issues_count(repository_data)
        forks = self.forks_count(repository_data)
        size = self.size(repository_data)

        results = {
            "Basic Info Present": self.basic_info_present(repository_data),
            "License Present": self.license_present(repository_data),
            "Not Brand New": score_not_br_new,
            "Stars Log": self.stars(repository_data),
            "Contributors": score_contr,
            "Readme Present": self.readme_present(),
            "Has Multiple Versions": self.has_multiple_versions(),
            "Has 1.0.0 Version or Greater": self.has_one_point_oh_version(),
            "Recent Release Last Six Months": self.recent_release_last_six_months(),
            "Recently Pushed Last Six Months": score_pushed,
            "Test Folder": self.test_folders_exist(),
            "Tutorials Folder": self.tutorial_folders_exist(),
            "Community Score": self.community_score()
        }
        
        py_files_count, total_lines_count=self.code_value()
        
        total_score_sourcerank = sum(value for key, value in results.items() if key not in ["Test Folder", "Tutorials Folder", "Community Score"])
        total_score = sum(results.values())
        
        return results, total_score, total_score_sourcerank, stars, py_files_count, total_lines_count, num_contributors , total_contributions, created_date, last_pushed_date, issues, forks, size

