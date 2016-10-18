from config import BEFORE_DEPLOY as _BEFORE_DEPLOY, DEBUG as _DEBUG
from .repository import RepositoryException, release_tag_cmp

import logging
import subprocess
import os
import shlex
import uuid
import traceback

logger_server = logging.getLogger("DeployServer.BeforeDeployManager")


class Synchronize:
    def __init__(self):
        self.git_path = _BEFORE_DEPLOY["GIT_PATH"]
        self.from_branch = _BEFORE_DEPLOY["FROM_BRANCH"]
        self.to_branch = _BEFORE_DEPLOY["TO_BRANCH"]

    def __run_shell_command(self, command, cwd=None):
        """Inner method to run a shell command

        Run a shell command described in param command and redirect stdout and stderr to a temp text file which
        content will be returned if succeed, else the content will be contained in a RepositoryException raised.

        :param command: content of a shell command.
        :param cwd: path of a shell command
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

    def __cwd(self, path=None):
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

    def __stash(self):

        self.__cwd()

        command = "git stash"

        self.__run_shell_command(command)

        logger_server.info(command)

    def __change_branch(self, branch):
        """Change branch

        :param branch:Target branch to change
        :return:
        """

        command = "git checkout " + branch

        self.__cwd()

        self.__run_shell_command(command)

        logger_server.info("checkout branch: " + branch)

    def __pull(self, branch):
        """Pull data
        Pull data from remote branch

        :param branch: target branch
        :return: pull content text
        """
        self.__change_branch(branch)

        command = "git pull"

        logger_server.info("Pull data from github[CMD:{cmd}]...".format(cmd=command))

        pull_content = self.__run_shell_command(command=command)

        if _DEBUG:
            logger_server.debug("pull_content:" + pull_content)

        return pull_content

    def __merge(self, from_branch, to_branch):
        """merge

        Merge from from_branch to to_branch
        :param from_branch: source branch
        :param to_branch: target branch
        :return:
        """
        self.__change_branch(to_branch)

        command = "git merge " + from_branch

        merge_content = self.__run_shell_command(command)

        logger_server.info("git merge " + from_branch)

        if _DEBUG:
            logger_server.debug("merge content:" + merge_content)

    def __push_branch(self, branch):
        """Do push branch
        Push branch to remote branch
        :param branch: target branch
        :return:
        """
        self.__change_branch(branch)

        command = "git push origin " + branch

        push_content = self.__run_shell_command(command)

        logger_server.info("git push origin " + branch)

        if _DEBUG:
            logger_server.debug("push content: " + push_content)

    def __get_last_commit(self, branch):
        """Get last commit content

        :param branch: target branch for commit
        :return: commit content
        """
        self.__change_branch(branch)

        command = "git log -1 --pretty=format:'%s'"

        logger_server.info("Get last commit content [CMD:{cmd}]...".format(cmd=command))

        last_commit = self.__run_shell_command(command=command)

        return last_commit.split('\n')[0]

    def __get_last_release_tag(self):
        """Get last release tag

        :return: last release tag
        """
        self.__cwd()

        command = 'git tag -l "r*.*.*"'

        logger_server.info("Get last release tags [CMD:{cmd}]...".format(cmd=command))

        tags = self.__run_shell_command(command=command)

        if _DEBUG:
            logger_server.debug("Get release tags: {tags}".format(tags=tags))

        tag_list = tags.split('\n')[:-1]
        tag_list.sort(key=release_tag_cmp, reverse=True)

        try:
            return tag_list[0]
        except Exception as ex:
            logger_server.info(ex)
            return "r1.1.0"

    def __create_tag(self, tag_id, tag_m):
        """Create Tag

        :param tag_id: The version number
        :param tag_m: description
        :return:
        """

        self.__cwd()

        command = "git tag -a {tag_id} -m '{tag_m}'".format(tag_id=tag_id, tag_m=tag_m)

        logger_server.info(command)

        self.__run_shell_command(command=command)

    def __push_tags(self):

        command = "git push --tags"

        logger_server.info(command)

        self.__run_shell_command(command)

    def get_info(self):
        # Step 1. stash code
        self.__stash()
        # Step 2. pull master from remote master
        self.__pull(self.from_branch)
        # Step 3. pull release from remote release
        self.__pull(self.to_branch)
        # Step 4. merge master to release
        self.__merge(self.from_branch, self.to_branch)
        # Step 5. get last commit content
        last_commit_content = self.__get_last_commit(self.to_branch)
        # Step 6. get get last tag name
        last_tag_name = self.__get_last_release_tag()

        return last_commit_content, last_tag_name

    def release(self, tag_id, tag_m):
        # Step 1. create tag
        self.__create_tag(tag_id, tag_m)
        # Step 2. push tags
        self.__push_tags()
        # Step 3. push branch
        self.__push_branch(self.to_branch)
