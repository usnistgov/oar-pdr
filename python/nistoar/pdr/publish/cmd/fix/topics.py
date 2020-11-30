"""
CLI command that will update to the NERDm topics metadatum with values converted from the 
theme property.  
"""
import logging, argparse, sys, os, shutil, tempfile, json
from copy import deepcopy

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagger.prepupd import UpdatePrepService
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.pdr.utils import write_json
from nistoar.pdr.cli import PDRCommandFailure
from nistoar.pdr import def_schema_dir
from nistoar.nerdm.taxonomy import ResearchTopicsTaxonomy
from .. import validate as vald8

default_name = "topics"
help = "update the research topics based on the values of the themes"
description = """
  update the NERDm topics metadata to include values from the theme property values properly converted 
  into research topics from the NIST Taxonomy saved into the NERDm topics property.  

  Theme values that originate from a POD record can sometimes be inaccurate (e.g. missing levels).  This
  command will attempt to match each theme to a term in the NIST Taxonomy vocabulary and save the values 
  as NERDm topic properties.  
"""

def load_into(subparser):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    :rtype: None
    """
    p = subparser
    p.description = description
    p.add_argument("aipid", metavar="AIPID", type=str, nargs='?', help="the AIP-ID for the bag to examine "+
                   "or the file path to the bag's root directory")
    p.add_argument("-b", "--bag-parent-dir", metavar="DIR", type=str, dest='bagparent',
                   help="the directory to look for the specified bag; if not specified, it will either set "+
                        "to the metadata_bag_dir config or otherwise to the working directory")
    p.add_argument("-p", "--from-pod", action="store_true", dest="frompod",
                   help="pull the themes from the POD record embedded in the bag rather from the NERDm "+
                        "metadata")
    p.add_argument("-a", "--as-annotations", action="store_true", dest="asannots",
                   help="save the updated topics as annotations")
    p.add_argument("-r", "--replace", action="store_true", dest="replacethemes",
                   help="remove all previously save topics from the NIST Taxonomy")
    p.add_argument("-t", "--add-theme", metavar='THEME', type=str, dest="addthemes", nargs='*',
                   help="add THEME in addition the themes in the theme property")
    p.add_argument("-V", "--validate", action="store_true", dest="validate",
                   help="validate the NERDm metadata after update.")
    
    return None

def execute(args, config=None, log=None):
    if not log:
        log = logging.getLogger(default_name)
    if not config:
        config = {}

    if isinstance(args, list):
        # cmd-line arguments not parsed yet
        p = argparse.ArgumentParser()
        load_command(p)
        args = p.parse_args(args)

    if not args.aipid:
        raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
    usenm = args.aipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)

    # set the input bag
    workdir = config.get('working_dir', '.')
    bagparent = config.get('metadata_bag_dir')
    if args.bagparent:
        bagparent = args.bagparent
    if not bagparent:
        bagparent = workdir
    elif not bagparent.startswith('./') and not bagparent.startswith('../') and not os.path.isabs(bagparent):
        bagparent = os.path.join(workdir, bagparent)
    bagdir = os.path.join(bagparent, args.aipid)
    if not os.path.isdir(bagdir):
        raise PDRCommandFailure(default_name, "Input bag does not exist (as a dir): "+bagdir, 2)

    bag = NISTBag(bagdir)
    update_topics(bag, args.frompod, args.replacethemes, args.addthemes, args.asannots, log)
    if args.validate:
        validate_resource(bag, log)

def update_topics(bag, frompod=False, replace=False, extrathemes=None, asannots=False, log=None):

    # load the taxonomy vocabulary
    taxon = open_research_topics_taxonomy()

    # get the topics parameter
    if not os.path.exists(bag.nerd_file_for('')):
        raise PDRCommandFailure(default_name,
                                os.path.basename(bag.dir)+": NERDm metadata not yet initialized", 3)
    nerdm = bag.nerd_metadata_for('', True)
    topics = nerdm.get('topic', [])

    tid = taxon.data.get('@id')
    if replace:
        # remove entries from the NIST taxonomy
        topics = [t for t in topics if not t.get('scheme') or t.get('scheme') != tid]

    # get the input themes
    themes = nerdm.get('theme', [])  # from NERDm
    if frompod:
        # extract the POD record instead
        if not os.path.exists(bag.pod_file()):
            raise PDRCommandFailure(default_name, os.path.basename(bag.dir)+": No POD found in bag", 3)
        pod = bag.pod_record()
        themes = pod.get('theme', [])

    if extrathemes:
        themes.extend(extrathemes)
    if len(themes) == 0 and log:
        log.warn("No input themes found (no updates made)")
        return

    # convert the themes
    converted = taxon.themes2topics(themes, incl_unrec=False)

    # merge the topics into the current list
    next_insert = 0
    for ctop in converted:
        for i, topic in enumerate(topics):
            if topic['scheme'] == ctop['scheme'] and topic['tag'] == ctop['tag']:
                topics[i] = ctop
                if i > next_insert:
                    next_insert = i+1
                ctop = None
                break
        if ctop:
            topics.insert(next_insert, ctop)
            next_insert += 1

    # save the result
    bldr = BagBuilder(os.path.dirname(bag.dir), os.path.basename(bag.dir), logger=log)
    if asannots:
        bldr.update_annotations_for('', {'topic': topics}, message="topics updated (to annotations)")
    else:
        bldr.update_metadata_for('', {'topic': topics}, message="topics updated")
    bldr.disconnect_logfile()
        
def open_research_topics_taxonomy(schemadir=None):
    if not schemadir:
        schemadir = def_schema_dir
    if not schemadir:
        raise PDRCommandFailure(default_name, "Unable to find taxonomy dictionary: schema dir unknown", 3)

    try:
        return ResearchTopicsTaxonomy.from_schema_dir(schemadir)
    except IOError as ex:
        raise PDRCommandFailure(default_name, "Unable to read taxonomy dictionary: "+str(ex), 3, ex)

def validate_resource(bag, log, merge=True):
    vald8.validate_nerdm_for(bag, '', log, merge, "Updated metadata is valid")




