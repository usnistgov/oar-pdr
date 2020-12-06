"""
package that provides enables editing of authors with in the NERDm metadata of an AIP bag.
See nistoar.pdr.cli and the pdr script for info on the general CLI infrastructure.

This module defines a set of subcommands to a command called (by default) "author".  These subcommands
include
  - add:  appends an author the current list
  - edit: updates author data for an author currently in the list
  - list: display the current authors in the author list, in order.
"""
from __future__ import print_function
import sys, os, logging, re
from collections import OrderedDict
from copy import deepcopy

from nistoar.pdr import cli
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.nerdm import PUB_SCHEMA_URI
from . import validate as vald8, define_pub_opts, determine_bag_path
# from . import add, edit

default_name = "authors"
help = "add, update, and display author metadata within the AIP"
description = """
  This command provides a suite of subcommands to add, update, or display author metadata within an AIP bag.
"""

def load_into(subparser, as_cmd=None):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    """
    p = subparser
    p.description = description

    if not as_cmd:
        as_cmd = default_name
    out = cli.CommandSuite(as_cmd, p)
    out.load_subcommand( AddAuthorCmd())
    out.load_subcommand(EditAuthorCmd())
    out.load_subcommand(ListAuthorCmd())
    return out

class AuthorCmd(object):
    """
    a base class for author commands.  An instance of this class serves the same role as a command
    submodule in the PDRCLI framework.
    """

    def __init__(self, cmdname, logger=None):
        self.name = cmdname
        if not logger:
            logger = logging.getLogger(self.default_name)
        self.deflog = logger

    @property
    def default_name(self):
        """
        the name this command get invoked by.   This property is part of the standard PDRCLI interface
        """
        return self.name

    def define_common_opts(self, subparser):
        """
        Add arguments to the parser that is common across all commands
        :param ArgumentParser subparser:   the argparse subparser instance to add options to 
        """
        return define_pub_opts(subparser)

    def define_data_opts(self, subparser):
        """
        Add arguments to the parser used to provide data that will go into an author record
        :param ArgumentParser subparser:   the argparse subparser instance to add options to 
        """
        g = subparser.add_argument_group("data entry options")
        g.add_argument("-f", "--family-name", metavar="FAMILY", type=str, dest="family",
                       help="add FAMILY as the author's familty name")
        g.add_argument("-g", "--given-name", metavar="GIVEN", type=str, dest="given",
                       help="add GIVEN as the author's given name (or names or initials)")
        g.add_argument("-m", "--middle-name", metavar="MID", type=str, dest="middle",
                       help="add MIDDLE as the author's middle name or names or initials")
        g.add_argument("--delete-middle-name", action="store_true", dest="delmiddle",
                       help="deleted the middle name (ignored if -m is given)")
        g.add_argument("-o", "--orcid", metavar="ID", type=str, dest="orcid",
                       help="add ID as the author's ORCID identifier")
        g.add_argument("-i", "--institution", "--affiliation", metavar="INST [SUBUNIT ...]", 
                       action="append", nargs="+", dest="affil",
                       help="add INST as the author's institutional affiliation.  INST [SUBUNIT ...] is "+ 
                            "one or more quoted names, where the first is the name of the institution as "+
                            "a whole and subsequent names identify subunits of the institution.  Use this "+
                            "option multiple times to set multiple institutions.  Provide \"NIST\" for INST "+
                            "to enable special handling of the NIST institution.")
        g.add_argument("-n", "--full-name", metavar="NAME", type=str, dest="fn",
                       help="add NAME as the rendering of the full name")
        g.add_argument("-E", "--assume-full-name", action="store_true", dest="deffn",
                       help="set the author's full name from the component name using the "+
                            "GIVEN-MIDDLE-FAMILY convention")
        return g
        
    def define_select_opts(self, subparser, to="operate on"):
        """
        add arguments/options used to edit a particular author's data.  This are primarily options
        used to identify the already added author that should be updated.
        """
        p = subparser
        g = p.add_argument_group("author selection options")
        g.add_argument("-k", "--select-key", dest="selkey", metavar="KEY", type=str, 
                       help="select the authors to "+to+" that currently have values which contain "+
                            "KEY as a whole word")
        g.add_argument("-F", "--select-on-family-name", action="append_const", dest="select", const="f",
                       help="select the author if KEY appears in the author's family name")
        g.add_argument("-G", "--select-on-given-name", action="append_const", dest="select", const="g",
                       help="select the author if KEY appears in the author's given name")
        g.add_argument("-M", "--select-on-middle-name", action="append_const", dest="select", const="m",
                       help="select the author if KEY appears in the author's middle name")
        g.add_argument("-N", "--select-on-full-name", action="append_const", dest="select", const="n",
                       help="select the author if KEY appears in the author's full name")
        g.add_argument("-O", "--select-on-orcid", action="append_const", dest="select", const="o",
                       help="select the author if KEY appears in the author's ORCID")
        g.add_argument("-I", "--select-on-institution", action="append_const", dest="select", const="a",
                       help="select the author if KEY appears in the author's affiliation (incl. subunits)")
        g.add_argument("-U", "--select-on-subunit", action="append_const", dest="select", const="u",
                       help="select the author if KEY appears in any subunit of the author's affiliation")
        g.add_argument("-u", "--force-unique-match", action="store_true", dest="unique",
                       help="require that only one author is matched; if key matches multiple authors, the "+
                            "command will fail and no update is done")

    def select_authors(self, key, selection, authors):
        """
        return the the authors from the given list that match a given key
        :param str key:   a string to look for within fields of each of the authors
        :param str-list selection:  the list of string codes indicating which properties within the author
                          objects to look for the key in.  If None or empty, all fields will be searched
        :parma dict-list authors:   the full list of NERDm-encoded authors to search
        :rtype dict-list:  
        :return: the list of matching authors
        """
        if not key:
            return authors

        word = re.compile(r"\b"+key+r"\b")
        if not selection:
            selection = 'f g m n o a u'.split()
        out = []
        for auth in authors:
            if ('n' in selection and word.search(auth.get("fn", "")))   or \
               ('f' in selection and word.search(auth.get("familyName", "")))  or \
               ('g' in selection and word.search(auth.get("givenName", "")))  or \
               ('m' in selection and word.search(auth.get("middleName", ""))) or \
               ('o' in selection and word.search(auth.get("orcid", ""))):
                out.append(auth)
            elif 'a' in selection or 'u' in selection:
                for affil in auth.get("affiliation", []):
                    if ('a' in selection and word.search(affil.get('title', ""))) or \
                       any([bool(word.search(u)) for u in affil.get("subunits", [])]):
                        out.append(auth)
                        break;

        return out

    def _fail(self, message, exitcode=1):
        raise cli.PDRCommandFailure(self.default_name, message, exitcode)

    def update_auth_data(self, author, args):
        """
        update the given NERDm author object with the values contained args
        """
        if args.family:
            author['familyName'] = args.family
        if args.given:
            author['givenName']  = args.given
        if args.middle:
            author['middleName'] = args.middle
        if args.orcid:
            author['orcid'] = args.orcid

        if args.delmiddle:
            del author['middleName']

        if args.fn:
            author['fn'] = args.fn
        elif args.deffn:
            author['fn'] = ''
            if author.get('givenName'):
                author['fn'] += author['givenName']
            if author.get('middleName'):
                if author['fn']: author['fn'] += ' '
                author['fn'] += author['middleName']
            if author.get('familyName'):
                if author['fn']: author['fn'] += ' '
                author['fn'] += author['familyName']

        if args.affil:
            author['affiliation'] = []
            for affil in args.affil:
                data = OrderedDict([('@type', "org:Organization"), ('title', affil[0])])
                affilid = lookup_inst_id(affil[0])
                if affilid:
                    data['@id'] = affilid
                if affil[0] == "NIST":
                    data['title'] = "National Institute of Standards and Technology"
                if len(affil) > 1:
                    data['subunits'] = affil[1:]
                author['affiliation'].append(data)

        if '@type' not in author:
            author['@type'] = "foaf:Person"

        return author

    def update_to_datapub(self, nerdm):
        """
        return an object with the necessary properties that would update the resource type of the 
        given NERDm record to DataPublication.  If the record is already of this type, the returned 
        object will be empty; otherwise, it will include two properties: updated "@id" and 
        "_extensionSchemas". 
        """
        def pos_of(lookfor, intypes):
            found = [t[0] for t in enumerate(intypes) if lookfor in t[1]]
            return (len(found) == 0 and -1) or found[0]

        def det_metaprefix(nerdm):
            if '_extensionSchemas' in nerdm or '_schema' in nerdm:
                return '_'
            if '$schema' in nerdm or '$extensionSchemas' in nerdm:
                return '$'
            return '_'

        out = OrderedDict()
        if not any([":DataPublication" in t for t in nerdm.get('@type',[])]):
            # okay, this is not yet a DataPublication; find a good position in the types list to add it
            insertpt = -1
            for lookfor in ":PublicDataResource :Dataset".split():
                insertpt = pos_of(lookfor, nerdm.get('@type',[]))
                if insertpt >= 0:
                    break
            if insertpt < 0:
                insertpt = 0

            # add it in
            out['@type'] = deepcopy(nerdm.get('@type',[]))
            out['@type'].insert(insertpt, "nrdp:DataPublication")

        if out:
            # make sure extensionSchemas has the associated schema
            tag = det_metaprefix(nerdm) + "extensionSchemas"
            schmas = deepcopy(nerdm.get(tag, []))
            if not any([u.endswith("/DataPublication") for u in schmas]):
                # remove the schema for PublicDataResource (as it would be redundant)
                oldidx = pos_of("/PublicDataResource", schmas)
                if oldidx >= 0:
                    del schmas[oldidx]

                # replace it with that for DataPublication
                schmas.append(PUB_SCHEMA_URI + "#/definitions/DataPublication")
                out[tag] = schmas

            # make sure Dataset is among the types
            if "dcat:Dataset" not in out.get('@type',[]):
                out['@type'].append("dcat:Dataset")

        elif pos_of(":Dataset", nerdm.get('@type',[])) < 0:
            # make sure Dataset is among the types
            out['@type'] = deepcopy(nerdm.get('@type',[]))
            out['@type'].append("dcat:Dataset")

        return out
        
            
NIST_AFFIL_ID = "ror:05xpvk416"
def lookup_inst_id(affilname):
    if not affilname:
        return None
    if "NIST" in affilname or "National Institute of Standards and Technology" in affilname:
        return NIST_AFFIL_ID
    return None

class AddAuthorCmd(AuthorCmd):
    """
    a CLI command for adding authors to NERDm metadata for a bag
    """
    _default_name = "add"
    description = """
       This command appends a new author to the NERDm authors list with metadata provided via 
       options
    """
    help = "add an author to the NERDm author list"
    
    def __init__(self, cmdname=None):
        if not cmdname:
            cmdname = self._default_name
        super(AddAuthorCmd, self).__init__(cmdname)

    def load_into(self, subparser):
        """
        load the command-line arguments into the subparser
        """
        p = subparser
#        p.usage = p.prog + " [-h] [-b DIR] AIPID\n" + (' ' * (len(p.prog)+7)) + \
#                           " [-f FAMILY] [-g GIVEN] [-m MID] [-o ID]\n" + (' ' * (len(p.prog)+7)) + \
#                           " [-i [INST [SUBUNIT ...]]] [-n NAME]"
        self.define_common_opts(p)
        p.add_argument("-V", "--validate", action="store_true", dest="validate",
                       help="validate the NERDm metadata after update.")
        p.add_argument("-a", "--as-annotations", action="store_true", dest="asannots",
                       help="save the updated version and history as annotations")
        self.define_data_opts(p)
        return self

    def execute(self, args, config=None, log=None):
        if not log:
            log = self.log
        if not config:
            config = {}

        if isinstance(args, list):
            # cmd-line arguments not parsed yet
            p = argparse.ArgumentParser()
            self.load_into(p)
            args = p.parse_args(args)

        if not args.aipid:
            raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
        args.aipid = args.aipid[0]
        usenm = args.aipid
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        log = log.getChild(usenm)
    
        # find the input bag
        workdir, bagparent, bagdir = determine_bag_path(args, config)
        if not os.path.isdir(bagdir):
            self._fail("Input bag does not exist (as a dir): "+bagdir, 2)
        log.info("Found input bag at "+bagdir)

        author = OrderedDict()
        self.update_auth_data(author, args)

        msg = "Updated author metadata"
        bldr = BagBuilder(os.path.dirname(bagdir), os.path.basename(bagdir), logger=log)
        try:
            nerd = bldr.bag.nerd_metadata_for('', args.asannots)
            authors = nerd.get('authors', [])
            authors.append(author)

            update = { 'authors': authors }
            update.update(self.update_to_datapub(nerd))
            if args.asannots:
                bldr.update_annotations_for('', update, message=msg+" (to annotations)")
            else:
                bldr.update_metadata_for('', update, message=msg)
        finally:
            bldr.disconnect_logfile()
        
        # validate the update if requested
        if args.validate:
            vald8.validate_nerdm_for(bag, '', log, args.asannots, "Updated metadata is valid")

        
class EditAuthorCmd(AuthorCmd):
    """
    a CLI command for editing existing authors to NERDm metadata for a bag
    """
    _default_name = "edit"
    description = """
       This command edits the metadata describing one or more author to the NERDm authors list with 
       values provided via options.  KEY and selection options are used to select which authors are updated.
       If -u/--force-unique-match is used, then the KEY must match only one author for the edits to be 
       applied.  
    """
    help = "edit the NERDm metadata of one or more authors in the author list"
    
    def __init__(self, cmdname=None):
        if not cmdname:
            cmdname = self._default_name
        super(EditAuthorCmd, self).__init__(cmdname)

    def load_into(self, subparser):
        """
        load the command-line arguments into the subparser
        """
        p = subparser
#        p.usage = p.prog + " [-h] [-b DIR] AIPID\n" + (' ' * (len(p.prog)+7)) + \
#                           " [-f FAMILY] [-g GIVEN] [-m MID] [-o ID]\n" + (' ' * (len(p.prog)+7)) + \
#                           " [-i [INST [SUBUNIT ...]]] [-n NAME]\n" + (' ' * (len(p.prog)+7)) + \
#                           " [KEY] [-FGMNOAU] [-u]"
        self.define_common_opts(p)
        p.add_argument("-V", "--validate", action="store_true", dest="validate",
                       help="validate the NERDm metadata after update.")
        p.add_argument("-a", "--as-annotations", action="store_true", dest="asannots",
                       help="save the updated version and history as annotations")
        self.define_data_opts(p)
        self.define_select_opts(p, "update")
        return self

    def execute(self, args, config=None, log=None):
        if not log:
            log = self.log
        if not config:
            config = {}

        if isinstance(args, list):
            # cmd-line arguments not parsed yet
            p = argparse.ArgumentParser()
            self.load_into(p)
            args = p.parse_args(args)

        if not args.aipid:
            raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
        args.aipid = args.aipid[0]
        usenm = args.aipid
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        log = log.getChild(usenm)
    
        # find the input bag
        workdir, bagparent, bagdir = determine_bag_path(args, config)
        if not os.path.isdir(bagdir):
            self._fail("Input bag does not exist (as a dir): "+bagdir, 2)
        log.info("Found input bag at "+bagdir)

        # select the authors to edit
        bag = NISTBag(bagdir)
        nerd = bag.nerd_metadata_for('', args.asannots)
        authors = nerd.get("authors", [])
        if len(authors) == 0:
            self._fail("Unable to select authors; none have been added yet", 3)

        selected = self.select_authors(args.selkey, args.select, authors)
        if len(selected) == 0:
            self._fail("No matching authors found", 3)
        if args.unique and len(selected) > 1:
            self._fail("Selection matches multiple authors (when only 1 requested)", 3)

        for auth in selected:
            self.update_auth_data(auth, args)

        # save the updates
        msg = "Updated author metadata"
        update = { 'authors': authors }
        update.update(self.update_to_datapub(nerd))

        bldr = BagBuilder(os.path.dirname(bagdir), os.path.basename(bagdir), logger=log)
        try:
            if args.asannots:
                bldr.update_annotations_for('', update, message=msg+" (to annotations)")
            else:
                bldr.update_metadata_for('', update, message=msg)
        finally:
            bldr.disconnect_logfile()

        # validate the update if requested
        if args.validate:
            vald8.validate_nerdm_for(bag, '', log, args.asannots, "Updated metadata is valid")

        
class ListAuthorCmd(AuthorCmd):
    """
    a CLI command for editing existing authors to NERDm metadata for a bag
    """
    _default_name = "list"
    description = """
       This command prints out a listing of the authors currently described in the NERDm metadata.
       Selection options can be used to select particular authors; alternatively, one author can be 
       selected for display by its (0-based) position.  
    """
    help = "display all or some of the authors' metadata"
    
    def __init__(self, cmdname=None):
        if not cmdname:
            cmdname = self._default_name
        super(ListAuthorCmd, self).__init__(cmdname)

    def load_into(self, subparser):
        """
        load the command-line arguments into the subparser
        """
        p = subparser
        p.usage = p.prog + "AIPID [-h] [-b DIR] [-a] [-V] [-n N | -k KEY [-FGMNOIU] [-u]]"
        self.define_common_opts(p)
        p.add_argument("-n", "--select-position", metavar="N", type=int, dest="pos", default=-1,
                       help="just show author at position N, where N=0 for the first author")
        self.define_select_opts(p, "list")
        return self

    def execute(self, args, config=None, log=None):
        if not log:
            log = self.log
        if not config:
            config = {}

        if isinstance(args, list):
            # cmd-line arguments not parsed yet
            p = argparse.ArgumentParser()
            self.load_into(p)
            args = p.parse_args(args)

        if not args.aipid:
            raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
        args.aipid = args.aipid[0]
        usenm = args.aipid
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        log = log.getChild(usenm)
    
        if args.pos >= 0 and args.selkey:
            self._fail("Option -n/--select-position is mutually exclusive with KEY selection", 1)
        if args.pos >= 0 and args.select:
            log.warn("Selection options (-FGMOAU) ignored when -n/--select-position is used")

        # find the input bag
        workdir, bagparent, bagdir = determine_bag_path(args, config)
        if not os.path.isdir(bagdir):
            self._fail("Input bag does not exist (as a dir): "+bagdir, 2)
        log.info("Found input bag at "+bagdir)

        # select the authors to edit
        bag = NISTBag(bagdir)
        nerd = bag.nerd_metadata_for('', True)
        authors = nerd.get("authors", [])

        if len(authors) == 0:
            self.tell("No author metadata have been added yet")
            return

        if args.pos >= 0:
            if args.pos >= len(authors):
                self.advise("Author position is out of range")
                authors = []
            else:
                authors = [authors[args.pos]]
                
        elif args.selkey:
            authors = self.select_authors(args.selkey, args.select, authors)

        if len(authors) == 0:
            self.tell("No matching author found")
            return

        for auth in authors:
            self.tell("%s, %s %s" % (auth.get('familyName', "???"), auth.get('givenName',"???"),
                                     auth.get('middleName', '')))
            self.tell("  aka:   %s" % auth.get('fn', '???'))
            self.tell("  ORCID: %s" % auth.get('orcid', '???'))
            for affil in auth.get('affiliation', []):
                self.tell("  from: %s" % affil.get('title', '???'))
                for unit in affil.get('subunits', []):
                    self.tell("        %s" % unit)
                if affil.get('@id'):
                    self.tell("        id: " + affil.get('@id'))
            self.tell("")

    def tell(self, msg):
        print(msg)

    def advise(self, msg):
        print(msg, file=sys.stderr)



        
                      

    


    
