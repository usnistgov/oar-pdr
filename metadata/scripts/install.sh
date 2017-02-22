#! /bin/bash
#
# This script installs the various metadata tools into a deployment (i.e.
# install) directory.
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
base=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

##########
true ${SOURCE_DIR:=$base}
true ${INSTALL_DIR:=/usr/local}
##########

# handle command line options
while [ "$1" != "" ]; do 
  case "$1" in
    --prefix=*|--install-dir=*)
        INSTALL_DIR=`echo $1 | sed -e 's/[^=]*=//'`
        ;;
    --prefix|--install-dir)
        shift
        INSTALL_DIR=$1
        ;;
    --source-dir=*|--dir=*)
        SOURCE_DIR=`echo $1 | sed -e 's/[^=]*=//'`
        ;;
    -d|--dir|--source-dir)
        shift
        SOURCE_DIR=$1
        ;;
    -*)
        echo "$prog: unsupported option:" $1
        false
        ;;
    *)
        echo "Warning: ignoring argument: $1"
        ;;
  esac
  shift
done

[ "$INSTALL_DIR" = "/usr/local" ] && {
    true ${PY_LIBDIR:=$INSTALL_DIR/lib/python2.7/dist-packages}
}
[ "$INSTALL_DIR" = "/usr" ] && {
    true ${PY_LIBDIR:=$INSTALL_DIR/lib/python2.7}
}

true ${ETC_DIR:=$INSTALL_DIR/etc}
true ${SCHEMA_DIR:=$ETC_DIR/schemas}
true ${JQ_LIBDIR:=$INSTALL_DIR/lib/jq}
true ${PY_LIBDIR:=$INSTALL_DIR/lib/python} 
true ${BINDIR:=$INSTALL_DIR/bin}

# install the schemas
mkdir -p $SCHEMA_DIR
schemafiles=`ls -d $SOURCE_DIR/model/*.json{,ld} | grep -v nerdm-fields-help`
echo cp $schemafiles $SCHEMA_DIR
cp $schemafiles $SCHEMA_DIR

# install the jq modules
mkdir -p $JQ_LIBDIR
echo "cp $SOURCE_DIR/jq/*.jq $JQ_LIBDIR"
cp $SOURCE_DIR/jq/*.jq $JQ_LIBDIR

#install the nerdm library
mkdir -p $PY_LIBDIR
echo Installing python libraries into $PY_LIBDIR...
(cd $SOURCE_DIR/python && python setup.py install --install-purelib=$PY_LIBDIR)

#install scripts
mkdir -p $BINDIR
echo cp $SOURCE_DIR/scripts/pdl2resources.py $BINDIR
cp $SOURCE_DIR/scripts/pdl2resources.py $BINDIR
echo cp $SOURCE_DIR/scripts/ingest-field-info.py $BINDIR
cp $SOURCE_DIR/scripts/ingest-field-info.py $BINDIR
echo cp $SOURCE_DIR/scripts/ingest-nerdm-res.py $BINDIR
cp $SOURCE_DIR/scripts/ingest-nerdm-res.py $BINDIR

#install miscellaneous data files
mkdir -p $ETC_DIR/samples
echo cp $SOURCE_DIR/jq/tests/data/nist-pdl-oct2016.json $ETC_DIR/samples
cp $SOURCE_DIR/jq/tests/data/nist-pdl-oct2016.json $ETC_DIR/samples
echo cp $SOURCE_DIR/model/nerdm-fields-help.json $ETC_DIR/samples
cp $SOURCE_DIR/model/nerdm-fields-help.json $ETC_DIR/samples

for f in `ls -d $SOURCE_DIR/model/examples/*.json`; do
    echo cp $f $ETC_DIR/samples
    cp $f $ETC_DIR/samples
done


