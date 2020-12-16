"""
a module for converting a NERDm record into a plain-text README document.  
"""
import textwrap, os
from mako.template import Template

from nistoar.pdr.exceptions import StateException
from nistoar import pdr

class ReadmeGenerator(object):

    def __init__(self, templatedir=None):
        """
        create the generator
        """
        if not templatedir:
            templatedir = self.find_default_templatedir()
        self.templatedir = templatedir

        if not self.templatedir:
            raise StateException("Unable to locate template dir (please specify)")
        if not os.path.isdir(templatedir):
            raise StateException("README template directory does not exist as a directory: "+templatedir)

    @classmethod
    def find_default_templatedir(cls):
        if 'OAR_MAKO_TEMPLATES_DIR' in os.environ:
            return os.path.join(os.environ['OAR_MAKO_TEMPLATES_DIR'], "readme")
        if 'OAR_ETC_DIR' in os.environ:
            return os.path.join(os.environ['OAR_ETC_DIR'], "mako", "readme")
        if pdr.def_etc_dir:
            return os.path.join(pdr.def_etc_dir, "mako", "readme")
        if 'OAR_HOME' in os.environ:
            return os.path.join(os.environ['OAR_HOME'], "etc", "mako", "readme")
        return None
        

    def _get_tmpl8(self, name):
        target = os.path.join(self.templatedir, name+".txt")
        return Template(filename=target)

    class Writer(object):
        def __init__(self, ngn, nerdm, ostrm, templated=False, brief=False):
            self.ngn = ngn  # the ReadmeGenerator
            self.nerdm = nerdm
            self.out = ostrm
            self._withprompts = templated
            self._brief = brief

        def _render_tmpl8(self, tmpl8, data, withprompts=None, brief=None):
            if withprompts is None:
                withprompts = self._withprompts
            if brief is None:
                brief = self._brief
            self.out.write(tmpl8.render(_prompts=withprompts, _brief=brief, nrd=data, **data))

        def apply(self, tmpl8name, data, withprompts=None, brief=None):
            tmpl8 = self.ngn._get_tmpl8(tmpl8name)
            self._render_tmpl8(tmpl8, data)

        def write_front_matter(self):
            self.apply("front_matter", self.nerdm)

        def write_general_info(self):
            self.apply("general_info", self.nerdm)

        def write_data_use(self):
            self.apply("data_use", self.nerdm)

        def write_references(self):
            self.apply("references", self.nerdm)

        def write_version_history(self):
            self.apply("version_history", self.nerdm)

        def write_methods(self):
            self.apply("methods", self.nerdm)

        def write_data_overview(self):
            self.apply("data_overview", self.nerdm)

        def write_readme(self):
            self.write_front_matter()
            self.write_general_info()
            self.write_data_use()
            self.write_references()
            self.write_data_overview()
            self.write_version_history()
            self.write_methods()

        
    def generate(self, nerdm, ostrm, templated=False, brief=False):
        """
        create the README and write it to the given output file stream
        :param dict nerdm:      the NERDm Resource metadata to convert
        :param file ostrm:      the file object to write the README document to.
        :param bool templated:  if true, include prompts where one can edit the document and 
                                  insert additional information
        :param bool brief:      write out an abbreviated version that does not list all of the files
        """
        wrtr = self.Writer(self, nerdm, ostrm, templated, brief)
        wrtr.write_readme()

    
