from GitHubRepositoryAnalyzer import GitHubRepositoryAnalyzer
import pandas as pd


def analyze_repositories(repo_list_file, output_excel_file):
    # Read repository links from file
    with open(repo_list_file, 'r') as file:
        repo_links = file.readlines()

    # Initialize an empty list to store results
    results_list = []

    # Loop through each repository link
    for link in repo_links:
        print(f'Started analysis for {link} project')

        _, _, _, owner, repo_name = link.strip().split('/')
        analyzer = GitHubRepositoryAnalyzer(owner, repo_name)

        # Analyze the repository
        results, total_score, total_score_sourcerank, stars, py_files_count, total_lines_count, num_contributors, \
        total_contributions, created_date, last_pushed_date = analyzer.analyze_repository()
        link = f'https://github.com/{owner}/{repo_name}'

        # Append the results to the list
        repo_data = {
            'Owner': owner,
            'Repo Name': repo_name,
            'Link': link,
            'Total Score': total_score,
            'Total Score (SourceRank)': total_score_sourcerank,
            'Stars': stars,
            'Python Files Count': py_files_count,
            'Total Lines Count': total_lines_count,
            'Number of Contributors': num_contributors,
            'Total Contributions': total_contributions,
            'Created Date': created_date,
            'Last Pushed Date': last_pushed_date,
            'Request Date': '15.07.2024'
        }

        # Add the detailed results from the dictionary
        repo_data.update(results)

        # Add the repository data to the results list
        results_list.append(repo_data)

    # Create a DataFrame from the results list
    df = pd.DataFrame(results_list)

    # Write the DataFrame to an Excel file
    df.to_excel(output_excel_file, index=False)

# File paths
repo_list_file = 'repo_list.txt'
output_excel_file = 'github_repositories_analysis.xlsx'

# Run the analysis
analyze_repositories(repo_list_file, output_excel_file)
