import sys

from ..base_language import BaseHook


class Language(BaseHook):
    """
    Implementation of a simple hook that can edit the first line of a file.
    """

    COMMAND = [sys.executable, "-m", __name__]

    def __init__(self, hook_config, repo_config):
        self.hook_config = hook_config
        self.repo_config = repo_config

    # def work_on_project(self, project_path):
    #     return SubprocessManager(
    #         command=self.COMMAND,
    #         env={
    #             "HOOK_DIR": self.hook_config.dir,
    #             "HOOK_NAME": self.hook_config.name,
    #             "HOOK_CONFIG": encode(self.hook_config),
    #         },
    #         cwd=project_path,
    #     )


if __name__ == "__main__":
    pass
