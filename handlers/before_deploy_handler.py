from .common_handler import CommonHandler
from core.before_deploy import BeforeDeploy
from config import BEFORE_DEPLOY as _BEFORE_DEPLOY

import re


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

        pattern = '^r\d+\.\d+\.\d+$'
        if not re.match(pattern, tag_id):
            return self.finish({"msg": "版本号格式错误,请重新发布"})

        before_deploy = BeforeDeploy()

        # Step 1. create tag
        before_deploy.create_tag(tag_id, tag_m)

        # Step 2. push
        before_deploy.push(_BEFORE_DEPLOY["TO_BRANCH"])

        return self.finish({"msg": "更新分支成功,请等待发布"})


