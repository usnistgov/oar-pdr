#! /bin/bash
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
base=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

##########
true ${SOURCE_DIR:=$base}
true ${INSTALL_DIR:=/app/pdr/nerdm}
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

true ${SCHEMA_DIR:=$INSTALL_DIR/schemas}
true ${JQ_LIBDIR:=$INSTALL_DIR/jq}
true ${PY_LIBDIR:=$INSTALL_DIR/python} 
true ${BINDIR:=$INSTALL_DIR/bin}

# install the schemas
mkdir -p $SCHEMA_DIR
echo "cp $SOURCE_DIR/model/*.json* $SCHEMA_DIR"
cp $SOURCE_DIR/model/*.json* $SCHEMA_DIR

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

