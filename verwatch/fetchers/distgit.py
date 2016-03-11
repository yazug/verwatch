import os
import rpm
from verwatch.fetchers.git import GitFetcher
from verwatch.util import run


class DistGitFetcher(GitFetcher):
    name = 'distgit'

    def _checkout(self, branch):
        self.cmd = 'git checkout --force "%s"' % branch
        errc, out, err = run(self.cmd)
        if errc:
            raise RuntimeError("git checkout failed: %s" % err or out)
        self.cmd = 'git reset --hard origin/%s' % branch
        errc, out, err = run(self.cmd)
        if errc:
            raise RuntimeError("git reset --hard failed: %s" % err or out)

    def _get_version(self, pkg_name, branch):
        self.cmd = None
        try:
            self._prepare_repo(pkg_name)
            self._checkout(branch)
        except RuntimeError as e:
            return {'error': e.args[0], 'cmd': self.cmd}

        specs = [f for f in os.listdir('.')
                 if os.path.isfile(f) and f.endswith('.spec')]
        if not specs:
            return {'error': "No .spec files found."}
        if len(specs) != 1:
            return {'error': "Multiple .spec files present."}
        spec_fn = specs[0]
        try:
            spec = rpm.ts().parseSpec(spec_fn)
        except ValueError as e:
            return {'error': "Error parsing '%s': %s" % (spec_fn, e.args[0])}
        dist = rpm.expandMacro("%{dist}")
        release = spec.sourceHeader['release']
        if release.endswith(dist):
            release = release[:-len(dist)]
        ver = {
            'version': spec.sourceHeader['version'],
            'release': release,
        }
        if 'epoch' in spec.sourceHeader:
            ver['epoch'] = str(spec.sourceHeader['epoch'])
        return ver
