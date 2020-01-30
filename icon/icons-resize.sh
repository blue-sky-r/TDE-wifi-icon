:

# utility for resizing icons - implemented for TDE-wifi-icon
#
#

[ $# -lt 3 ] && cat <<< """
= $0 = resize all icons in source dir to the destination dir while keeping the color space =

usage: $0 src size dst

src  ... source dir
size ... resize to either X or XxY
dst  ... destinaion dir

""" && exit 1

SRC=${1%/}
DIM=$2; [[ ! $DIM =~ .+x.+ ]] && DIM=${DIM}x${DIM} 
DST=${3%/}

for srcico in $SRC/*.png
{ 
	dstico=$DST/${srcico##*/}
	convert -sample $DIM "$srcico" "$dstico"
}

ls -l "$DST/"
