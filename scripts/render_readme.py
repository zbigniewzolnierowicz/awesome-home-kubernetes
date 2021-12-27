import urllib.parse
import json
import os
import sys
import jinja2

SOURCEGRAPH_SEARCH_URL = "https://sourcegraph.com/search"
RESULTCOUNT = 2000
DATA_FILE = "data.json"
DATA_PATH = os.path.join(os.getcwd(), DATA_FILE)
TEMPLATE_FOLDER = os.path.join(os.getcwd(), "templates")
TEMPLATE_FILE = "README.md.j2"
TEMPLATE_PATH = os.path.join(TEMPLATE_FOLDER, TEMPLATE_FILE)

# TODO: Check if file exists, otherwise exit with error
if os.path.isfile(DATA_PATH):
    with open(DATA_PATH, "r", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
else:
    print(f"No data file present. Please provide {DATA_PATH}")
    sys.exit(1)

if not os.path.isfile(TEMPLATE_PATH):
    print(f"No template file present. Please provide {TEMPLATE_PATH}")
    sys.exit(1)


def massage_data():
    # Sort repositories
    json_data["user_repositories"] = sorted(json_data["user_repositories"], key=lambda d: d["repo"].lower())
    json_data["chart_repositories"] = sorted(json_data["chart_repositories"], key=lambda d: d["repo"].lower())

    # Add Github URL if no URL attribute is set
    for user_repo in json_data["user_repositories"]:
        if not "url" in user_repo or not user_repo["url"]:
            user_repo["url"] = f"https://github.com/{user_repo['repo']}"

    for chart_repo in json_data["chart_repositories"]:
        if not "url" in chart_repo or not chart_repo["url"]:
            chart_repo["url"] = f"https://github.com/{chart_repo['repo']}"


def build_sourcegraph_repo_search_url(repositories):
    repos = []
    for repo in repositories:
        repos.append(rf"repo:^github\.com/{repo['repo']}$")

    params = {"q": f"({' or '.join(repos)}) count:{RESULTCOUNT}", "patternType": "literal"}

    return f"{SOURCEGRAPH_SEARCH_URL}?{urllib.parse.urlencode(params)}"


def build_sourcegraph_user_search_url(repositories):
    repos = []
    for repo in repositories:
        user = repo["repo"].split("/")[0]
        repos.append(rf"repo:^github\.com/{user}/.*")

    params = {"q": f"({' or '.join(repos)}) count:{RESULTCOUNT}", "patternType": "literal"}

    return f"{SOURCEGRAPH_SEARCH_URL}?{urllib.parse.urlencode(params)}"


def generate_gitops_search_urls(repositories):
    gitops_tools = set(repo["gitops_tool"] for repo in repositories if "gitops_tool" in repo)

    output = {}

    for tool in gitops_tools:
        output[tool] = build_sourcegraph_repo_search_url(
            [repo for repo in repositories if "gitops_tool" in repo and repo["gitops_tool"] == tool]
        )

    return output


def render_readme_template():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_FOLDER))

    search_urls = {
        "user_repo": build_sourcegraph_repo_search_url(json_data["user_repositories"]),
        "user_gitops_types": generate_gitops_search_urls(json_data["user_repositories"]),
        "user_code": build_sourcegraph_user_search_url(json_data["user_repositories"]),
        "chart_repo": build_sourcegraph_repo_search_url(json_data["chart_repositories"]),
        "chart_user": build_sourcegraph_user_search_url(json_data["chart_repositories"]),
    }

    template = env.get_template(TEMPLATE_FILE)
    output = template.render(
        user_repositories=json_data["user_repositories"],
        chart_repositories=json_data["chart_repositories"],
        search_urls=search_urls,
    )
    return output


def main():
    massage_data()
    print(render_readme_template())
    return 0


if __name__ == "__main__":
    sys.exit(main())
