from config import BEFORE_DEPLOY as _BEFORE_DEPLOY, DEBUG as _DEBUG
from .repository import RepositoryException

import logging
import subprocess
import os
import shlex
import uuid
import traceback

logger_server = logging.getLogger("DeployServer.BeforeDeployManager")


class BeforeDeploy:
    def __init__(self):
        self.git_path = _BEFORE_DEPLOY["GIT_PATH"]

    def _run_shell_command(self, command, cwd=None):
        """Inner method to run a shell command

        Run a shell command described in param command and redirect stdout and stderr to a temp text file which
        content will be returned if succeed, else the content will be contained in a RepositoryException raised.

        :param command: content of a shell command.
        :return: stdout/stderr content
        :raise: RepositoryException if failed
        """
        success = True

        command = shlex.split(command)

        tmp_filename = '/tmp/' + str(uuid.uuid4())

        with open(tmp_filename, 'w', encoding='utf-8') as w_tmpfile:
            kwargs = {
                'args': command,
                'stdout': w_tmpfile,
                'stderr': w_tmpfile
            }
            if cwd:
                kwargs['cwd'] = cwd
            return_code = subprocess.call(**kwargs)
            if return_code > 0:
                success = False

        with open(tmp_filename, 'r', encoding='utf-8') as r_tmpfile:
            std_content = r_tmpfile.read()

        os.remove(tmp_filename)

        if not success:
            raise RepositoryException(std_content)
        else:
            return std_content

    def cwd(self, path=None):
        """Change current work directory

        :param path: Target directory to change, using git_path if None
        :return:
        """
        if not path:
            path = self.git_path
        try:
            if os.getcwd() != path:
                logger_server.info("Change current dir to {path}...".format(path=path))
                os.chdir(path)
        except Exception as ex:
            logger_server.info("Fail to change current dir to {path}".format(path=path))
            raise RepositoryException(traceback.print_exc())

    def _change_branch(self, branch):
        """Change branch

        :param branch:Target branch to change
        :return:
        """

        command = "git checkout " + branch

        self.cwd()

        self._run_shell_command(command)

        logger_server.info("checkout branch: " + branch)

    def pull(self, branch):
        """Pull data

        Pull data from remote branch

        :return: pull content text
        """
        self._change_branch(branch)

        command = "git pull --rebase origin " + branch

        logger_server.info("Pull data from github[CMD:{cmd}]...".format(cmd=command))

        pull_content = self._run_shell_command(command=command)

        if _DEBUG:
            logger_server.debug("pull_content:" + pull_content)

        return pull_content

    def do_merge(self, from_branch, to_branch):
        """Do merge

        Merge from from_branch to to_branch
        :param from_branch:
        :param to_branch:
        :return:
        """
        self._change_branch(to_branch)

        command = "git merge " + from_branch

        merge_content = self._run_shell_command(command)

        logger_server.info("git merge " + from_branch)

        if _DEBUG:
            logger_server.debug("merge content:" + merge_content)

    def do_push(self, branch):
        """Do push
        Push branch to remote branch
        :param branch:
        :return:
        """
        self._change_branch(branch)

        command = "git push origin " + branch

        push_content = self._run_shell_command(command)

        logger_server.info("git push origin " + branch)

        if _DEBUG:
            logger_server.debug("push content: " + push_content)

    def get_last_commit(self, branch):
        """Get last commit content

        :param branch: target branch for commit
        :return: commit content
        """
        self._change_branch(branch)

        command = "git log -1 --pretty=format:'%s'"

        logger_server.info("Get last commit content [CMD:{cmd}]...".format(cmd=command))

        last_commit = self._run_shell_command(command=command)

        return last_commit.split('\n')[0]

    def get_last_release_tag(self, branch):
        """Get last release tag

        :return: last release tag
        """
        self._change_branch(branch)

        command = 'git tag -l "v*.*.*"'

        logger_server.info("Get last release tags [CMD:{cmd}]...".format(cmd=command))

        tags = self._run_shell_command(command=command)

        if _DEBUG:
            logger_server.debug("Get release tags: {tags}".format(tags=tags))

        tag_list = tags.split('\n')

        return tag_list[-2]

