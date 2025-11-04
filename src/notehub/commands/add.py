from notehub.gh_wrapper import create_issue

def run(args):
    result = create_issue()
    print(f"Note-issue created successfully")
