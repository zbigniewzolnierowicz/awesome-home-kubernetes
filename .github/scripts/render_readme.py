import jinja2
import json
import os
import sys
import urllib.parse

SOURCEGRAPH_SEARCH_URL = "https://sourcegraph.com/search"
RESULTCOUNT = 2000
DATA_FILE = 'data.json'
DATA_PATH = os.path.join(os.getcwd(), DATA_FILE)
TEMPLATE_FOLDER = os.path.join(os.getcwd(), 'templates')
TEMPLATE_FILE = 'README.md.j2'
TEMPLATE_PATH = os.path.join(TEMPLATE_FOLDER, TEMPLATE_FILE)

# TODO: Check if file exists, otherwise exit with error
if os.path.isfile(DATA_PATH):
  with open(DATA_PATH, 'r') as data_file:
    json_data = json.load(data_file)
else:
  print(f"No data file present. Please provide {DATA_PATH}")
  sys.exit(1)

if not os.path.isfile(TEMPLATE_PATH):
  print(f"No template file present. Please provide {TEMPLATE_PATH}")
  sys.exit(1)

def massage_data():
  # Sort repositories
  json_data['user_repositories'] = sorted(json_data['user_repositories'], key=lambda d: d['repo'].lower())
  json_data['chart_repositories'] = sorted(json_data['chart_repositories'], key=lambda d: d['repo'].lower())
  
  # Add Github URL if no URL attribute is set
  for user_repo in json_data['user_repositories']:
    if not 'url' in user_repo or not user_repo['url']:
      user_repo['url'] = f"https://github.com/{user_repo['repo']}"

  for chart_repo in json_data['chart_repositories']:
    if not 'url' in chart_repo or not chart_repo['url']:
      chart_repo['url'] = f"https://github.com/{chart_repo['repo']}"

def build_sourcegraph_repo_search_url(repositories):
  repos = []
  for repo in repositories:
    repos.append(f"repo:^github\.com/{repo['repo']}$")

  params = {
    'q': f"({' or '.join(repos)}) count:{RESULTCOUNT}",
    'patternType': 'literal'
  }

  return f"{SOURCEGRAPH_SEARCH_URL}?{urllib.parse.urlencode(params)}" 

def build_sourcegraph_user_search_url(repositories):
  repos = []
  for repo in repositories:
    user = repo['repo'].split("/")[0]
    repos.append(f"repo:^github\.com/{user}/.*")

  params = {
    'q': f"({' or '.join(repos)}) count:{RESULTCOUNT}",
    'patternType': 'literal'
  }

  return f"{SOURCEGRAPH_SEARCH_URL}?{urllib.parse.urlencode(params)}" 

def render_readme_template():
  env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_FOLDER))
  template = env.get_template(TEMPLATE_FILE)
  output = template.render(
    user_repo_search_url=build_sourcegraph_repo_search_url(json_data['user_repositories']),
    user_search_url=build_sourcegraph_user_search_url(json_data['user_repositories']),
    chart_repo_search_url=build_sourcegraph_repo_search_url(json_data['chart_repositories']),
    chart_user_search_url=build_sourcegraph_user_search_url(json_data['chart_repositories']),
    user_repositories=json_data['user_repositories'],
    chart_repositories=json_data['chart_repositories']
  )
  return output

def main():
  massage_data()
  print(render_readme_template())
  return 0

if __name__ == '__main__':
  sys.exit(main())
