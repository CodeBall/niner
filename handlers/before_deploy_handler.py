from .common_handler import CommonHandler
from core.before_deploy import BeforeDeploy
from config import BEFORE_DEPLOY as _BEFORE_DEPLOY


class BeforeDeployHandler(CommonHandler):
    def get(self):
        before_deploy = BeforeDeploy()
        from_branch = _BEFORE_DEPLOY["FROM_BRANCH"]
        to_branch = _BEFORE_DEPLOY["TO_BRANCH"]

        # Step 1. pull master from remote master
        before_deploy.pull(from_branch)

        # Step 2. pull release from remote release
        before_deploy.pull(to_branch)

        # Step 3. merge master to release
        before_deploy.do_merge(from_branch, to_branch)

        # Step 4. get last commit content
        last_commit_content = before_deploy.get_last_commit(to_branch)

        # Step 5. get last tag name
        last_tag_name = before_deploy.get_last_release_tag(to_branch)

        nums = last_tag_name[1:].split('.')
        nums[2] = str(int(nums[2]) + 1)

        next_tag_name = 'r' + '.'.join(nums)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        return self.finish({"last_commit_content": last_commit_content, "next_tag_name": next_tag_name})

    def post(self):
        tag_id = self.get_argument("tag_id")
        tag_m = self.get_argument("tag_m")

