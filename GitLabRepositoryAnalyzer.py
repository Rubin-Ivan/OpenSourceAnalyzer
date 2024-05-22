import datetime
import math
import requests


class GitLabRepositoryAnalyzer:
    
    def __init__(self, repo_id, repo_path):
        self.repo_id = repo_id
        self.repo_path = repo_path
        self.base_url = "https://gitlab.com/api/v4"
    
    def basic_info_present(self, repository_data):
        score = 0
        if repository_data.get('description'):
            score += 1
        if repository_data.get('web_url'):
            score += 1
        if repository_data.get('tag_list'):
            score += 1
        return score

    def license_present(self):
        license_list=["LICENSE", "LICENSE.txt", "LICENSE.md", "LICENSE.rst"]
        for license_var in license_list:
            url = f"{self.base_url}/projects/{self.repo_id}/repository/files/{license_var}/raw"
            response = requests.get(url)
            if response.status_code == 200:
                return 1  
        return 0

    def not_brand_new(self, repository_data):
        creation_date = datetime.datetime.strptime(repository_data.get('created_at'), "%Y-%m-%dT%H:%M:%S.%fZ")
        six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
        return int(creation_date < six_months_ago)
    
    def stars(self, repository_data):
        stargazers_count = repository_data.get('star_count', 0)
        if stargazers_count > 0:
            return int(max(0, int(round(math.log(stargazers_count, 10)))))
        else:
            return 0
    
    def contributors(self, repository_data):
        url = f"{self.base_url}/projects/{self.repo_id}/repository/contributors"
        response = requests.get(url)
        contributors_data = response.json()
        total_contributions = sum(contributor.get('commits', 0) for contributor in contributors_data)
        return int(max(0, round(math.log(total_contributions, 10) / 2.0)))
    
    def readme_present(self):
        url = f"{self.base_url}/projects/{self.repo_id}/repository/files/README.md/raw"
        response = requests.get(url)
        return int(response.status_code == 200)
    
    def has_multiple_versions(self):
        url = f"{self.base_url}/projects/{self.repo_id}/releases"
        response = requests.get(url)
        releases = response.json()
        return int(len(releases) > 1)
    
    def has_one_point_oh_version(self):
        url = f"{self.base_url}/projects/{self.repo_id}/releases"
        response = requests.get(url)
        
        if response.status_code == 200:
            try:
                releases = response.json()
                if isinstance(releases, list):
                    for release in releases:
                        tag_name = release.get("tag_name", "")
                        if tag_name.startswith(("v1.", "1", "v2", "2")):
                            return 1
                else:
                    print("Unexpected response format: releases is not a list")
                    print("Response content:", response.content)
            except ValueError:
                print("Failed to parse response as JSON")
                print("Response content:", response.content)
        else:
            print("Failed to fetch releases, status code:", response.status_code)
        
        return 0
    
    def recent_release_last_six_months(self):
        url = f"{self.base_url}/projects/{self.repo_id}/releases"
        response = requests.get(url)
        
        if response.status_code == 200:
            releases = response.json()
            if releases:
                latest_release_date = datetime.datetime.strptime(releases[0]['released_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                return int(latest_release_date > six_months_ago)
            else:
                return 0
        else:
            return 0
    
    def recently_pushed_last_six_months(self, repository_data):
        pushed_at = repository_data.get('last_activity_at', None)
        if pushed_at:
            last_pushed_date = datetime.datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
            return int(last_pushed_date > six_months_ago)
        else:
            return 0
    
    def test_folders_exist(self):
        url = f"{self.base_url}/projects/{self.repo_id}/repository/tree"
        response = requests.get(url)
        
        if response.status_code == 200:
            contents = response.json()
            test_found = False
            tests_found = False
            for item in contents:
                if item.get("type") == "tree" and item.get("name") == "test":
                    test_found = True
                elif item.get("type") == "tree" and item.get("name") == "tests":
                    tests_found = True
            
            return int(test_found or tests_found)
        else:
            print("Ошибка при запросе 2:", response.status_code)
            return 0
    
    def tutorial_folders_exist(self):
        url = f"{self.base_url}/projects/{self.repo_id}/repository/tree"
        response = requests.get(url)
        
        if response.status_code == 200:
            contents = response.json()
            tut_found = False
            for item in contents:
                if item.get("type") == "tree" and item.get("name") in ["tutorials", "examples", "notebooks"]:
                    tut_found = True
            return int(tut_found)
        else:
            print("Ошибка при запросе 3:", response.status_code)
            return 0
    
    def community_score(self):
        url = f"{self.base_url}/projects/{self.repo_id}/repository/tree?per_page=100&page=1"
        response = requests.get(url)
        
        if response.status_code == 200:
            contents = response.json()
            score = 0
            files = {item.get("name").lower() for item in contents if item.get("type") == "blob"}
            
            if "code_of_conduct.md" in files:
                score += 1
            
            if "contributing.md" in files:
                score += 1
            
            if "issue_template.md" in files:
                score += 1
            
            if "merge_request_template.md" in files:
                score += 1
            
            return score
        else:
            print("Ошибка при запросе списка файлов. Код ошибки:", response.status_code)
            return 0

    def analyze_repository(self):
        url = f"{self.base_url}/projects/{self.repo_id}"
        response = requests.get(url)
        repository_data = response.json()
        
        results = {
            "Basic Info Present": self.basic_info_present(repository_data),
            "License Present": self.license_present(),
            "Not Brand New": self.not_brand_new(repository_data),
            "Stars": self.stars(repository_data),
            "Contributors": self.contributors(repository_data),
            "Readme Present": self.readme_present(),
            "Has Multiple Versions": self.has_multiple_versions(),
            "Has 1.0.0 Version or Greater": self.has_one_point_oh_version(),
            "Recent Release Last Six Months": self.recent_release_last_six_months(),
            "Recently Pushed Last Six Months": self.recently_pushed_last_six_months(repository_data),
            "Test Folder": self.test_folders_exist(),
            "Tutorials Folder": self.tutorial_folders_exist(),
            "Community Score": self.community_score()
        }
        
        print(results)
        
        total_score_sourcerank = sum(value for key, value in results.items() if key not in ["Test Folder", "Tutorials Folder", "Community Score"])
        total_score = sum(results.values())
        
        return results, total_score, total_score_sourcerank