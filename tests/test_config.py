MY_ADVICE_REPO = "https://github.com/thatch/hobbyhorse"

ICK_TOML_CFG = """
[[mount]]
url = {MY_ADVICE_REPO}
"""


# def test_defaults():
#     m = MainConfig(MY_ADVICE_REPO)
#     assert m.advice_repo == MY_ADVICE_REPO
#     assert "pyproject.toml" in m.project_root_markers
#     assert not m.skip_project_root_in_repo_root
#
#
# def test_project_root_markers_extend():
#     m = MainConfig("", project_root_markers_extend=["BLAH"])
#     assert "pyproject.toml" in m.project_root_markers
#     assert "BLAH" in m.project_root_markers
#
#     m = RepoConfig("", project_root_markers_extend=["BLAH"])
#     assert "pyproject.toml" in m.project_root_markers
#     assert "BLAH" in m.project_root_markers
