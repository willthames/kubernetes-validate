#!/bin/ash

if [ $# -lt 5 ]; then
  echo "expected: $0 <strict(true|false)> <version|latest> <quiet(true|false)> <nowarn(true|false)> target"
  echo "got: $@"
  exit 1
fi

args=""
if [[ "$1" != "false" ]] ; then
  args="${args} --strict"
fi

if [[ "$2" != "latest" ]] ; then
  args="${args} -k ${2}"
fi

if [[ "$3" != "false" ]] ; then
  args="${args} --quiet"
fi

if [[ "$4" != "false" ]] ; then
  args="${args} --no-warn"
fi

if [ -d "$5" ] ; then
  output=$(find $5 -type f | xargs kubernetes-validate ${args})
  rc=$?
elif [ -f "$5" ] ; then
  output=$(kubernetes-validate ${args} $5)
  rc=$?
else
  echo "unexpected: $5 should be a file or a directory"
  exit 2
fi
output=$(echo -n "$output" | sed -z -e 's/%/%25/g' -e "s/\n/%0A/g" -e "s/\r/%0D/g")
echo -n "output=${output}" >> $GITHUB_OUTPUT
exit $rc
