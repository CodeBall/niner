__author__ = 'magus0219'
import handlers
from tornado.web import RedirectHandler
from core.deploy_manager import dmc

URLS = [
            # Core Entity
            (r'/event', handlers.DeployHandler),
            (r'/repo/(.*)/(.*)/rollback/(.*)/(.*)', handlers.RollbackHandler),
            (r'/repo/(.*)/(.*)/(.*)', handlers.OperationHandler),
            (r'/repo/(.*)/(.*)', handlers.IndexHandler),
            (r'/repo', RedirectHandler, {"url": "/deploy/repo/{repo_with_branch}".format(
                repo_with_branch=dmc.list_repos_with_branch()[0])}),
            (r'/login', handlers.LoginHandler),
            (r'/logout', handlers.LogoutHandler),
            (r'/register', handlers.RegisterHandler),
            (r'/chpwd', handlers.ChangePasswordHandler),
            (r'/branch/update', handlers.BeforeDeployHandler)
        ]