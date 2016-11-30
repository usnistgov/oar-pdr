"""
A python interface to the PDR's jq-based JSON transformation
"""
import os, json, subprocess as subproc, types

class JqCommand(object):
    """
    a class for calling the jq tool command

    This is general purpose class.  The OAR PDR system is expected to use
    the Jq class, which is more PDR-aware, over this class.  
    """

    def __init__(self, libdir=None, jqpath=None):
        """
        create the command instance

        :param libdir str:   the path directory containing needed jq modules
        :param jqpath str:   the path to the jq executable to use
        """
        self.libargs = []
        if libdir:
            self.library = libdir

        self.jqexe = jqpath
        if not self.jqexe:
            self.jqexe = "jq"

    @property
    def library(self):
        if len(self.libargs) < 1:
            return None
        return self.libargs[0][2:]

    @library.setter
    def library(self, libdir):
        if not os.path.isdir(libdir):
            raise IOError(2, "jq Library Directory Not Found: "+libdir)
        self.libargs = ["-L"+libdir]

    def process_data(self, jqfilter, datastr, args=None):
        """ 
        This executes jq with with given JSON data and returns the 
        converted output.

        :param jqfilter str:  The jq filter to apply to the input
        :param datastr  str:  The input data as a JSON-formatted string
        :param args    dict:  arguments to pass in via --argjson
        """
        argopts = self.form_argopts(args)

        cmd = self.form_cmd(jqfilter, args)
        proc = subproc.Popen(cmd, stdout=subproc.PIPE, stderr=subproc.PIPE,
                             stdin=subproc.PIPE)
        (out, err) = proc.communicate(datastr)

        if proc.returncode != 0:
            raise RuntimeError(err + "\nFailed jq command: " +
                               self._format_cmd(cmd))

        return json.loads(out)

    def process_file(self, jqfilter, filepath, args=None):
        """ 
        This executes jq with JSON data from the given file and returns the 
        converted output.

        :param jqfilter str:  The jq filter to apply to the input
        :param filepath str:  The file containt the input JSON data 
        :param args dict:     arguments to pass in via --argjson
        """
        argopts = self.form_argopts(args)

        cmd = self.form_cmd(jqfilter, args, filepath)
        proc = subproc.Popen(cmd, stdout=subproc.PIPE, stderr=subproc.PIPE)
        (out, err) = proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(err + "\nFailed jq command: " +
                               self._format_cmd(cmd))

        return json.loads(out)

    def _format_cmd(self, cmd):
        for i in range(len(cmd)):
            if len(cmd[i].split()) > 1:
                cmd[i] = "'{0}'".format(cmd[i])
            elif cmd[i].startswith('"') and cmd[i].endswith('"'):
                cmd[i] = "'{0}'".format(cmd[i])
        return " ".join(cmd)

    def form_argopts(self, argdata):
        """
        format the input dictionary into --argjson options
        """
        argopts = []
        if argdata:
            if not isinstance(argdata, dict):
                raise ValueError("args parameter is not a dictionary: "+
                                 str(argdata))
            for name in argdata:
                argopts += [ "--argjson", name, json.dumps(argdata[name]) ]

        return argopts
        
    def form_cmd(self, jqfilter, args=None, infile=None):
        """
        create the command line for executing jq to process data with a 
        given filter.  

        :param jqfilter str:  the jq-compliant transformation filter to use
        :param args dict:     the custom arg data to set (via --argjson)
        :param infile str:    the path to a file with the input JSON data.  If 
                                None (i.e. not provided), it is assumed that 
                                the input data will appear at stdin.
        :returns dict, array or str:  the (parsed) output JSON data 
        """
        cmd = [self.jqexe] + self.libargs + self.form_argopts(args)
        cmd.append(jqfilter)
        if infile:
            cmd.append(infile)

        return cmd

class Jq(object):
    """
    a machine for transforming JSON data using PDR modules

    A Jq instance is constructed with a filter so as to be applied multiple 
    times over multiple documents of the same type.  
    """

    def __init__(self, jqfilter, libpath=None, modules=None, args=None):
        """
        create the Jq filter machine.  

        :param jqfilter str:   the jq filter to apply to the input data; module
                               import statements can be left by using the 
                               modules argument.
        :param libpath str:    the path to the directory containing needed 
                               jq module files
        :param modules array of str:  a list of modules to import as a preface
                               to the given filter
        :param args dict:      a dictionary of data to pass into the jq filter
                               (via the jq --argjson option).
        """
        if modules and not libpath:
            raise ValueError("Missing libpath argument; needed when modules is given")
        self.cmd = JqCommand(libpath)

        modimport = ''
        if modules:
            for mod in modules:
                pref = mod
                if ':' in mod:
                    mod, pref = mod.rsplit(':')
                modimport += 'import "{0}" as {1}; '.format(mod, pref)

        self.filter = modimport + jqfilter
        
        self.args = {}
        if args:
            if not isinstance(args, dict):
                raise ValueError("args paramter not a dict: " + str(args))
            self.args = args.copy()

    def transform(self, datastr, args=None):
        """
        transform the given JSON-formatted data

        :param datastr  str:  The input data as a JSON-formatted string
        :param args dict:      additional data to pass into the transformation,
                               in addition to (and overriding) those set at 
                               construction.  
        """
        use = self.args.copy()
        if args:
            if not isinstance(args, dict):
                raise ValueError("args paramter not a dict: " + str(args))
            use.update(args)
        return self.cmd.process_data(self.filter, datastr, use)

    def transform_file(self, filepath, args=None):
        """
        transform the given JSON-formatted data

        :param filepath str:   the path to a file containing the input JSON data
                               to transform
        :param args dict:      additional data to pass into the transformation,
                               in addition to (and overriding) those set at 
                               construction.  
        """
        use = self.args.copy()
        if args:
            if not isinstance(args, dict):
                raise ValueError("args paramter not a dict: " + str(args))
            use.update(args)
        return self.cmd.process_file(self.filter, filepath, use)
        
    
