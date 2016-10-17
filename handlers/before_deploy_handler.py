from .common_handler import CommonHandler
from core.before_deploy import Synchronize

import re


class BeforeDeployHandler(CommonHandler):
    def get(self):
        before_deploy = Synchronize()

        last_commit_content, last_tag_name = before_deploy.get_info()

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

        before_deploy = Synchronize()

        before_deploy.release(tag_id, tag_m)

        return self.finish({"msg": "更新分支成功,请等待发布"})


